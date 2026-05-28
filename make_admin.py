import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User

def create_admin():
    email = "admin@management.com"
    username = "admin"
    password = "AdminPassword123!"

    print(f"[ADMIN SETUP] Creation de l'administrateur ({email})...")
    app = create_app()
    with app.app_context():
        try:
            # Vérifier si l'utilisateur existe déjà
            admin_user = User.query.filter_by(email=email).first()
            if admin_user:
                admin_user.role = 'admin'
                admin_user.username = username
                admin_user.set_password(password)
                db.session.commit()
                print(f"[SUCCESS] L'administrateur existe deja. Son role a ete force a 'admin' et son mot de passe reinitialise.")
            else:
                new_admin = User(
                    username=username,
                    email=email,
                    role='admin',
                    is_active=True
                )
                new_admin.set_password(password)
                db.session.add(new_admin)
                db.session.commit()
                print(f"[SUCCESS] Administrateur cree avec succes !")
                print(f"   Email: {email}")
                print(f"   Mot de passe: {password}")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la creation de l'administrateur : {e}")

if __name__ == "__main__":
    create_admin()
