"""Tests for system tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetSystemSetup:
    """Tests for the get_system_setup tool."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        service = MagicMock()
        service.is_system_setup = AsyncMock(return_value=False)
        service.get_system_info = AsyncMock(return_value={"app_name": "Tomo"})
        return service

    @pytest.mark.asyncio
    async def test_get_system_setup_needs_setup(self, mock_db_service):
        """Test get_system_setup when system needs setup."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_setup()

        assert result["success"] is True
        assert result["data"]["needs_setup"] is True
        assert result["data"]["is_setup"] is False
        assert result["data"]["app_name"] == "Tomo"

    @pytest.mark.asyncio
    async def test_get_system_setup_already_setup(self, mock_db_service):
        """Test get_system_setup when system is already set up."""
        from tools.system.tools import SystemTools

        mock_db_service.is_system_setup = AsyncMock(return_value=True)

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_setup()

        assert result["success"] is True
        assert result["data"]["needs_setup"] is False
        assert result["data"]["is_setup"] is True

    @pytest.mark.asyncio
    async def test_get_system_setup_no_system_info(self, mock_db_service):
        """Test get_system_setup when system_info is empty."""
        from tools.system.tools import SystemTools

        mock_db_service.get_system_info = AsyncMock(return_value=None)

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_setup()

        assert result["success"] is True
        assert result["data"]["app_name"] == "Tomo"

    @pytest.mark.asyncio
    async def test_get_system_setup_handles_error(self, mock_db_service):
        """Test get_system_setup handles errors gracefully."""
        from tools.system.tools import SystemTools

        mock_db_service.is_system_setup = AsyncMock(
            side_effect=Exception("Database error")
        )

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_setup()

        assert result["success"] is False
        assert result["error"] == "SETUP_CHECK_ERROR"


class TestGetSystemInfo:
    """Tests for the get_system_info tool."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        service = MagicMock()
        service.get_system_info = AsyncMock(
            return_value={
                "app_name": "Tomo",
                "is_setup": True,
                "setup_completed_at": "2024-01-15T10:00:00",
                "installation_id": "abc123",
                "license_type": "community",
                "license_key": "secret-key",
                "license_expires_at": None,
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-01-15T10:00:00",
            }
        )
        return service

    @pytest.mark.asyncio
    async def test_get_system_info_success(self, mock_db_service):
        """Test get_system_info returns expected data."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_info()

        assert result["success"] is True
        assert result["data"]["app_name"] == "Tomo"
        assert result["data"]["installation_id"] == "abc123"
        # license_key should not be exposed
        assert "license_key" not in result["data"]

    @pytest.mark.asyncio
    async def test_get_system_info_not_found(self, mock_db_service):
        """Test get_system_info when system info is missing."""
        from tools.system.tools import SystemTools

        mock_db_service.get_system_info = AsyncMock(return_value=None)

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_info()

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_system_info_handles_error(self, mock_db_service):
        """Test get_system_info handles errors gracefully."""
        from tools.system.tools import SystemTools

        mock_db_service.get_system_info = AsyncMock(
            side_effect=Exception("Database error")
        )

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_system_info()

        assert result["success"] is False
        assert result["error"] == "SYSTEM_INFO_ERROR"


class TestGetComponentVersions:
    """Tests for the get_component_versions tool."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        service = MagicMock()
        service.get_component_versions = AsyncMock(
            return_value=[
                {
                    "component": "backend",
                    "version": "1.2.0",
                    "updated_at": "2024-01-15T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "component": "frontend",
                    "version": "1.2.0",
                    "updated_at": "2024-01-15T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "component": "api",
                    "version": "1.1.0",
                    "updated_at": "2024-01-10T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
            ]
        )
        return service

    @pytest.mark.asyncio
    async def test_get_component_versions_success(self, mock_db_service):
        """Test get_component_versions returns expected data."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_component_versions()

        assert result["success"] is True
        assert result["data"]["backend"] == "1.2.0"
        assert result["data"]["frontend"] == "1.2.0"
        assert result["data"]["api"] == "1.1.0"
        assert "components" in result["data"]

    @pytest.mark.asyncio
    async def test_get_component_versions_empty(self, mock_db_service):
        """Test get_component_versions when no versions exist."""
        from tools.system.tools import SystemTools

        mock_db_service.get_component_versions = AsyncMock(return_value=[])

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_component_versions()

        assert result["success"] is True
        assert result["data"]["backend"] == "1.0.0"
        assert result["data"]["frontend"] == "1.0.0"
        assert result["data"]["api"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_component_versions_handles_error(self, mock_db_service):
        """Test get_component_versions handles errors gracefully."""
        from tools.system.tools import SystemTools

        mock_db_service.get_component_versions = AsyncMock(
            side_effect=Exception("Database error")
        )

        system_tools = SystemTools(mock_db_service)

        result = await system_tools.get_component_versions()

        assert result["success"] is False
        assert result["error"] == "VERSION_ERROR"


class TestCheckUpdates:
    """Tests for the check_updates tool."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        service = MagicMock()
        service.get_component_versions = AsyncMock(
            return_value=[
                {
                    "component": "backend",
                    "version": "1.0.0",
                    "updated_at": "2024-01-15T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "component": "frontend",
                    "version": "1.0.0",
                    "updated_at": "2024-01-15T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "component": "api",
                    "version": "1.0.0",
                    "updated_at": "2024-01-15T10:00:00",
                    "created_at": "2024-01-01T00:00:00",
                },
            ]
        )
        return service

    @pytest.mark.asyncio
    async def test_check_updates_available(self, mock_db_service):
        """Test check_updates when update is available."""
        from tools.system.tools import SystemTools

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "tag_name": "v1.1.0",
                "html_url": "https://github.com/test/releases/v1.1.0",
                "body": "Release notes here",
            }
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            system_tools = SystemTools(mock_db_service)
            result = await system_tools.check_updates()

        assert result["success"] is True
        assert result["data"]["components"]["backend"] == "1.0.0"
        assert result["data"]["latest_version"] == "1.1.0"
        assert result["data"]["update_available"] is True

    @pytest.mark.asyncio
    async def test_check_updates_no_update(self, mock_db_service):
        """Test check_updates when already on latest."""
        from tools.system.tools import SystemTools

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "tag_name": "v1.0.0",
                "html_url": "https://github.com/test/releases/v1.0.0",
                "body": "Current release",
            }
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            system_tools = SystemTools(mock_db_service)
            result = await system_tools.check_updates()

        assert result["success"] is True
        assert result["data"]["update_available"] is False

    @pytest.mark.asyncio
    async def test_check_updates_no_releases(self, mock_db_service):
        """Test check_updates when no GitHub releases exist."""
        from tools.system.tools import SystemTools

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            system_tools = SystemTools(mock_db_service)
            result = await system_tools.check_updates()

        assert result["success"] is True
        assert result["data"]["update_available"] is False
        assert "No releases found" in result["data"]["message"]

    @pytest.mark.asyncio
    async def test_check_updates_http_error(self, mock_db_service):
        """Test check_updates handles HTTP errors."""
        import httpx

        from tools.system.tools import SystemTools

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Connection failed")
            )

            system_tools = SystemTools(mock_db_service)
            result = await system_tools.check_updates()

        assert result["success"] is False
        assert result["error"] == "UPDATE_CHECK_ERROR"

    @pytest.mark.asyncio
    async def test_check_updates_generic_exception(self, mock_db_service):
        """Test check_updates handles generic exceptions."""
        from tools.system.tools import SystemTools

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Unexpected error")
            )

            system_tools = SystemTools(mock_db_service)
            result = await system_tools.check_updates()

        assert result["success"] is False
        assert result["error"] == "UPDATE_CHECK_ERROR"


class TestVersionComparison:
    """Tests for version comparison helper."""

    def test_compare_versions_less_than(self):
        """Test version comparison when v1 < v2."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(MagicMock())

        assert system_tools._compare_versions("1.0.0", "1.1.0") == -1
        assert system_tools._compare_versions("1.0.0", "2.0.0") == -1
        assert system_tools._compare_versions("1.0.0", "1.0.1") == -1

    def test_compare_versions_equal(self):
        """Test version comparison when v1 == v2."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(MagicMock())

        assert system_tools._compare_versions("1.0.0", "1.0.0") == 0
        assert system_tools._compare_versions("v1.0.0", "1.0.0") == 0

    def test_compare_versions_greater_than(self):
        """Test version comparison when v1 > v2."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(MagicMock())

        assert system_tools._compare_versions("1.1.0", "1.0.0") == 1
        assert system_tools._compare_versions("2.0.0", "1.0.0") == 1
        assert system_tools._compare_versions("1.0.1", "1.0.0") == 1

    def test_compare_versions_with_short_versions(self):
        """Test version comparison with versions shorter than 3 parts."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(MagicMock())

        # 1.0 should be treated as 1.0.0
        assert system_tools._compare_versions("1.0", "1.0.0") == 0
        assert system_tools._compare_versions("1", "1.0.0") == 0
        assert system_tools._compare_versions("2", "1.0.0") == 1

    def test_compare_versions_with_non_numeric_parts(self):
        """Test version comparison with non-numeric parts (prerelease)."""
        from tools.system.tools import SystemTools

        system_tools = SystemTools(MagicMock())

        # 1.0.0-beta should parse, stripping the -beta
        assert system_tools._compare_versions("1.0.0-beta", "1.0.0") == 0
        assert system_tools._compare_versions("1.1.0-rc1", "1.0.0") == 1

        # Completely non-numeric parts should become 0
        assert system_tools._compare_versions("abc", "0.0.0") == 0
