"""Décorateurs pour la sécurité et authentification"""
from functools import wraps
from flask import session, redirect, url_for, flash, g, request
from app.services.auth_service import AuthService


def login_required(f):
    """Décorateur pour vérifier la connexion"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté pour accéder à cette page.', 'error')
            return redirect(url_for('auth.login'))

        # Charger l'utilisateur dans g
        g.current_user = AuthService.get_user_by_id(session['user_id'])
        if not g.current_user or not g.current_user.is_active:
            session.clear()
            flash('Session invalide. Veuillez vous reconnecter.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(required_role):
    """Décorateur pour vérifier le rôle"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vous devez être connecté.', 'error')
                return redirect(url_for('auth.login'))

            user = AuthService.get_user_by_id(session['user_id'])
            if not user or user.role != required_role:
                flash('Accès interdit : permissions insuffisantes.', 'error')
                return redirect(url_for('main.index'))

            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    """Décorateur pour vérifier le rôle Admin"""
    return role_required('Admin')(f)


def mj_required(f):
    """Décorateur pour vérifier le rôle MJ"""
    return role_required('MJ')(f)


def mj_or_admin_required(f):
    """Décorateur pour vérifier le rôle MJ ou Admin"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté.', 'error')
            return redirect(url_for('auth.login'))

        user = AuthService.get_user_by_id(session['user_id'])
        if not user or user.role not in ['MJ', 'Admin']:
            flash('Accès interdit : vous devez être MJ ou Administrateur.', 'error')
            return redirect(url_for('main.index'))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def verified_required(f):
    """Décorateur pour vérifier que l'email est vérifié"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        user = AuthService.get_user_by_id(session['user_id'])
        if not user or not user.is_verified:
            flash('Veuillez vérifier votre email avant d\'accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def anonymous_required(f):
    """Décorateur pour les pages accessibles uniquement aux non-connectés"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function