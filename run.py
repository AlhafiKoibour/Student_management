from app import create_app, db

app = create_app()
# Initialisation de la base de données
with app.app_context():
    db.create_all()
    print("Tables créées avec succès !")

if __name__ == '__main__':
    print("[START] Demarrage du serveur StudSecure sur https://127.0.0.1:5000")
    app.run(host='0.0.0.0.', port=5000, ssl_context='adhoc', debug=True)
