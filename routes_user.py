# routes_user.py
# Gestisce le rotte per gli utenti normali

from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models import VMRequest, db
from config import VM_TYPES, PROXMOX_CONFIG
from proxmox import get_vm_power_status, get_proxmox_auth


def register_user_routes(app):
    # Dashboard utente - Mostra le richieste dell'utente corrente
    @app.route('/user/dashboard')
    def user_dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Recupera tutte le richieste dell'utente loggato
        user_requests = VMRequest.query.filter_by(user_id=session['user_id']).order_by(VMRequest.requested_at.desc()).all()
        return render_template('user_dashboard.html', requests=user_requests, vm_types=VM_TYPES)

    # Richiede una nuova VM
    @app.route('/user/request-vm', methods=['GET', 'POST'])
    def request_vm():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            vm_type = request.form.get('vm_type')
            # Verifica validità del tipo VM
            if vm_type not in VM_TYPES:
                flash('Tipo di VM non valido', 'error')
                return redirect(url_for('request_vm'))
            
            # Crea nuova richiesta VM
            new_request = VMRequest(user_id=session['user_id'], vm_type=vm_type, status='pending')
            db.session.add(new_request)
            db.session.commit()
            
            flash('Richiesta inviata con successo! In attesa di approvazione.', 'success')
            return redirect(url_for('user_dashboard'))
        
        return render_template('request_vm.html', vm_types=VM_TYPES)

    # Dettagli di una specifica VM
    @app.route('/user/vm-details/<int:request_id>')
    def vm_details(request_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        vm_request = VMRequest.query.get_or_404(request_id)
        
        # Controllo autorizzazione: solo proprietario o admin può vedere
        if vm_request.user_id != session['user_id']:
            flash('Accesso negato', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Ottieni stato alimentazione VM da Proxmox
        power_status = None
        if vm_request.vm_id:
            try:
                power_status = get_vm_power_status(
                    vm_request.vm_id, 
                    node='px1', 
                    vm_type=VM_TYPES.get(vm_request.vm_type, {}).get('type','lxc')
                )
            except Exception:
                power_status = None
        
        return render_template('vm_details.html', request=vm_request, power_status=power_status)

    # Avvia una VM
    @app.route('/user/start-vm/<int:request_id>', methods=['POST'])
    def start_vm(request_id):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Accesso negato'}), 403
        
        vm_request = VMRequest.query.get_or_404(request_id)
        
        # Controllo autorizzazione: solo proprietario o admin
        if not (session.get('is_admin') or vm_request.user_id == session['user_id']):
            return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
        
        if not vm_request.vm_id:
            return jsonify({'success': False, 'message': 'VM non presente o non ancora creata'}), 400
        
        node = 'px1'
        vm_type = VM_TYPES.get(vm_request.vm_type, {}).get('type', 'lxc')
        endpoint = 'lxc' if vm_type == 'lxc' else 'qemu'
        auth, headers = get_proxmox_auth()
        
        if auth is None and headers is None:
            return jsonify({'success': False, 'message': 'Errore autenticazione ProxMox'}), 500
        
        import requests
        start_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}/{vm_request.vm_id}/status/start"
       
        try:
            # Chiamata API Proxmox per avviare VM
            resp = requests.post(start_url, headers=headers, auth=auth, 
                               verify=PROXMOX_CONFIG.get('verify_ssl', True), timeout=30)
            
            if resp.status_code not in (200, 201):
                return jsonify({'success': False, 'message': f'Errore avvio VM: {resp.status_code}'}), 500
            
            vm_request.status = 'approved'
            db.session.commit()
            return jsonify({'success': True, 'message': 'VM avviata'}), 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Errore imprevisto: {str(e)}'}), 500

    # Ferma una VM
    @app.route('/user/stop-vm/<int:request_id>', methods=['POST'])
    def stop_vm(request_id):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Accesso negato'}), 403
        
        vm_request = VMRequest.query.get_or_404(request_id)
        
        if not (session.get('is_admin') or vm_request.user_id == session['user_id']):
            return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
        
        if not vm_request.vm_id:
            return jsonify({'success': False, 'message': 'VM non presente'}), 400
        
        node = 'px1'
        vm_type = VM_TYPES.get(vm_request.vm_type, {}).get('type', 'lxc')
        endpoint = 'lxc' if vm_type == 'lxc' else 'qemu'
        auth, headers = get_proxmox_auth()
        
        if auth is None and headers is None:
            return jsonify({'success': False, 'message': 'Errore autenticazione ProxMox'}), 500
        
        import requests
        stop_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}/{vm_request.vm_id}/status/stop"
        
        try:
            # Chiamata API Proxmox per fermare VM
            resp = requests.post(stop_url, headers=headers, auth=auth, 
                               verify=PROXMOX_CONFIG['verify_ssl'], timeout=30)
            
            if resp.status_code not in (200, 201):
                return jsonify({'success': False, 'message': f'Errore spegnimento VM: {resp.status_code}'}), 500
            
            # Ottieni nuovo stato dopo lo spegnimento
            st = get_vm_power_status(vm_request.vm_id, node=node, vm_type=vm_type)
            return jsonify({'success': True, 'status': st})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Errore imprevisto: {str(e)}'}), 500

    # Ottieni stato alimentazione VM
    @app.route('/user/vm-power-status/<int:request_id>', methods=['GET'])
    def vm_power_status(request_id):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Accesso negato'}), 403
        
        vm_request = VMRequest.query.get_or_404(request_id)
        
        if not (session.get('is_admin') or vm_request.user_id == session['user_id']):
            return jsonify({'success': False, 'message': 'Permessi insufficienti'}), 403
        
        if not vm_request.vm_id:
            return jsonify({'success': False, 'message': 'VM non presente'}), 400
        
        node = 'px1'
        vm_type = VM_TYPES.get(vm_request.vm_type, {}).get('type', 'lxc')
        
        # Ottieni stato da Proxmox
        status = get_vm_power_status(vm_request.vm_id, node=node, vm_type=vm_type)
        return jsonify({'success': True, 'status': status})