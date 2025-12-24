# proxmox.py
# Gestisce le interazioni con l'API Proxmox

import requests
import requests.auth
import traceback
from config import PROXMOX_CONFIG, VM_TYPES


# Gestione autenticazione Proxmox
def get_proxmox_auth():
    # Utilizza token API se configurato
    if PROXMOX_CONFIG.get('use_token', False):
        token_id = PROXMOX_CONFIG.get('token_id', '')
        token_secret = PROXMOX_CONFIG.get('token_secret', '')
        if not token_id or not token_secret:
            return None, None
        username = PROXMOX_CONFIG['user']
        token_username = f"{username}!{token_id}"
        auth = requests.auth.HTTPBasicAuth(token_username, token_secret)
        headers = {}
        return auth, headers

    # Altrimenti usa autenticazione con username/password
    try:
        url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/access/ticket"
        data = {
            'username': PROXMOX_CONFIG['user'],
            'password': PROXMOX_CONFIG['password']
        }
        response = requests.post(url, data=data, verify=PROXMOX_CONFIG['verify_ssl'], timeout=10)
        if response.status_code == 200:
            result = response.json()['data']
            ticket = result['ticket']
            csrf = result['CSRFPreventionToken']
            headers = {
                'Cookie': f'PVEAuthCookie={ticket}',
                'CSRFPreventionToken': csrf
            }
            return None, headers
        return None, None
    except Exception:
        traceback.print_exc()
        return None, None


# Ottiene il prossimo ID VM disponibile
def get_next_vm_id(node='px1', vm_type='lxc'):
    auth, headers = get_proxmox_auth()
    if auth is None and headers is None:
        return None
    
    try:
        endpoint = 'lxc' if vm_type == 'lxc' else 'qemu'
        url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}"
        response = requests.get(url, headers=headers, auth=auth, verify=PROXMOX_CONFIG['verify_ssl'], timeout=10)
        
        if response.status_code == 200:
            # Trova l'ID più alto e incrementa di 1
            items = response.json().get('data', [])
            max_id = 100  # ID di partenza minimo
            for item in items:
                if item.get('vmid', 0) > max_id:
                    max_id = item['vmid']
            return max_id + 1
        return 100
    except Exception:
        traceback.print_exc()
        return None


# Crea una VM da template
def create_vm_from_template(vm_id, vm_name, vm_type, node='px1', storage='local-lvm'):
    auth, headers = get_proxmox_auth()
    if auth is None and headers is None:
        return False, "Errore autenticazione ProxMox"

    vm_config = VM_TYPES[vm_type]
    try:
        template_id = vm_config['template_id']
        
        # Clona il template
        clone_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/lxc/{template_id}/clone"
        clone_data = {
            'newid': vm_id,
            'hostname': vm_name,
            'full': 1,
            'target': node,
            'storage': storage
        }
        clone_response = requests.post(clone_url, headers=headers, auth=auth, data=clone_data, 
                                     verify=PROXMOX_CONFIG['verify_ssl'], timeout=120)
        
        if clone_response.status_code == 200:
            # Avvia la VM clonata
            start_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/lxc/{vm_id}/status/start"
            start_response = requests.post(start_url, headers=headers, auth=auth, 
                                         verify=PROXMOX_CONFIG['verify_ssl'], timeout=10)
            
            if start_response.status_code == 200:
                return True, f"Container {vm_id} '{vm_name}' creato e avviato con successo"
            else:
                return False, f"Errore avvio container: {start_response.status_code}"
        else:
            return False, f"Errore clonazione: {clone_response.status_code}"
    except Exception:
        traceback.print_exc()
        return False, "Errore durante creazione"


# Ottiene lo stato di alimentazione di una VM
def get_vm_power_status(vm_id, node='px1', vm_type='lxc'):
    auth, headers = get_proxmox_auth()
    if auth is None and headers is None:
        return None
    
    endpoint = 'lxc' if vm_type == 'lxc' else 'qemu'
    try:
        status_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}/{vm_id}/status/current"
        resp = requests.get(status_url, headers=headers, auth=auth, verify=PROXMOX_CONFIG['verify_ssl'], timeout=8)
        
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            st = data.get('status')
            if st:
                return st
            if data.get('uptime'):
                return 'running'
            return 'stopped'
    except Exception:
        pass
    return None


# Elimina una VM da Proxmox
def delete_vm(vm_id, node='px1', vm_type='lxc', wait_stop_seconds=20):
    """Stop (se necessario) e rimuove la VM/container da ProxMox.
    
    Restituisce (True, message) in caso di successo, altrimenti (False, message).
    """
    auth, headers = get_proxmox_auth()
    if auth is None and headers is None:
        return False, "Errore autenticazione ProxMox"

    endpoint = 'lxc' if vm_type == 'lxc' else 'qemu'
    try:
        # Controlla se la VM è in esecuzione
        status = get_vm_power_status(vm_id, node=node, vm_type=vm_type)
        
        # Se in esecuzione, prova a fermarla
        if status == 'running':
            stop_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}/{vm_id}/status/stop"
            requests.post(stop_url, headers=headers, auth=auth, verify=PROXMOX_CONFIG['verify_ssl'], timeout=30)
            
            # Attende che la VM si spenga
            import time
            waited = 0
            while waited < wait_stop_seconds:
                st = get_vm_power_status(vm_id, node=node, vm_type=vm_type)
                if st != 'running':
                    break
                time.sleep(1)
                waited += 1

        # Elimina la VM
        del_url = f"https://{PROXMOX_CONFIG['host']}:{PROXMOX_CONFIG['port']}/api2/json/nodes/{node}/{endpoint}/{vm_id}"
        resp = requests.delete(del_url, headers=headers, auth=auth, verify=PROXMOX_CONFIG['verify_ssl'], timeout=60)
        
        if resp.status_code in (200, 204):
            return True, "VM eliminata con successo"
        else:
            return False, f"Errore eliminazione: {resp.status_code} - {resp.text[:200]}"
    except Exception as e:
        traceback.print_exc()
        return False, str(e)