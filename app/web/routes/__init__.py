"""Web route registry.

This layer centralizes HTTP blueprint registration.
"""

from . import main, combat, combatant, group, template, summary, xp
from . import auth, campaign, story_arc, episode, pnj, notification, admin

BLUEPRINTS = [
    main.bp,
    combat.bp,
    combatant.bp,
    group.bp,
    template.bp,
    summary.bp,
    xp.bp,
    auth.bp,
    campaign.bp,
    story_arc.bp,
    episode.bp,
    pnj.bp,
    notification.bp,
    admin.bp,
]

def register_blueprints(app):
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)

__all__ = ["register_blueprints", "BLUEPRINTS"]
