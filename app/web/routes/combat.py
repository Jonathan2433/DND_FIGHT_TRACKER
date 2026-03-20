"""Routes pour la gestion des combats"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, g, flash, current_app

from app.application.use_cases import CombatService, CombatantService, GroupService, TemplateService, NotificationService, EmailService
from app.models import Combat, CharacterTemplate, EncounterTemplate, CampaignMember, User
from app.domain.policies import CombatPolicy, EncounterTemplatePolicy
from app.utils import CONDITIONS_LIST, CONDITIONS_DESCRIPTIONS, MONSTER_TEMPLATES, get_initiative_order, get_current_actor
from werkzeug.utils import secure_filename
from uuid import uuid4
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import os
import json
from app.utils.decorators import login_required
from app.extensions import socketio


bp = Blueprint('combat', __name__, url_prefix='/combat')


def _can_manage_combat(combat):
    return CombatPolicy.can_manage(g.current_user, combat)


def _can_view_player_combat(combat):
    return CombatPolicy.can_view_player(g.current_user, combat)


def _parse_battlemap_tokens(raw_tokens):
    if not raw_tokens:
        return {}
    try:
        parsed = json.loads(raw_tokens)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


def _save_uploaded_media(file_storage, allowed_extensions):
    if not file_storage or not file_storage.filename:
        return None
    extension = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    if extension not in allowed_extensions:
        return None
    filename = f"{uuid4().hex}_{secure_filename(file_storage.filename)}"
    file_storage.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return filename


def _save_remote_image(image_url, allowed_extensions):
    if not image_url:
        return None

    trimmed_url = image_url.strip()
    parsed = urlparse(trimmed_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None

    try:
        request_obj = Request(trimmed_url, headers={'User-Agent': 'DND-Fight-Tracker/1.0'})
        with urlopen(request_obj, timeout=8) as response:
            content_type = (response.headers.get('Content-Type') or '').split(';')[0].strip().lower()
            extension_from_type = {
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/webp': 'webp',
            }.get(content_type)

            path_extension = parsed.path.rsplit('.', 1)[-1].lower() if '.' in parsed.path else ''
            extension = extension_from_type or path_extension
            if extension == 'jpeg':
                extension = 'jpg'

            if extension not in allowed_extensions:
                return None

            filename = f"{uuid4().hex}_remote.{extension}"
            destination = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(destination, 'wb') as output_file:
                output_file.write(response.read())
            return filename
    except Exception:
        return None




def _campaign_players(combat):
    """Lister les joueurs de la campagne (hors MJ) pour invitation de combat."""
    memberships = CampaignMember.query.filter_by(campaign_id=combat.campaign_id).all()
    user_ids = [member.user_id for member in memberships if member.user_id != combat.campaign.mj_id]
    if not user_ids:
        return []

    users = User.query.filter(User.id.in_(user_ids), User.is_active.is_(True)).order_by(User.username.asc()).all()
    return users

def _get_player_controlled_combatant_ids(combat, user):
    """Retourne les IDs des tokens PJ contrôlés par l'utilisateur courant."""
    if not user:
        return []

    player_characters = CharacterTemplate.query.filter_by(
        owner_id=user.id,
        character_type='PJ',
        is_active=True,
    ).all()

    owned_names = {character.name.strip().lower() for character in player_characters if character.name}
    if not owned_names:
        return []

    return [
        combatant.id
        for combatant in combat.combatants
        if combatant.type == 'PJ' and combatant.name and combatant.name.strip().lower() in owned_names
    ]


@bp.route('/create', methods=['POST'])
@login_required
def create_combat():
    """Creer un nouveau combat rattache a un arc narratif."""
    story_arc_id = request.form.get('story_arc_id')
    episode_id = request.form.get('episode_id')

    if not story_arc_id or not episode_id:
        flash("Un combat doit obligatoirement etre rattache a un arc et un episode.", "error")
        return redirect(url_for('main.index'))

    from app.models.story_arc import StoryArc
    from app.models.episode import Episode

    arc = StoryArc.query.get_or_404(int(story_arc_id))
    episode = Episode.query.get_or_404(int(episode_id))
    if episode.story_arc_id != arc.id:
        flash("Episode invalide pour cet arc narratif.", "error")
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))
    if not (g.current_user.role == 'Admin' or g.current_user.is_mj_of(arc.campaign)):
        flash("Seul le MJ proprietaire peut creer un combat sur cet arc.", "error")
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    name = request.form['name']
    combat = CombatService.create_combat(
        name=name,
        story_arc_id=arc.id,
        campaign_id=arc.campaign_id,
        episode_id=episode.id,
    )

    return redirect(url_for('combat.view_combat', combat_id=combat.id))


@bp.route('/<int:combat_id>')
@login_required
def view_combat(combat_id):
    """Afficher un combat (vue MJ)."""
    combat = Combat.query.get_or_404(combat_id)
    if not _can_manage_combat(combat):
        flash('Seul le MJ proprietaire peut acceder a la gestion du combat.', 'error')
        return redirect(url_for('combat.view_combat_player', combat_id=combat_id))

    combat_data = CombatService.get_combat_with_organized_data(combat_id)
    character_templates = CharacterTemplate.query.all()
    if g.current_user.role == 'Admin':
        encounter_templates = EncounterTemplate.query.all()
    else:
        encounter_templates = EncounterTemplate.query.filter_by(owner_id=g.current_user.id).all()

    current_actor = get_current_actor(combat_data['combat'])

    return render_template(
        'combat.html',
        combat=combat_data['combat'],
        current_actor=current_actor,
        groups=combat_data['groups'],
        singles=combat_data['singles'],
        group_condition_states=combat_data['group_condition_states'],
        conditions_list=CONDITIONS_LIST,
        conditions_descriptions=CONDITIONS_DESCRIPTIONS,
        MONSTER_TEMPLATES=MONSTER_TEMPLATES,
        character_templates=character_templates,
        encounter_templates=encounter_templates,
        start_time=combat_data['combat'].start_time,
        round_start=combat_data['combat'].current_round_start,
        turn_start=combat_data['combat'].current_turn_start,
        initiative_order=combat_data['initiative_order'],
        battlemap_tokens=_parse_battlemap_tokens(combat_data['combat'].battlemap_tokens_json),
        campaign_players=_campaign_players(combat_data['combat'])
    )


@bp.route('/<int:combat_id>/player')
@login_required
def view_combat_player(combat_id):
    """Vue joueur pour un combat."""
    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        flash('Acces non autorise a ce combat.', 'error')
        return redirect(url_for('main.index'))

    combat_data = CombatService.get_combat_with_organized_data(combat_id)
    combatants_sorted = get_initiative_order(combat.combatants)
    current_actor = get_current_actor(combat)
    player_controlled_ids = _get_player_controlled_combatant_ids(combat, g.current_user)

    return render_template(
        'combat_player.html',
        combat=combat,
        combatants=combatants_sorted,
        current_actor=current_actor,
        start_time=combat.start_time,
        round_start=combat.current_round_start,
        turn_start=combat.current_turn_start,
        groups=combat_data['groups'],
        singles=combat_data['singles'],
        group_condition_states=combat_data['group_condition_states'],
        battlemap_tokens=_parse_battlemap_tokens(combat.battlemap_tokens_json),
        player_controlled_ids=player_controlled_ids
    )




@bp.route('/<int:combat_id>/invite_players', methods=['POST'])
@login_required
def invite_players_to_combat(combat_id):
    """Envoyer des invitations de combat aux joueurs sélectionnés."""
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    combat = Combat.query.get_or_404(combat_id)
    selected_ids = request.form.getlist('player_ids')
    if not selected_ids:
        flash('Selectionnez au moins un joueur a inviter.', 'warning')
        return redirect(url_for('combat.view_combat', combat_id=combat_id))

    selected_user_ids = []
    for user_id in selected_ids:
        try:
            selected_user_ids.append(int(user_id))
        except (TypeError, ValueError):
            continue

    if not selected_user_ids:
        flash('Selection de joueurs invalide.', 'warning')
        return redirect(url_for('combat.view_combat', combat_id=combat_id))

    campaign_user_ids = {member.user_id for member in CampaignMember.query.filter_by(campaign_id=combat.campaign_id).all()}
    invited_users = User.query.filter(User.id.in_(selected_user_ids), User.is_active.is_(True)).all()

    invitation_url = url_for('combat.join_combat', combat_id=combat_id, _external=True)
    invited_count = 0
    email_failed_count = 0

    for user in invited_users:
        if user.id not in campaign_user_ids or user.id == combat.campaign.mj_id:
            continue

        NotificationService.create_notification(
            user_id=user.id,
            title='Invitation au combat',
            message=f'Le MJ vous invite au combat "{combat.name}". Cliquez pour rejoindre la vue joueur.',
            kind=f'combat_invitation:{combat.id}',
            campaign_id=combat.campaign_id,
            auto_commit=False,
        )
        if user.email:
            try:
                email_result = EmailService.send_combat_invitation(
                    user_email=user.email,
                    username=user.username,
                    campaign_name=combat.campaign.name,
                    combat_name=combat.name,
                    invitation_url=invitation_url,
                )
                if email_result and email_result.get('error'):
                    email_failed_count += 1
            except Exception:
                email_failed_count += 1
        invited_count += 1

    from app.extensions import db
    db.session.commit()

    if invited_count:
        flash(f'{invited_count} invitation(s) envoyee(s) (notification in-app).', 'success')
        if email_failed_count:
            flash(
                f'Email indisponible pour {email_failed_count} invitation(s) (configuration SMTP ou adresse email).',
                'warning'
            )
    else:
        flash('Aucun joueur valide a inviter.', 'warning')

    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/join')
@login_required
def join_combat(combat_id):
    """Lien d'invitation vers la vue joueur d'un combat."""
    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        flash('Acces non autorise a ce combat.', 'error')
        return redirect(url_for('main.index'))

    return redirect(url_for('combat.view_combat_player', combat_id=combat_id))


def _require_manage_or_redirect(combat_id):
    combat = Combat.query.get_or_404(combat_id)
    if _can_manage_combat(combat):
        return None
    flash('Action reservee au MJ proprietaire.', 'error')
    return redirect(url_for('combat.view_combat_player', combat_id=combat_id))


@bp.route('/<int:combat_id>/start')
@login_required
def start_combat(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.start_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/next_turn')
@login_required
def next_turn(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.next_turn(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/close')
@login_required
def close_combat(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    combat = CombatService.close_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('summary.combat_summary', combat_id=combat.id))


@bp.route('/<int:combat_id>/add', methods=['POST'])
@login_required
def add_combatant(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatantService.add_combatant(
        combat_id=combat_id,
        name=request.form['name'],
        type=request.form['type'],
        hp_max=int(request.form['hp_max']),
        hp_current=request.form.get('hp_current'),
        initiative=int(request.form['initiative']),
        ac_base=int(request.form['ac'])
    )
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/add_character_template', methods=['POST'])
@login_required
def add_character_template(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    template_id = request.form.get('template_id')
    initiative = int(request.form.get('initiative'))

    TemplateService.add_character_template_to_combat(combat_id, template_id, initiative)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/load_encounter', methods=['POST'])
@login_required
def load_encounter(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    encounter_id = int(request.form['encounter_id'])
    encounter = EncounterTemplate.query.get_or_404(encounter_id)
    if not EncounterTemplatePolicy.can_manage(g.current_user, encounter):
        flash('Template de rencontre non autorise.', 'error')
        return redirect(url_for('combat.view_combat', combat_id=combat_id))

    TemplateService.load_encounter_template(combat_id, encounter_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/add_template', methods=['POST'])
@login_required
def add_template(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    template_name = request.form['template']
    quantity = int(request.form['quantity'])
    manual_initiative = request.form.get('initiative')
    monster_image = request.files.get('monster_image')
    monster_image_url = request.form.get('monster_image_url', '').strip()
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}

    monster_image_filename = _save_uploaded_media(monster_image, allowed_extensions) if monster_image else None
    if not monster_image_filename and monster_image_url:
        downloaded_image_filename = _save_remote_image(monster_image_url, allowed_extensions)
        monster_image_filename = downloaded_image_filename or monster_image_url

    TemplateService.add_monster_template_to_combat(
        combat_id,
        template_name,
        quantity,
        manual_initiative,
        monster_image_filename=monster_image_filename
    )
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/create_group', methods=['POST'])
@login_required
def create_group(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    ids = request.form.getlist('selected_combatants')
    GroupService.create_group([int(combatant_id) for combatant_id in ids])
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/battlemap/media', methods=['POST'])
@login_required
def upload_battlemap_media(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    combat = Combat.query.get_or_404(combat_id)
    media = request.files.get('battlemap_media')
    filename = _save_uploaded_media(media, {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'webm'})
    if not filename:
        flash('Fichier invalide. Formats autorises: png, jpg, jpeg, webp, mp4, webm.', 'error')
        return redirect(url_for('combat.view_combat', combat_id=combat_id))

    extension = filename.rsplit('.', 1)[-1].lower()
    combat.battlemap_media_filename = filename
    combat.battlemap_media_type = 'video' if extension in {'mp4', 'webm'} else 'image'

    from app.extensions import db
    db.session.commit()
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/battlemap/tokens', methods=['POST'])
@login_required
def save_battlemap_tokens(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    combat = Combat.query.get_or_404(combat_id)
    payload = request.get_json(silent=True) or {}
    tokens = payload.get('tokens', {})
    if not isinstance(tokens, dict):
        return jsonify({'error': 'invalid tokens'}), 400

    combat.battlemap_tokens_json = json.dumps(tokens)

    from app.extensions import db
    db.session.commit()
    broadcast_combat_update(combat_id)
    return jsonify({'status': 'ok'})


@bp.route('/<int:combat_id>/battlemap/player-token', methods=['POST'])
@login_required
def save_player_token_position(combat_id):
    """Autorise un joueur à déplacer uniquement son token et uniquement pendant son tour."""
    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        return jsonify({'error': 'forbidden'}), 403

    payload = request.get_json(silent=True) or {}
    token_id = payload.get('token_id')
    x = payload.get('x')
    y = payload.get('y')

    try:
        token_id = int(token_id)
        x = float(x)
        y = float(y)
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid payload'}), 400

    current_actor = get_current_actor(combat)
    player_controlled_ids = _get_player_controlled_combatant_ids(combat, g.current_user)

    if token_id not in player_controlled_ids:
        return jsonify({'error': 'token_not_owned'}), 403

    if not current_actor or current_actor.id != token_id:
        return jsonify({'error': 'not_your_turn'}), 403

    tokens = _parse_battlemap_tokens(combat.battlemap_tokens_json)
    tokens[str(token_id)] = {
        'x': max(0, min(100, x)),
        'y': max(0, min(100, y)),
    }
    combat.battlemap_tokens_json = json.dumps(tokens)

    from app.extensions import db
    db.session.commit()
    broadcast_combat_update(combat_id)
    return jsonify({'status': 'ok'})


@bp.route('/<int:combat_id>/state')
@login_required
def combat_state(combat_id):
    """Etat JSON du combat pour synchronisation."""
    from app.utils import get_current_actor

    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        return jsonify({'error': 'forbidden'}), 403

    combatants = get_initiative_order(combat.combatants)
    current_actor = get_current_actor(combat)
    player_controlled_ids = _get_player_controlled_combatant_ids(combat, g.current_user)

    return jsonify({
        'round': combat.round,
        'current_actor_id': current_actor.id if current_actor else None,
        'battlemap_media_filename': combat.battlemap_media_filename,
        'battlemap_media_type': combat.battlemap_media_type,
        'battlemap_tokens': _parse_battlemap_tokens(combat.battlemap_tokens_json),
        'player_controlled_ids': player_controlled_ids,
        'combatants': [
            {
                'id': c.id,
                'name': c.name,
                'type': c.type,
                'hp_current': c.hp_current,
                'hp_max': c.hp_max,
                'temp_hp': c.temp_hp,
                'initiative': c.initiative,
                'ac_total': c.ac_total,
                'is_dead': c.is_dead,
                'has_fled': c.has_fled,
                'conditions': c.conditions.split(',') if c.conditions else [],
                'notes': c.notes,
                'token_label': c.token_label
            }
            for c in combatants
        ]
    })


@bp.route('/<int:combat_id>/delete', methods=['POST'])
@login_required
def delete_combat(combat_id):
    """Supprimer un combat."""
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.delete_combat(combat_id)
    return redirect(url_for('main.index'))


def broadcast_combat_update(combat_id):
    """Diffuser une mise a jour via SocketIO."""
    socketio.emit(
        'combat_update',
        {'combat_id': combat_id},
        room=f'combat_{combat_id}'
    )
