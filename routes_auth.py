# routes_auth.py
# Gestisce le rotte di autenticazione (login, registrazione, logout)

from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db


def register_auth_routes(app):
    # Pagina iniziale - Redirect in base al tipo di utente
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session.get('is_admin'):
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        return redirect(url_for('login'))

    # Login utente
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Recupera credenziali dal form
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Cerca l'utente nel database
            user = User.query.filter_by(username=username).first()
            
            # Verifica password e crea sessione
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_admin'] = user.is_admin
                flash('Login effettuato con successo!', 'success')
                
                # Redirect in base al ruolo
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Username o password errati', 'error')
        
        return render_template('login.html')

    # Logout utente
    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logout effettuato con successo', 'success')
        return redirect(url_for('login'))

    # Registrazione nuovo utente
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Controlla se username già esiste
            if User.query.filter_by(username=username).first():
                flash('Username già esistente', 'error')
                return render_template('register.html')
            
            # Controlla se email già esiste
            if User.query.filter_by(email=email).first():
                flash('Email già esistente', 'error')
                return render_template('register.html')
            
            # Crea nuovo utente con password hashata
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=False
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registrazione completata! Effettua il login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')