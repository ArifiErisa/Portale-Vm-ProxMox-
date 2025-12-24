from datetime import datetime

# Configurazione principale dell'applicazione
PROXMOX_CONFIG = {
    'host': '192.168.56.15',
    'port': 8006,
    'user': 'root@pam',
    'password': 'Password&1',
    'use_token': False,
    'verify_ssl': False
}

# Tipi di VM/Container disponibili
VM_TYPES = {
    'bronze': {
        'name': 'Bronze',
        'description': 'Macchina base per utilizzi semplici',
        'cores': 1,
        'memory': 512,
        'disk': 2,
        'template': 'ct-bronze-template',
        'template_id': 1800,
        'type': 'lxc'
    },
    'silver': {
        'name': 'Silver',
        'description': 'Macchina media per utilizzi standard',
        'cores': 2,
        'memory': 1024,
        'disk': 4,
        'template': 'ct-silver-template',
        'template_id': 1801,
        'type': 'lxc'
    },
    'gold': {
        'name': 'Gold',
        'description': 'Macchina potente per utilizzi avanzati',
        'cores': 2,
        'memory': 2048,
        'disk': 8,
        'template': 'ct-gold-template',
        'template_id': 1802,
        'type': 'lxc'
    }
}

SECRET_KEY = 'sdfsdfkj9kwic'
SQLALCHEMY_DATABASE_URI = 'sqlite:///vm_portal.db'
