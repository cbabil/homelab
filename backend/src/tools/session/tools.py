"""
Session Tools

Provides session management capabilities for the MCP server.
Implements CRUD operations with role-based access control.
"""

from typing import Dict, Any
import structlog
from fastmcp import Context
from services.session_service import SessionService
from models.session import SessionStatus

logger = structlog.get_logger("session_tools")


class SessionTools:
    """Session management tools for the MCP server."""

    def __init__(self, session_service: SessionService, auth_service=None):
        """Initialize session tools.

        Args:
            session_service: Session service instance.
            auth_service: Auth service for permission checks.
        """
        self.session_service = session_service
        self.auth_service = auth_service
        logger.info("Session tools initialized")

    def _get_user_context(self, ctx: Context) -> tuple:
        """Extract user context from request.

        Returns:
            Tuple of (user_id, current_session_id, role)
        """
        meta = getattr(ctx, 'meta', {}) or {}
        user_id = meta.get('user_id', '')
        session_id = meta.get('session_id', '')
        role = meta.get('role', 'user')
        return user_id, session_id, role

    def _is_admin(self, role: str) -> bool:
        """Check if user has admin role."""
        return role == 'admin'

    async def list_sessions(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """List sessions for a user.

        Users can only list their own sessions.
        Admins can list any user's sessions.

        Params:
            user_id: Optional - Admin can specify target user
            status: Optional - Filter by status

        Returns:
            List of sessions.
        """
        try:
            current_user_id, current_session_id, role = self._get_user_context(ctx)
            target_user_id = params.get("user_id", current_user_id)
            status_filter = params.get("status")

            # Permission check: users can only list their own sessions
            if not self._is_admin(role) and target_user_id != current_user_id:
                return {
                    "success": False,
                    "message": "Permission denied: cannot list other users' sessions",
                    "error": "PERMISSION_DENIED"
                }

            status = SessionStatus(status_filter) if status_filter else None
            sessions = await self.session_service.list_sessions(
                user_id=target_user_id,
                status=status
            )

            # Mark the current session
            session_data = []
            for s in sessions:
                data = s.model_dump()
                data["is_current"] = (s.id == current_session_id)
                session_data.append(data)

            return {
                "success": True,
                "data": session_data,
                "message": f"Found {len(sessions)} sessions"
            }

        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list sessions: {str(e)}",
                "error": "LIST_ERROR"
            }

    async def get_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Get a single session by ID.

        Users can only get their own sessions.
        Admins can get any session.

        Params:
            session_id: Required - Session ID to retrieve

        Returns:
            Session details.
        """
        try:
            current_user_id, _, role = self._get_user_context(ctx)
            session_id = params.get("session_id")

            if not session_id:
                return {
                    "success": False,
                    "message": "session_id is required",
                    "error": "MISSING_PARAM"
                }

            session = await self.session_service.get_session(session_id)

            if not session:
                return {
                    "success": False,
                    "message": "Session not found",
                    "error": "NOT_FOUND"
                }

            # Permission check
            if not self._is_admin(role) and session.user_id != current_user_id:
                return {
                    "success": False,
                    "message": "Permission denied: cannot access other users' sessions",
                    "error": "PERMISSION_DENIED"
                }

            return {
                "success": True,
                "data": session.model_dump(),
                "message": "Session retrieved"
            }

        except Exception as e:
            logger.error("Failed to get session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get session: {str(e)}",
                "error": "GET_ERROR"
            }

    async def update_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Update session last_activity.

        Users can only update their own current session.
        Admins can update any session.

        Params:
            session_id: Required - Session ID to update

        Returns:
            Success status.
        """
        try:
            current_user_id, current_session_id, role = self._get_user_context(ctx)
            session_id = params.get("session_id")

            if not session_id:
                return {
                    "success": False,
                    "message": "session_id is required",
                    "error": "MISSING_PARAM"
                }

            # For non-admins, verify they own this session
            if not self._is_admin(role):
                session = await self.session_service.get_session(session_id)
                if not session or session.user_id != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot update other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

            updated = await self.session_service.update_session(session_id)

            return {
                "success": True,
                "data": {"updated": updated},
                "message": "Session updated" if updated else "Session not found or already expired"
            }

        except Exception as e:
            logger.error("Failed to update session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to update session: {str(e)}",
                "error": "UPDATE_ERROR"
            }

    async def delete_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Terminate one or more sessions.

        Users can only delete their own sessions.
        Admins can delete any session or all sessions for a user.

        Params:
            session_id: Optional - Delete specific session
            user_id: Optional - Admin: delete all sessions for user
            all: Optional - Delete all own sessions
            exclude_current: Optional - Keep current session (default: true)

        Returns:
            Count of terminated sessions.
        """
        try:
            current_user_id, current_session_id, role = self._get_user_context(ctx)
            target_session_id = params.get("session_id")
            target_user_id = params.get("user_id")
            delete_all = params.get("all", False)
            exclude_current = params.get("exclude_current", True)

            # Determine exclude session
            exclude_session_id = current_session_id if exclude_current else None

            if target_session_id:
                # Delete specific session
                session = await self.session_service.get_session(target_session_id)

                if not session:
                    return {
                        "success": False,
                        "message": "Session not found",
                        "error": "NOT_FOUND"
                    }

                # Permission check
                if not self._is_admin(role) and session.user_id != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot delete other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

                count = await self.session_service.delete_session(
                    session_id=target_session_id,
                    terminated_by=current_user_id
                )

            elif delete_all or target_user_id:
                # Delete all sessions for a user
                user_to_delete = target_user_id or current_user_id

                # Permission check: only admin can delete other users' sessions
                if not self._is_admin(role) and user_to_delete != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot delete other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

                count = await self.session_service.delete_session(
                    user_id=user_to_delete,
                    terminated_by=current_user_id,
                    exclude_session_id=exclude_session_id
                )

            else:
                return {
                    "success": False,
                    "message": "Must specify session_id, user_id, or all=true",
                    "error": "MISSING_PARAM"
                }

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Terminated {count} session(s)"
            }

        except Exception as e:
            logger.error("Failed to delete session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to delete session: {str(e)}",
                "error": "DELETE_ERROR"
            }

    async def cleanup_expired_sessions(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Mark expired sessions. Admin only.

        Returns:
            Count of sessions marked as expired.
        """
        try:
            _, _, role = self._get_user_context(ctx)

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Permission denied: admin only",
                    "error": "PERMISSION_DENIED"
                }

            count = await self.session_service.cleanup_expired_sessions()

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Cleaned up {count} expired session(s)"
            }

        except Exception as e:
            logger.error("Failed to cleanup sessions", error=str(e))
            return {
                "success": False,
                "message": f"Failed to cleanup sessions: {str(e)}",
                "error": "CLEANUP_ERROR"
            }
