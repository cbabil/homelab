"""
Server Data Models

Defines server connection and configuration data models using Pydantic.
Implements strict validation as per architectural requirements.
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import ipaddress
import re


class AuthType(str, Enum):
    """Authentication types for SSH connections."""
    PASSWORD = "password"
    KEY = "key"


class ServerStatus(str, Enum):
    """Server connection status states."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PREPARING = "preparing"


class SystemInfo(BaseModel):
    """System information from remote server."""
    os: str = Field(..., description="Operating system information")
    kernel: str = Field(..., description="Kernel version")
    architecture: str = Field(..., description="System architecture")
    docker_version: Optional[str] = Field(None, description="Docker version if installed")
    agent_status: Optional[str] = Field(None, description="Agent container status (running/not running)")
    agent_version: Optional[str] = Field(None, description="Agent version if installed")


class ServerConnection(BaseModel):
    """Server connection configuration model."""
    id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Server display name")
    host: str = Field(..., min_length=1, max_length=255, description="Server hostname or IP")
    port: int = Field(default=22, ge=1, le=65535, description="SSH port number")
    username: str = Field(..., min_length=1, max_length=100, description="SSH username")
    auth_type: AuthType = Field(..., description="Authentication method")
    status: ServerStatus = Field(default=ServerStatus.DISCONNECTED)
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    last_connected: Optional[str] = Field(None, description="Last connection timestamp")
    system_info: Optional[SystemInfo] = Field(None, description="System information")
    docker_installed: bool = Field(default=False, description="Whether Docker is installed")
    system_info_updated_at: Optional[str] = Field(None, description="When system info was last updated")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, value: str) -> str:
        """Validate hostname or IP address format."""
        # Try IP address validation first
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            pass
        
        # Validate hostname format
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(hostname_pattern, value):
            raise ValueError('Invalid host format - must be valid IP or hostname')

        return value

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Validate SSH username format."""
        username_pattern = r'^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$'
        if not re.match(username_pattern, value):
            raise ValueError('Invalid username format')
        
        return value


class ServerCredentials(BaseModel):
    """Encrypted server credentials storage."""
    server_id: str = Field(..., description="Associated server ID")
    encrypted_data: str = Field(..., description="AES-256 encrypted credential data")
    created_at: str = Field(..., description="Creation timestamp")
