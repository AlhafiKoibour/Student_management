import os
import sys

# Ajoute le dossier courant au path python pour pouvoir importer app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import StudentProfile

def update_profiles():
    """
    Met à jour tous les profils existants en remplissant les champs nom et prenom.
    Si vides, utilise le matricule en tant que défaut.
    """
    print("[UPDATE PROFILES] Démarrage de la mise à jour des profils...")
    app = create_app()
    
    with app.app_context():
        try:
            # Récupérer tous les profils avec nom ou prenom vides
            profiles = StudentProfile.query.filter(
                (StudentProfile.nom == '') | (StudentProfile.prenom == '') | 
                (StudentProfile.nom.is_(None)) | (StudentProfile.prenom.is_(None))
            ).all()
            
            if not profiles:
                print("[INFO] Aucun profil à mettre à jour. Tous les profils ont nom et prenom remplis.")
                return
            
            print(f"[UPDATE PROFILES] {len(profiles)} profil(s) trouvé(s) à mettre à jour.")
            
            updated_count = 0
            for profile in profiles:
                old_nom = profile.nom or "vide"
                old_prenom = profile.prenom or "vide"
                
                # Si nom vide, utiliser une partie du matricule
                if not profile.nom or profile.nom == '':
                    profile.nom = profile.matricule.split('-')[0] if '-' in profile.matricule else profile.matricule
                
                # Si prenom vide, utiliser "Etudiant"
                if not profile.prenom or profile.prenom == '':
                    profile.prenom = "Etudiant"
                
                print(f"  Profil {profile.matricule}: nom '{old_nom}' → '{profile.nom}', prenom '{old_prenom}' → '{profile.prenom}'")
                updated_count += 1
            
            # Sauvegarder tous les changements
            db.session.commit()
            print(f"\n[SUCCESS] {updated_count} profil(s) mis à jour avec succès dans la base de données.")
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Erreur lors de la mise à jour des profils : {e}")

if __name__ == "__main__":
    update_profiles()
