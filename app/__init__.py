import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

# Initialisation des extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialisation des extensions avec l'application
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Déclaration du User Loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Enregistrement des Blueprints
    from app.routes import main_bp, auth_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Ensure default admin user exists
    with app.app_context():
        from app.models import User

        default_admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@management.com')
        default_admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        default_admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'AdminPassword123!')

        db.create_all()

        admin_user = User.query.filter_by(email=default_admin_email).first()
        if admin_user is None:
            admin_user = User(
                username=default_admin_username,
                email=default_admin_email,
                role='admin',
                is_active=True
            )
            admin_user.set_password(default_admin_password)
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info(f"Default admin account created: {default_admin_email}")
        else:
            if admin_user.role != 'admin' or not admin_user.is_active:
                admin_user.role = 'admin'
                admin_user.is_active = True
                db.session.commit()
                app.logger.info(f"Default admin account updated to admin: {default_admin_email}")

    # Configuration des logs de sécurité
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/security.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Démarrage de l\'application de gestion des étudiants')

    return app
