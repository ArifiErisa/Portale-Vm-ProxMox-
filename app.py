# app.py
# File principale dell'applicazione Flask

from flask import Flask
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI
from models import db, User
from routes_auth import register_auth_routes
from routes_user import register_user_routes
from routes_admin import register_admin_routes
from werkzeug.security import generate_password_hash


def create_app():
    # Inizializzazione app Flask
    app = Flask(__name__)
    
    # Configurazione app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inizializza estensioni
    db.init_app(app)

    # Registra rotte
    register_auth_routes(app)
    register_user_routes(app)
    register_admin_routes(app)

    return app


app = create_app()


def init_db(app):
    """Crea tabelle e utente admin di default se mancante."""
    with app.app_context():
        # Crea tutte le tabelle del database
        db.create_all()
        
        # Crea utente admin se non esiste
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin', 
                email='admin@example.com', 
                password_hash=generate_password_hash('admin123'), 
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Utente admin creato: username='admin', password='admin123'")


if __name__ == '__main__':
    # Inizializza database e avvia server
    init_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)