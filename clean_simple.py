from app import app
from models import db, User, VMRequest
from flask import Flask

def reset_database():
    """Resetta il database mantenendo solo l'utente admin"""
    
    with app.app_context():
        print("=== STATO INIZIALE ===")
        
        # Mostra utenti attuali
        users = User.query.all()
        print(f"Utenti totali: {len(users)}")
        for user in users:
            print(f"  ID: {user.id}, Username: {user.username}, Admin: {user.is_admin}")
        
        # Mostra richieste VM
        vm_count = VMRequest.query.count()
        print(f"\nRichieste VM totali: {vm_count}")
        
        # Chiedi conferma
        confirm = input("\nVuoi eliminare tutti gli utenti tranne admin e tutte le richieste VM? (si/no): ").lower()
        
        if confirm != 'si':
            print("Operazione annullata.")
            return
        
        try:
            # Elimina tutte le richieste VM
            deleted_vm = VMRequest.query.delete()
            print(f"\n✅ Eliminate {deleted_vm} richieste VM")
            
            # Elimina tutti gli utenti tranne admin
            deleted_users = User.query.filter(User.username != 'admin').delete()
            print(f"✅ Eliminati {deleted_users} utenti")
            
            # Commit delle modifiche
            db.session.commit()
            
            print("\n=== STATO FINALE ===")
            
            # Mostra utenti rimanenti
            remaining_users = User.query.all()
            print(f"Utenti rimanenti: {len(remaining_users)}")
            for user in remaining_users:
                print(f"  ID: {user.id}, Username: {user.username}, Admin: {user.is_admin}")
            
            # Mostra richieste VM rimanenti
            remaining_vm = VMRequest.query.count()
            print(f"\nRichieste VM rimanenti: {remaining_vm}")
            
            print("\n🎯 Database resettato con successo!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Errore durante il reset: {e}")

if __name__ == "__main__":
    reset_database()