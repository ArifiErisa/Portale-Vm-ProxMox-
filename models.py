from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    requests = db.relationship('VMRequest', foreign_keys='VMRequest.user_id', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class VMRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vm_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    vm_id = db.Column(db.Integer, nullable=True)
    vm_name = db.Column(db.String(100), nullable=True)
    vm_hostname = db.Column(db.String(100), nullable=True)
    vm_username = db.Column(db.String(50), nullable=True)
    vm_password = db.Column(db.String(255), nullable=True)
    vm_ssh_key = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<VMRequest {self.id} - {self.vm_type}>'
