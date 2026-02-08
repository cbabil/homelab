"""
SSH Service Module

Provides secure SSH connection management using paramiko.
Implements connection pooling to prevent SSH flooding.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import paramiko
import structlog

logger = structlog.get_logger("ssh_service")


class SSHConnectionPool:
    """Thread-safe SSH connection pool."""

    def __init__(self):
        self._connections: dict[str, paramiko.SSHClient] = {}
        self._lock = asyncio.Lock()
        self._in_use: dict[str, bool] = {}

    def _make_key(self, host: str, port: int, username: str) -> str:
        """Create unique key for connection."""
        return f"{host}:{port}:{username}"

    async def get(self, key: str) -> paramiko.SSHClient | None:
        """Get an available connection from pool."""
        async with self._lock:
            if key in self._connections and not self._in_use.get(key, False):
                client = self._connections[key]
                # Verify connection is still alive
                if client.get_transport() and client.get_transport().is_active():
                    self._in_use[key] = True
                    logger.debug("Reusing pooled connection", key=key)
                    return client
                else:
                    # Connection is dead, remove it
                    logger.debug("Removing dead connection from pool", key=key)
                    try:
                        client.close()
                    except Exception:
                        pass
                    del self._connections[key]
                    if key in self._in_use:
                        del self._in_use[key]
            return None

    async def put(self, key: str, client: paramiko.SSHClient) -> None:
        """Add a connection to the pool."""
        async with self._lock:
            self._connections[key] = client
            self._in_use[key] = False
            logger.debug("Connection added to pool", key=key)

    async def release(self, key: str) -> None:
        """Release a connection back to the pool."""
        async with self._lock:
            if key in self._in_use:
                self._in_use[key] = False
                logger.debug("Connection released to pool", key=key)

    async def close(self, key: str) -> None:
        """Close and remove a specific connection."""
        async with self._lock:
            if key in self._connections:
                try:
                    self._connections[key].close()
                except Exception:
                    pass
                del self._connections[key]
                if key in self._in_use:
                    del self._in_use[key]
                logger.debug("Connection closed and removed", key=key)

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for key, client in list(self._connections.items()):
                try:
                    client.close()
                except Exception:
                    pass
            self._connections.clear()
            self._in_use.clear()
            logger.info("All pooled connections closed")


class SSHService:
    """Manages secure SSH connections with connection pooling."""

    def __init__(self, strict_host_key_checking: bool = None):
        """Initialize SSH service with secure defaults."""
        self._pool = SSHConnectionPool()
        self.connection_configs = {
            "timeout": 60,
            "auth_timeout": 30,
            "banner_timeout": 60,
            "compress": True,
            "allow_agent": False,
            "look_for_keys": False,
        }

        if strict_host_key_checking is None:
            self.strict_host_key_checking = True
        else:
            self.strict_host_key_checking = strict_host_key_checking

        logger.info(
            "SSH service initialized with connection pooling",
            strict_host_key_checking=self.strict_host_key_checking,
        )

    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create a securely configured SSH client."""
        client = paramiko.SSHClient()

        known_hosts_path = Path.home() / ".ssh" / "known_hosts"
        if known_hosts_path.exists():
            try:
                client.load_host_keys(str(known_hosts_path))
            except Exception as e:
                logger.warning("Failed to load known hosts", error=str(e))

        if self.strict_host_key_checking:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.WarningPolicy())

        return client

    @asynccontextmanager
    async def _get_connection(
        self, host: str, port: int, username: str, auth_type: str, credentials: dict
    ):
        """Context manager for getting a pooled SSH connection."""
        from services.helpers.ssh_helpers import connect_key, connect_password

        key = self._pool._make_key(host, port, username)
        client = await self._pool.get(key)

        if client is None:
            # Create new connection
            client = self._create_ssh_client()
            try:
                logger.info("Creating new SSH connection", host=host, port=port)
                if auth_type == "password":
                    await connect_password(
                        client,
                        host,
                        port,
                        username,
                        credentials,
                        self.connection_configs,
                    )
                elif auth_type == "key":
                    await connect_key(
                        client,
                        host,
                        port,
                        username,
                        credentials,
                        self.connection_configs,
                    )
                else:
                    raise ValueError(f"Unsupported auth type: {auth_type}")

                # Add to pool after successful connection
                await self._pool.put(key, client)
            except Exception:
                client.close()
                raise

        try:
            yield client
        finally:
            # Release back to pool (don't close)
            await self._pool.release(key)

    async def test_connection(
        self, host: str, port: int, username: str, auth_type: str, credentials: dict
    ) -> tuple[bool, str, dict | None]:
        """Test SSH connection and return system info if successful."""
        from services.helpers.ssh_helpers import get_system_info

        try:
            logger.info(
                "Testing SSH connection", host=host, port=port, username=username
            )

            async with self._get_connection(
                host, port, username, auth_type, credentials
            ) as client:
                system_info = await get_system_info(client)
                logger.info("SSH connection test successful", host=host)
                return True, "Connection successful", system_info

        except Exception as e:
            logger.error("SSH connection failed", host=host, error=str(e))
            return False, str(e), None

    async def execute_command(
        self,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: dict,
        command: str,
        timeout: int = 120,
    ) -> tuple[bool, str]:
        """Execute a command on remote server via SSH."""
        try:
            logger.info(
                "Executing SSH command", host=host, port=port, username=username
            )

            async with self._get_connection(
                host, port, username, auth_type, credentials
            ) as client:

                def run_command():
                    stdin, stdout, stderr = client.exec_command(
                        command, timeout=timeout
                    )
                    exit_status = stdout.channel.recv_exit_status()
                    output = stdout.read().decode("utf-8")
                    error = stderr.read().decode("utf-8")
                    return exit_status, output, error

                loop = asyncio.get_running_loop()
                exit_status, output, error = await loop.run_in_executor(
                    None, run_command
                )

                if exit_status == 0:
                    logger.info("SSH command executed successfully", host=host)
                    return True, output
                else:
                    logger.error(
                        "SSH command failed", host=host, exit_status=exit_status
                    )
                    return False, error or output

        except Exception as e:
            logger.error("SSH command execution failed", host=host, error=str(e))
            return False, str(e)

    async def execute_command_with_progress(
        self,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: dict,
        command: str,
        progress_callback=None,
        timeout: int = 600,
    ) -> tuple[bool, str]:
        """Execute a command with real-time progress callback."""
        try:
            logger.info("Executing SSH command with progress", host=host, port=port)

            async with self._get_connection(
                host, port, username, auth_type, credentials
            ) as client:
                loop = asyncio.get_running_loop()

                def run_command_streaming():
                    stdin, stdout, stderr = client.exec_command(
                        command, timeout=timeout
                    )
                    channel = stdout.channel

                    full_output = []
                    buffer = ""

                    while not channel.exit_status_ready() or channel.recv_ready():
                        if channel.recv_ready():
                            chunk = channel.recv(1024).decode("utf-8", errors="replace")
                            buffer += chunk

                            while "\n" in buffer or "\r" in buffer:
                                for sep in ["\n", "\r"]:
                                    if sep in buffer:
                                        line, buffer = buffer.split(sep, 1)
                                        if line.strip():
                                            full_output.append(line)
                                            if progress_callback:
                                                loop.call_soon_threadsafe(
                                                    lambda current_line=line: asyncio.run_coroutine_threadsafe(
                                                        progress_callback(current_line),
                                                        loop,
                                                    )
                                                )
                                        break
                        else:
                            import time

                            time.sleep(0.1)

                    if buffer.strip():
                        full_output.append(buffer.strip())
                        if progress_callback:
                            remaining = buffer.strip()
                            loop.call_soon_threadsafe(
                                lambda rem=remaining: asyncio.run_coroutine_threadsafe(
                                    progress_callback(rem), loop
                                )
                            )

                    exit_status = channel.recv_exit_status()
                    error = stderr.read().decode("utf-8")

                    return exit_status, "\n".join(full_output), error

                exit_status, output, error = await loop.run_in_executor(
                    None, run_command_streaming
                )

                if exit_status == 0:
                    logger.info("SSH command with progress completed", host=host)
                    return True, output
                else:
                    logger.error("SSH command with progress failed", host=host)
                    return False, error or output

        except Exception as e:
            logger.error("SSH command with progress failed", host=host, error=str(e))
            return False, str(e)

    async def close_connection(self, host: str, port: int, username: str) -> None:
        """Explicitly close a pooled connection."""
        key = self._pool._make_key(host, port, username)
        await self._pool.close(key)

    async def close_all_connections(self) -> None:
        """Close all pooled connections."""
        await self._pool.close_all()
