# routes_admin.py
# Gestisce le rotte amministrative del portale VM

from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models import VMRequest, User, db
from proxmox import get_next_vm_id, create_vm_from_template, delete_vm
from config import VM_TYPES


def register_admin_routes(app):
    # Dashboard amministrativa - Mostra tutte le richieste VM
    @app.route('/admin/dashboard')
    def admin_dashboard():
        # Controllo autenticazione e permessi admin
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Accesso negato', 'error')
            return redirect(url_for('login'))
        # Recupera tutte le richieste ordinate per data decrescente
        all_requests = VMRequest.query.order_by(VMRequest.requested_at.desc()).all()
        return render_template('admin_dashboard.html', requests=all_requests, vm_types=VM_TYPES)

    # Approva una richiesta VM e crea la macchina virtuale in Proxmox
    @app.route('/admin/approve/<int:request_id>', methods=['POST'])
    def approve_request(request_id):
        # Controllo autenticazione e permessi
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Accesso negato: utente non autenticato'}), 403
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Accesso negato: permessi amministratore richiesti'}), 403
        
        try:
            # Recupera la richiesta dal database
            vm_request = VMRequest.query.get_or_404(request_id)
            # Verifica che la richiesta sia ancora in attesa
            if vm_request.status != 'pending':
                return jsonify({'success': False, 'message': f'Richiesta già processata (stato: {vm_request.status})'}), 400
            
            # Genera nome VM basato su username e ID richiesta
            vm_name = f"ct-{vm_request.user.username}-{vm_request.id}"
            vm_config = VM_TYPES[vm_request.vm_type]
            container_type = vm_config.get('type', 'lxc')
            
            # Ottiene il prossimo ID VM disponibile da Proxmox
            vm_id = get_next_vm_id(vm_type=container_type)
            if not vm_id:
                return jsonify({'success': False, 'message': 'Errore comunicazione con ProxMox. Verifica configurazione e permessi token.'}), 500
            
            # Crea la VM da template in Proxmox
            success, message = create_vm_from_template(vm_id, vm_name, vm_request.vm_type)
            
            if success:
                # Credenziali fisse per tutte le VM create
                vm_password = 'Password&1'
                vm_username = 'root'
                vm_hostname = vm_name
                
                # Aggiorna il record della richiesta con i dati della VM creata
                vm_request.status = 'approved'
                vm_request.approved_at = __import__('datetime').datetime.utcnow()
                vm_request.approved_by = session['user_id']
                vm_request.vm_id = vm_id
                vm_request.vm_name = vm_name
                vm_request.vm_hostname = vm_hostname
                vm_request.vm_username = vm_username
                vm_request.vm_password = vm_password
                db.session.commit()
                
                return jsonify({'success': True, 'message': 'Creazione macchina avvenuta con successo!', 'vm_id': vm_id})
            else:
                return jsonify({'success': False, 'message': f'Errore creazione container: {message}'}), 500
        except Exception as e:
            # Gestione errori generici
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Errore imprevisto: {str(e)}'}), 500

    # Rifiuta una richiesta VM
    @app.route('/admin/reject/<int:request_id>', methods=['POST'])
    def reject_request(request_id):
        # Controllo permessi admin
        if 'user_id' not in session or not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Accesso negato'}), 403
        
        # Recupera e aggiorna lo stato della richiesta a "rejected"
        vm_request = VMRequest.query.get_or_404(request_id)
        if vm_request.status != 'pending':
            return jsonify({'success': False, 'message': 'Richiesta già processata'}), 400
        
        vm_request.status = 'rejected'
        vm_request.approved_at = __import__('datetime').datetime.utcnow()
        vm_request.approved_by = session['user_id']
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Richiesta rifiutata'})

    # Elimina una VM da Proxmox
    @app.route('/admin/delete/<int:request_id>', methods=['POST'])
    def delete_request(request_id):
        """Elimina la macchina associata a una richiesta (solo admin)."""
        # Controllo permessi admin
        if 'user_id' not in session or not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Accesso negato'}), 403

        # Recupera la richiesta VM
        vm_request = VMRequest.query.get_or_404(request_id)
        if not vm_request.vm_id:
            return jsonify({'success': False, 'message': 'Nessuna VM associata a questa richiesta'}), 400

        try:
            # Determina il tipo di VM (LXC o QEMU)
            vm_config = VM_TYPES.get(vm_request.vm_type, {})
            vm_type = vm_config.get('type', 'lxc')
            
            # Elimina la VM da Proxmox
            success, message = delete_vm(vm_request.vm_id, node='px1', vm_type=vm_type)
            
            if success:
                # Aggiorna lo stato della richiesta a "deleted"
                vm_request.status = 'deleted'
                vm_request.vm_id = None
                db.session.commit()
                return jsonify({'success': True, 'message': 'VM eliminata con successo'})
            else:
                return jsonify({'success': False, 'message': message}), 500
        except Exception as e:
            # Gestione errori
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Errore imprevisto: {str(e)}'}), 500