"""Role-Based Access Control (RBAC) Matrix Pattern.

Governs multi-user authorization quorums for reviewing, snoozing, and approving
recursive code modifications.
"""
from enum import Enum
from typing import Dict, Set

class Role(str, Enum):
    VIEWER = "viewer"
    DEVELOPER = "developer"
    MAINTAINER = "maintainer"
    OPERATOR = "operator"

class Permission(str, Enum):
    VIEW_PROPOSALS = "view_proposals"
    VIEW_STATUS = "view_status"
    REQUEST_DASH = "request_dash"
    SNOOZE_PROPOSAL = "snooze_proposal"
    PROVIDE_FEEDBACK = "provide_feedback"
    APPROVE_PROPOSAL = "approve_proposal"
    TRIGGER_SANDBOX = "trigger_sandbox"
    MERGE_PATCH = "merge_patch"
    CONFIGURE_LIMITS = "configure_limits"
    RESET_CIRCUIT_BREAKER = "reset_circuit_breaker"
    PAIR_MCP = "pair_mcp"

class RBACManager:
    """Manages role-to-permission mapping and user role assignments."""

    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.VIEWER: {
            Permission.VIEW_PROPOSALS,
            Permission.VIEW_STATUS
        },
        Role.DEVELOPER: {
            Permission.VIEW_PROPOSALS,
            Permission.VIEW_STATUS,
            Permission.REQUEST_DASH,
            Permission.SNOOZE_PROPOSAL,
            Permission.PROVIDE_FEEDBACK
        },
        Role.MAINTAINER: {
            Permission.VIEW_PROPOSALS,
            Permission.VIEW_STATUS,
            Permission.REQUEST_DASH,
            Permission.SNOOZE_PROPOSAL,
            Permission.PROVIDE_FEEDBACK,
            Permission.APPROVE_PROPOSAL,
            Permission.TRIGGER_SANDBOX,
            Permission.MERGE_PATCH
        },
        Role.OPERATOR: {p for p in Permission}
    }

    def __init__(self):
        self._user_roles: Dict[str, Role] = {}

    def assign_role(self, user_id: str, role: Role):
        self._user_roles[user_id] = role

    def get_role(self, user_id: str) -> Role:
        return self._user_roles.get(user_id, Role.VIEWER)

    def is_authorized(self, user_id: str, permission: Permission) -> bool:
        role = self.get_role(user_id)
        return permission in self.ROLE_PERMISSIONS.get(role, set())
