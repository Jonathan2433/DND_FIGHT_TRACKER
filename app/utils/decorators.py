"""Decorateurs pour la securite et l'authentification."""
from functools import wraps

from flask import session, redirect, url_for, flash, g, request

from app.application.use_cases.auth_service import AuthService


def login_required(f):
    """Decorateur pour verifier la connexion."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez etre connecte pour acceder a cette page.', 'error')
            return redirect(url_for('auth.login', next=request.url))

        g.current_user = AuthService.get_user_by_id(session['user_id'])
        if not g.current_user or not g.current_user.is_active:
            session.clear()
            flash('Session invalide. Veuillez vous reconnecter.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(required_role):
    """Decorateur pour verifier un role strict."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vous devez etre connecte.', 'error')
                return redirect(url_for('auth.login'))

            user = AuthService.get_user_by_id(session['user_id'])
            if not user or user.role != required_role:
                flash('Acces interdit : permissions insuffisantes.', 'error')
                return redirect(url_for('main.index'))

            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    """Decorateur pour verifier le role Admin."""
    return role_required('Admin')(f)


def mj_required(f):
    """Decorateur pour verifier la capacite MJ."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez etre connecte.', 'error')
            return redirect(url_for('auth.login'))

        user = AuthService.get_user_by_id(session['user_id'])
        if not user or not user.has_mj_capability():
            flash('Acces interdit : vous devez avoir les droits MJ.', 'error')
            return redirect(url_for('main.index'))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def mj_or_admin_required(f):
    """Decorateur pour verifier la capacite MJ ou Admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez etre connecte.', 'error')
            return redirect(url_for('auth.login'))

        user = AuthService.get_user_by_id(session['user_id'])
        if not user or not (user.role == 'Admin' or user.has_mj_capability()):
            flash('Acces interdit : vous devez etre MJ ou Administrateur.', 'error')
            return redirect(url_for('main.index'))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def verified_required(f):
    """Decorateur pour verifier que l'email est verifie."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        user = AuthService.get_user_by_id(session['user_id'])
        if not user or not user.is_verified:
            flash('Veuillez verifier votre email avant d\'acceder a cette page.', 'warning')
            return redirect(url_for('auth.login'))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def anonymous_required(f):
    """Decorateur pour les pages accessibles uniquement aux non-connectes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function
