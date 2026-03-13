"""Compatibility service exports (backed by application use cases)."""

from app.application.use_cases.auth_service import AuthService
from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.character_service import CharacterService
from app.application.use_cases.combat_service import CombatService
from app.application.use_cases.combatant_service import CombatantService
from app.application.use_cases.email_service import EmailService
from app.application.use_cases.group_service import GroupService
from app.application.use_cases.story_arc_service import StoryArcService
from app.application.use_cases.template_service import TemplateService
from app.application.use_cases.xp_service import XPService

__all__ = [
    "AuthService",
    "CampaignService",
    "CharacterService",
    "CombatService",
    "CombatantService",
    "EmailService",
    "GroupService",
    "StoryArcService",
    "TemplateService",
    "XPService",
]
