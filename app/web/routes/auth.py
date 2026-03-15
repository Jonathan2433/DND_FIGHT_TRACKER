# Migrated to app.web.routes
"""Routes d'authentification"""
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.application.use_cases.auth_service import AuthService
from app.utils.decorators import anonymous_required, login_required

# Créer le blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')


def _get_safe_next_url(raw_next_url):
    """Retourner une URL locale sûre pour la redirection post-auth."""
    if not raw_next_url:
        return ''

    parsed_url = urlparse(raw_next_url)
    if parsed_url.netloc or not parsed_url.path.startswith('/'):
        return ''

    return raw_next_url


@bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    """Inscription utilisateur"""
    invitation_token = request.values.get('invitation_token', '').strip()
    invited_email = request.values.get('invited_email', '').strip()
    next_url = _get_safe_next_url(request.values.get('next', '').strip())

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'Joueur')

        result = AuthService.register_user(username, email, password, role)

        if 'error' in result:
            flash(result['error'], 'error')
        else:
            flash(result['message'], 'success')
            if invitation_token:
                return redirect(url_for('campaign.accept_invitation', token=invitation_token))
            if next_url:
                return redirect(next_url)
            return redirect(url_for('auth.login'))

    return render_template(
        'auth/register.html',
        invitation_token=invitation_token,
        invited_email=invited_email,
        next_url=next_url,
    )


@bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """Connexion utilisateur"""
    next_url = _get_safe_next_url(request.values.get('next', '').strip())

    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        result = AuthService.login_user(username_or_email, password)

        if 'error' in result:
            flash(result['error'], 'error')
        else:
            session['user_id'] = result['user'].id
            flash(f'Bienvenue, {result["user"].username} !', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.index'))

    return render_template('auth/login.html', next_url=next_url)


@bp.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/verify/<token>')
def verify_email(token):
    """Vérification d'email"""
    result = AuthService.verify_email(token)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash('Email vérifié avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    return redirect(url_for('main.index'))


@bp.route('/profile')
@login_required
def profile():
    """Profil utilisateur"""
    from flask import g
    return render_template('auth/profile.html', user=g.current_user)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Modifier le profil utilisateur."""
    from flask import g

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        previous_email = g.current_user.email

        result = AuthService.update_profile(
            user_id=g.current_user.id,
            username=username or None,
            email=email or None,
            password=password or None,
        )

        if 'error' in result:
            flash(result['error'], 'error')
        else:
            if email and email != previous_email:
                flash('Profil mis a jour. Verifiez votre nouvel email.', 'warning')
            else:
                flash('Profil mis a jour avec succes.', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html', user=g.current_user)
