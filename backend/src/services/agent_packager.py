"""
Agent Packager Service

Packages the agent source code for deployment to remote servers.
Creates a base64-encoded tarball that can be transferred via SSH.
"""

import base64
import io
import os
import tarfile
from pathlib import Path

import structlog

logger = structlog.get_logger("agent_packager")

# Path to agent source code relative to backend
AGENT_SOURCE_DIR = Path(__file__).parent.parent.parent.parent / "agent"


class AgentPackager:
    """Packages agent code for remote deployment."""

    def __init__(self, agent_dir: Path | None = None):
        """Initialize the packager.

        Args:
            agent_dir: Path to agent source directory. Defaults to /agent.
        """
        self.agent_dir = agent_dir or AGENT_SOURCE_DIR

    def get_version(self) -> str:
        """Get agent version from source.

        Returns:
            Version string from __init__.py or 'dev'.
        """
        init_file = self.agent_dir / "src" / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            for line in content.split("\n"):
                if line.startswith("__version__"):
                    # Extract version from: __version__ = "1.0.0"
                    return line.split("=")[1].strip().strip("\"'")
        return "dev"

    def package(self) -> str:
        """Package agent code as base64-encoded tarball.

        Returns:
            Base64-encoded tar.gz of agent source code.

        Raises:
            FileNotFoundError: If agent directory doesn't exist.
        """
        if not self.agent_dir.exists():
            raise FileNotFoundError(f"Agent directory not found: {self.agent_dir}")

        # Create tar.gz in memory
        buffer = io.BytesIO()

        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            for root, dirs, files in os.walk(self.agent_dir):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != "__pycache__"]

                for file in files:
                    # Skip .pyc files and other artifacts
                    if file.endswith(".pyc") or file.startswith("."):
                        continue

                    file_path = Path(root) / file
                    # Archive path relative to agent_dir
                    arcname = file_path.relative_to(self.agent_dir)
                    tar.add(file_path, arcname=str(arcname))

        # Get the tarball bytes and encode
        buffer.seek(0)
        tarball_bytes = buffer.read()
        encoded = base64.b64encode(tarball_bytes).decode("utf-8")

        logger.info(
            "Agent packaged",
            version=self.get_version(),
            size_bytes=len(tarball_bytes),
            encoded_size=len(encoded),
        )

        return encoded

    def get_file_list(self) -> list[str]:
        """Get list of files that will be packaged.

        Returns:
            List of file paths relative to agent directory.
        """
        files = []
        for root, dirs, filenames in os.walk(self.agent_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in filenames:
                if file.endswith(".pyc") or file.startswith("."):
                    continue
                file_path = Path(root) / file
                files.append(str(file_path.relative_to(self.agent_dir)))
        return sorted(files)
