# Portale Web per Creazione Macchine Virtuali ProxMox

Portale web sviluppato in Flask per la gestione e creazione di macchine virtuali tramite ProxMox, con sistema di approvazione amministrativa.

##  Caratteristiche

- **Autenticazione utenti**: Sistema di login/registrazione con distinzione tra utenti normali e amministratori
- **Gestione richieste VM**: Gli utenti possono richiedere macchine virtuali di diversi tipi (Bronze, Silver, Gold)
- **Workflow di approvazione**: Gli amministratori possono approvare o rifiutare le richieste
- **Integrazione ProxMox**: Creazione automatica delle VM tramite API ProxMox
- **Restituzione credenziali**: Gli utenti ricevono tutte le informazioni per accedere alla VM creata
- **Interfaccia moderna**: UI responsive e intuitiva

## Requisiti

- Python 3.8 o superiore
- ProxMox VE con API abilitata
- Accesso a un cluster ProxMox configurato

##  Installazione

### 1. Clona o scarica il progetto

# Portale Web per Creazione Macchine Virtuali ProxMox

Applicazione Flask per la gestione di richieste e la creazione di macchine virtuali tramite le API di ProxMox.


Caratteristiche principali

- Autenticazione utenti (utente / admin)
- Richieste VM con workflow di approvazione
- Creazione VM tramite API ProxMox
- Pagine utente e dashboard amministratore

Requisiti

- Python 3.8+
- Dipendenze: `pip install -r requirements.txt`
- Accesso a ProxMox VE con API raggiungibile

Installazione
```python
PROXMOX_CONFIG = {
    'host': '192.168.1.100',  # IP del tuo ProxMox
    'port': 8006,
    'user': 'root@pam',  # Utente ProxMox
    'password': 'your-proxmox-password',  # Password ProxMox
    'verify_ssl': False  # Disabilita verifica SSL per sviluppo
}
```

 **Per configurazione completa su ProxMox**, consulta:
- `QUICK_START.md` - Setup rapido
- `PROXMOX_SETUP.md` - Guida dettagliata

### 2. Configura i template VM

Assicurati di avere almeno un template VM configurato in ProxMox. Modifica la sezione `VM_TYPES` in `app.py` con i nomi dei tuoi template:

```python
VM_TYPES = {
    'bronze': {
        'template': 'nome-template', 
        ...
    },
    ...
}
```

### 3. Inizializza il database

Il database viene creato automaticamente al primo avvio. Viene creato un utente admin di default:
- **Username**: `admin`
- **Password**: `admin123`

 **IMPORTANTE**: Cambia la password admin in produzione!

### 4. Avvia l'applicazione

```bash
python app.py
```

L'applicazione sarà disponibile su `http://localhost:5000`

##  Utilizzo

### Per gli Utenti

1. **Registrazione**: Crea un nuovo account tramite "Registrati"
2. **Login**: Accedi con le tue credenziali
3. **Richiedi VM**: Vai su "Nuova Richiesta" e scegli il tipo di macchina virtuale
4. **Attendi approvazione**: La richiesta sarà in attesa di approvazione da parte di un amministratore
5. **Ricevi credenziali**: Una volta approvata, visualizza i dettagli della VM con tutte le credenziali di accesso

### Per gli Amministratori

1. **Login**: Accedi con le credenziali admin
2. **Dashboard**: Visualizza tutte le richieste degli utenti
3. **Approva/Rifiuta**: Clicca su "Approve" per creare la VM o "Rifiuta" per rifiutare la richiesta



## Configurazione Tipi di Macchina

Il sistema supporta tre tipologie di macchina virtuale (LXC container) basate sulla potenza:

### Bronze
- **CPU**: 1 core
- **RAM**: 512 MB
- **Disco**: 2 GB
- **Template ID**: 1800
- **Descrizione**: Macchina base per utilizzi semplici

### Silver
- **CPU**: 2 core
- **RAM**: 1024 MB (1 GB)
- **Disco**: 4 GB
- **Template ID**: 1801
- **Descrizione**: Macchina media per utilizzi standard

### Gold
- **CPU**: 2 core
- **RAM**: 2048 MB (2 GB)
- **Disco**: 8 GB
- **Template ID**: 1802
- **Descrizione**: Macchina potente per utilizzi avanzati

### Note:
- Tutte le macchine sono container LXC (Linux Containers)
- Ogni tipo utilizza un template specifico pre-configurato (ct-*-template)
- La configurazione è definita nel file di configurazione dell'applicazione
- I template con ID 1800, 1801 e 1802 devono essere preesistenti nel Proxmox


##  Note Tecniche

- Il database SQLite viene creato automaticamente come `vm_portal.db`
- Le password sono hashate con Werkzeug
- Le credenziali VM vengono generate automaticamente


## Troubleshooting

### Errore di connessione a ProxMox

- Verifica che l'IP e la porta siano corretti
- Controlla che l'API ProxMox sia abilitata
- Verifica le credenziali di accesso
- Controlla i firewall

### Template non trovato

- Verifica che il template esista in ProxMox
- Controlla che il nome del template corrisponda esattamente
- Assicurati che il template sia accessibile dal nodo specificato

### VM non si avvia

- Controlla i log di ProxMox
- Verifica che ci siano risorse disponibili sul nodo
- Controlla la configurazione di rete



