# Migrated to app.web.routes
# app/routes/pnj.py - VERSION COMPLÈTE CORRIGÉE

import os
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify, current_app
from werkzeug.utils import secure_filename
from app.utils.decorators import login_required
from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.notification_service import NotificationService
from app.models import CharacterTemplate
from app.models.story_arc import StoryArc
from app.extensions import db
from app.utils import allowed_file

bp = Blueprint('pnj', __name__, url_prefix='/pnj')


@bp.route('/campaign/<int:campaign_id>/create', methods=['GET', 'POST'])
@login_required
def create_pnj(campaign_id):
    """Créer un PNJ dans une campagne"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut créer des PNJ.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    arcs = StoryArc.query.filter_by(campaign_id=campaign_id).order_by(StoryArc.order_index.asc()).all()

    if request.method == 'POST':
        try:
            image = request.files.get('image')
            image_filename = None

            if image and image.filename and allowed_file(image.filename):
                original_filename = secure_filename(image.filename)
                _, extension = os.path.splitext(original_filename)
                image_filename = f"{uuid4().hex}{extension.lower()}"
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))

            story_arc_id = request.form.get('story_arc_id', type=int)
            story_arc = None
            if story_arc_id:
                story_arc = StoryArc.query.filter_by(id=story_arc_id, campaign_id=campaign_id).first()
                if not story_arc:
                    flash("L'arc narratif sélectionné n'existe pas dans cette campagne.", 'error')
                    return render_template('pnj/create_pnj.html', campaign=campaign, arcs=arcs)

            # ✅ CORRECTION : Créer directement le PNJ avec CharacterTemplate
            pnj = CharacterTemplate(
                # Identification
                name=request.form['name'],
                first_name=request.form.get('first_name', ''),
                age=int(request.form.get('age', 0)) if request.form.get('age') else None,
                character_class=request.form.get('character_class', 'PNJ'),
                level=int(request.form.get('level', 1)),

                # Combat
                hp_max=int(request.form['hp_max']),
                hp_current=int(request.form['hp_max']),
                ac_base=int(request.form['ac_base']),
                ac_bonus=0,
                initiative_bonus=int(request.form.get('initiative_bonus', 0)),

                # Caractéristiques
                force=int(request.form.get('force', 10)),
                dexterite=int(request.form.get('dexterite', 10)),
                constitution=int(request.form.get('constitution', 10)),
                intelligence=int(request.form.get('intelligence', 10)),
                sagesse=int(request.form.get('sagesse', 10)),
                charisme=int(request.form.get('charisme', 10)),

                # Sécurité et visibilité
                owner_id=g.current_user.id,
                campaign_id=campaign_id,
                story_arc_id=story_arc.id if story_arc else None,
                character_type='PNJ',
                visibility_level=request.form.get('visibility_level', 'private'),
                is_shared=bool(request.form.get('is_shared', False)),
                is_active=True,

                # Notes
                notes=request.form.get('notes', ''),
                private_notes=request.form.get('private_notes', ''),
                background_story=request.form.get('background_story', ''),
                image_filename=image_filename,
            )

            db.session.add(pnj)
            db.session.commit()

            if pnj.is_shared:
                NotificationService.create_campaign_notification(
                    campaign,
                    "Nouveau PNJ partagé",
                    f'Le MJ a ajouté le PNJ "{pnj.name}" à la campagne "{campaign.name}".',
                    kind='shared_npc_added',
                )

            flash(f'PNJ "{pnj.name}" créé avec succès !', 'success')
            return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

        except Exception as e:
            flash(f'Erreur lors de la création : {str(e)}', 'error')

    return render_template('pnj/create_pnj.html', campaign=campaign, arcs=arcs)


@bp.route('/<int:pnj_id>/toggle_share', methods=['POST'])
@login_required
def toggle_share_pnj(pnj_id):
    """Basculer le partage d'un PNJ avec les joueurs"""
    try:
        pnj = CharacterTemplate.query.get_or_404(pnj_id)

        # Vérifier que c'est bien un PNJ et que l'utilisateur est le MJ de la campagne
        if pnj.character_type != 'PNJ':
            flash('Cette action ne concerne que les PNJ.', 'error')
            return redirect(url_for('campaign.view_campaign', campaign_id=pnj.campaign_id))

        if not pnj.campaign or not g.current_user.is_mj_of(pnj.campaign):
            flash('Seul le MJ peut modifier le partage des PNJ.', 'error')
            return redirect(url_for('campaign.view_campaign', campaign_id=pnj.campaign_id))

        # Basculer le partage
        pnj.is_shared = not pnj.is_shared
        db.session.commit()

        if pnj.is_shared:
            NotificationService.create_campaign_notification(
                pnj.campaign,
                "PNJ partagé",
                f'Le MJ a partagé le PNJ "{pnj.name}" dans la campagne "{pnj.campaign.name}".',
                kind='shared_npc_added',
            )

        status = "partagé" if pnj.is_shared else "masqué"
        flash(f'PNJ "{pnj.name}" {status} avec succès !', 'success')

        return redirect(url_for('pnj.list_campaign_pnjs', campaign_id=pnj.campaign_id))

    except Exception as e:
        flash(f'Erreur lors de la modification : {str(e)}', 'error')
        return redirect(url_for('main.index'))


# app/routes/pnj.py - MISE À JOUR DE LA MÉTHODE list_campaign_pnjs

@bp.route('/campaign/<int:campaign_id>/list')
@login_required
def list_campaign_pnjs(campaign_id):
    """Lister les PNJ d'une campagne"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign:
        flash('Campagne non trouvée.', 'error')
        return redirect(url_for('main.index'))

    # Récupérer tous les PNJ de la campagne
    selected_arc_id = request.args.get('arc_id', type=int)
    query = CharacterTemplate.query.filter_by(
        campaign_id=campaign_id,
        character_type='PNJ',
        is_active=True
    )

    if selected_arc_id:
        query = query.filter_by(story_arc_id=selected_arc_id)

    all_pnjs = query.order_by(CharacterTemplate.name.asc()).all()

    # Filtrer selon les permissions
    pnjs = []
    for pnj in all_pnjs:
        # MJ voit tout
        if g.current_user.is_mj_of(campaign):
            pnjs.append(pnj)
        # Joueurs ne voient que les PNJ partagés
        elif pnj.is_shared:
            pnjs.append(pnj)

    return render_template('pnj/list_pnjs.html',
                           campaign=campaign,
                           arcs=campaign.story_arcs,
                           selected_arc_id=selected_arc_id,
                           pnjs=pnjs,
                           is_mj=g.current_user.is_mj_of(campaign))


@bp.route('/<int:pnj_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_pnj(pnj_id):
    """Modifier un PNJ (MJ uniquement)"""
    pnj = CharacterTemplate.query.get_or_404(pnj_id)

    # Vérifier que c'est bien un PNJ
    if pnj.character_type != 'PNJ':
        flash('Cette action ne concerne que les PNJ.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    # Vérifier les permissions
    if not pnj.campaign or not g.current_user.is_mj_of(pnj.campaign):
        flash('Seul le MJ peut modifier les PNJ de sa campagne.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    if request.method == 'POST':
        try:
            # Mettre à jour les champs
            pnj.name = request.form['name']
            pnj.first_name = request.form.get('first_name', '')
            pnj.age = int(request.form.get('age', 0)) if request.form.get('age') else None
            pnj.character_class = request.form.get('character_class', 'PNJ')
            pnj.level = int(request.form.get('level', 1))
            pnj.hp_max = int(request.form['hp_max'])
            pnj.ac_base = int(request.form['ac_base'])
            pnj.initiative_bonus = int(request.form.get('initiative_bonus', 0))
            pnj.visibility_level = request.form.get('visibility_level', 'private')
            pnj.is_shared = bool(request.form.get('is_shared', False))

            # Caractéristiques
            pnj.force = int(request.form.get('force', 10))
            pnj.dexterite = int(request.form.get('dexterite', 10))
            pnj.constitution = int(request.form.get('constitution', 10))
            pnj.intelligence = int(request.form.get('intelligence', 10))
            pnj.sagesse = int(request.form.get('sagesse', 10))
            pnj.charisme = int(request.form.get('charisme', 10))

            # Notes
            pnj.notes = request.form.get('notes', '')
            pnj.private_notes = request.form.get('private_notes', '')
            pnj.background_story = request.form.get('background_story', '')

            db.session.commit()

            if pnj.is_shared:
                NotificationService.create_campaign_notification(
                    pnj.campaign,
                    "PNJ partagé mis à jour",
                    f'Le MJ a modifié le PNJ partagé "{pnj.name}" dans la campagne "{pnj.campaign.name}".',
                    kind='shared_npc_updated',
                )

            flash(f'PNJ "{pnj.name}" modifié avec succès !', 'success')
            return redirect(url_for('template.character_profile', id=pnj_id))

        except Exception as e:
            flash(f'Erreur lors de la modification : {str(e)}', 'error')

    return render_template('pnj/edit_pnj.html', pnj=pnj, campaign=pnj.campaign)


@bp.route('/<int:pnj_id>/delete', methods=['POST'])
@login_required
def delete_pnj(pnj_id):
    """Supprimer un PNJ (MJ uniquement)"""
    pnj = CharacterTemplate.query.get_or_404(pnj_id)

    # Vérifier que c'est bien un PNJ
    if pnj.character_type != 'PNJ':
        flash('Cette action ne concerne que les PNJ.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    # Vérifier les permissions
    if not pnj.campaign or not g.current_user.is_mj_of(pnj.campaign):
        flash('Seul le MJ peut supprimer les PNJ de sa campagne.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    try:
        campaign_id = pnj.campaign_id
        campaign = pnj.campaign
        pnj_name = pnj.name

        # Vérifier s'il est utilisé dans des combats
        from app.models import Combatant
        combat_usage = Combatant.query.filter_by(name=pnj.name).first()

        should_notify = pnj.is_shared
        if combat_usage:
            # Ne pas supprimer, juste désactiver
            pnj.is_active = False
            db.session.commit()
            flash(f'PNJ "{pnj_name}" désactivé (utilisé dans des combats).', 'warning')
        else:
            # Supprimer complètement
            db.session.delete(pnj)
            db.session.commit()
            flash(f'PNJ "{pnj_name}" supprimé définitivement.', 'success')

        if should_notify and campaign:
            NotificationService.create_campaign_notification(
                campaign=campaign,
                title="PNJ partagé supprimé",
                message=f'Le MJ a supprimé le PNJ partagé "{pnj_name}" dans la campagne "{campaign.name}".',
                kind='shared_npc_deleted',
            )

        return redirect(url_for('pnj.list_campaign_pnjs', campaign_id=campaign_id))

    except Exception as e:
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))


@bp.route('/<int:pnj_id>/change_visibility', methods=['POST'])
@login_required
def change_pnj_visibility(pnj_id):
    """Changer le niveau de visibilité d'un PNJ"""
    pnj = CharacterTemplate.query.get_or_404(pnj_id)

    # Vérifier que c'est bien un PNJ et les permissions
    if pnj.character_type != 'PNJ':
        flash('Cette action ne concerne que les PNJ.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    if not pnj.campaign or not g.current_user.is_mj_of(pnj.campaign):
        flash('Seul le MJ peut modifier la visibilité des PNJ.', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

    try:
        new_visibility = request.form.get('visibility_level', 'private')
        if new_visibility in ['private', 'reduced', 'semi_complete', 'complete']:
            pnj.visibility_level = new_visibility
            db.session.commit()

            flash(f'Visibilité de "{pnj.name}" mise à jour !', 'success')
        else:
            flash('Niveau de visibilité invalide.', 'error')

        return redirect(url_for('pnj.list_campaign_pnjs', campaign_id=pnj.campaign_id))

    except Exception as e:
        flash(f'Erreur lors de la modification : {str(e)}', 'error')
        return redirect(url_for('template.character_profile', id=pnj_id))

@bp.route('/campaign/<int:campaign_id>/pj/<int:pj_id>/private_notes', methods=['GET', 'POST'])
@login_required
def manage_private_notes(campaign_id, pj_id):
    """Gérer les notes privées MJ sur un PJ"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut gérer les notes privées.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    # Récupérer le PJ (doit être dans cette campagne)
    pj = CharacterTemplate.query.filter_by(
        id=pj_id,
        campaign_id=campaign_id,
        character_type='PJ'
    ).first_or_404()

    if not pj.can_add_private_notes(g.current_user):
        flash('Vous ne pouvez pas ajouter de notes privées à ce personnage.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    if request.method == 'POST':
        try:
            new_notes = request.form.get('private_notes', '')
            pj.private_notes = new_notes

            db.session.commit()

            flash(f'Notes privées sur {pj.name} mises à jour !', 'success')
            return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

        except Exception as e:
            flash(f'Erreur lors de la sauvegarde : {str(e)}', 'error')

    return render_template('pnj/private_notes.html',
                           campaign=campaign,
                           pj=pj,
                           current_notes=pj.private_notes or '')

@bp.route('/campaign/<int:campaign_id>/pj/quick_notes', methods=['POST'])
@login_required
def quick_private_notes(campaign_id):
    """Mise à jour rapide des notes privées via AJAX"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        return jsonify({'error': 'Permission refusée'}), 403

    pj_id = request.json.get('pj_id')
    notes = request.json.get('notes', '')

    pj = CharacterTemplate.query.filter_by(
        id=pj_id,
        campaign_id=campaign_id,
        character_type='PJ'
    ).first()

    if not pj or not pj.can_add_private_notes(g.current_user):
        return jsonify({'error': 'PJ non trouvé ou permission refusée'}), 404

    try:
        pj.private_notes = notes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Notes privées sur {pj.name} mises à jour'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
