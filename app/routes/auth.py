"""Routes d'authentification"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import AuthService
from app.utils.decorators import anonymous_required, login_required

# Créer le blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    """Inscription utilisateur"""
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
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """Connexion utilisateur"""
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        result = AuthService.login_user(username_or_email, password)

        if 'error' in result:
            flash(result['error'], 'error')
        else:
            session['user_id'] = result['user'].id
            flash(f'Bienvenue, {result["user"].username} !', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/login.html')


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