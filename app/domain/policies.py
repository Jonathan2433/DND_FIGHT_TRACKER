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


class CombatPolicy:
    @staticmethod
    def can_manage(user, combat):
        if not user or not combat:
            return False
        if user.role == "Admin":
            return True
        if combat.campaign:
            return user.is_mj_of(combat.campaign)
        return False

    @staticmethod
    def can_view_player(user, combat):
        if not user or not combat:
            return False
        if CombatPolicy.can_manage(user, combat):
            return True
        if combat.campaign:
            return user.is_member_of(combat.campaign)
        return False


class EncounterTemplatePolicy:
    @staticmethod
    def can_manage(user, template):
        if not user or not template:
            return False
        return user.role == "Admin" or template.owner_id == user.id

__all__ = ["CampaignPolicy", "CharacterPolicy", "CombatPolicy", "EncounterTemplatePolicy"]
