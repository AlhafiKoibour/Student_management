from functools import wraps
from flask import current_app, request, abort, redirect, url_for
from flask_login import current_user
import bleach
from app import db
from app.models import SecurityLog

def sanitize_input(text):
    """
    Nettoie le texte en entrée pour empêcher les injections HTML/XSS.
    Supprime toutes les balises HTML et les attributs.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        return text
    # Utilisation de bleach pour nettoyer l'entrée
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def admin_required(f):
    """
    Décorateur pour sécuriser les routes d'administration.
    Vérifie que l'utilisateur est connecté et possède le rôle d'administrateur.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            # Enregistrement de la tentative d'accès non autorisé
            log_security_event(
                user_id=current_user.id,
                action=f"Tentative d'accès non autorisé à la page : {request.path}",
                ip_address=request.remote_addr
            )
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_security_event(user_id, action, ip_address=None):
    """
    Enregistre un événement de sécurité dans la base de données et dans le fichier de log de l'application.
    """
    if ip_address is None:
        ip_address = request.remote_addr if request else "0.0.0.0"

    try:
        # Enregistrement en base de données
        log_entry = SecurityLog(
            user_id=user_id,
            action=sanitize_input(action),
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erreur lors de l'écriture du journal de sécurité en BD : {e}")

    # Enregistrement dans le fichier de log
    log_msg = f"SECURITY EVENT - User ID: {user_id} - Action: {action} - IP: {ip_address}"
    if current_app:
        current_app.logger.warning(log_msg)
    else:
        print(log_msg)
