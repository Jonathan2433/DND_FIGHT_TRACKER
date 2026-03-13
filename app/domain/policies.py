"""Domain policies centralizing access rules."""

class CampaignPolicy:
    @staticmethod
    def can_access(user, campaign):
        if not user or not campaign:
            return False
        return user.role == "Admin" or user.is_mj_of(campaign) or user.is_member_of(campaign)

    @staticmethod
    def can_manage(user, campaign):
        if not user or not campaign:
            return False
        return user.role == "Admin" or user.is_mj_of(campaign)

class CharacterPolicy:
    @staticmethod
    def can_edit(user, character):
        if not user or not character:
            return False
        return user.role == "Admin" or character.owner_id == user.id or (character.campaign and user.is_mj_of(character.campaign))

    @staticmethod
    def can_view(user, character):
        if not character:
            return False
        return character.can_be_viewed_by(user, character.campaign)

__all__ = ["CampaignPolicy", "CharacterPolicy"]
