"""Package des modèles - Imports centralisés"""

# Import des modèles pour faciliter l'usage
from .combat import Combat, Combatant, CombatLog
from .character import CharacterTemplate
from .encounter import EncounterTemplate
from .experience import XPLog
from .user import User, EmailVerification
from .campaign import (
    Campaign,
    CampaignSession,
    CampaignMember,
    CampaignInvitation,
    JoinRequest,
    CampaignInspirationLog,
)
from .story_arc import StoryArc
from .notification import Notification
from .episode import Episode, EpisodeUserNote

# Exposition des modèles
__all__ = [
    'Combat',
    'Combatant',
    'CombatLog',
    'CharacterTemplate',
    'EncounterTemplate',
    'XPLog',
    'User',
    'EmailVerification',
    'Campaign',
    'CampaignSession',
    'CampaignMember',
    'CampaignInvitation',
    'JoinRequest',
    'CampaignInspirationLog',
    'StoryArc',
    'Notification',
    'Episode',
    'EpisodeUserNote'
]
