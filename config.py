import os
from datetime import timedelta
from dotenv import load_dotenv

# Charge les variables d'environnement à partir du fichier .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-super-secret-key-12345')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres17:E04zTOGnvW0ISQpMtPVIBpgDPRuUKDhr@dpg-d8c6dm7avr4c73eh7q10-a/student_db_dp9z')
   # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql+pg8000://postgres:evrad@localhost:5432/student_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sécurisation des sessions
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuration des uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join('app', 'static', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)) # 5 Mo
