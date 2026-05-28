import os
import sys

from sqlalchemy import inspect, text

# Ajoute le dossier courant au path python pour pouvoir importer app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, StudentProfile, SecurityLog

def sync_db():
    print("[DB SETUP] Initialisation et synchronisation de la base de donnees...")
    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if not inspector.has_table('student_profiles'):
                db.create_all()
                print("[SUCCESS] Toutes les tables ont ete creees avec succes dans student_db.")
                return

            existing_columns = {column['name'] for column in inspector.get_columns('student_profiles')}
            missing_columns = []
            if 'nom' not in existing_columns:
                missing_columns.append('nom')
            if 'prenom' not in existing_columns:
                missing_columns.append('prenom')

            if missing_columns:
                print(f"[DB UPDATE] Colonnes manquantes detectees : {missing_columns}")
                for column in missing_columns:
                    db.session.execute(text(f"ALTER TABLE student_profiles ADD COLUMN {column} VARCHAR(100)"))

                if 'nom' in missing_columns:
                    db.session.execute(text("UPDATE student_profiles SET nom = '' WHERE nom IS NULL"))
                    db.session.execute(text("ALTER TABLE student_profiles ALTER COLUMN nom SET NOT NULL"))
                if 'prenom' in missing_columns:
                    db.session.execute(text("UPDATE student_profiles SET prenom = '' WHERE prenom IS NULL"))
                    db.session.execute(text("ALTER TABLE student_profiles ALTER COLUMN prenom SET NOT NULL"))

                db.session.commit()
                print("[SUCCESS] Colonnes manquantes ajoutees et mises a jour.")
            else:
                print("[INFO] Aucune colonne manquante dans student_profiles. Aucune action requise.")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la synchronisation de la base : {e}")

if __name__ == "__main__":
    sync_db()
