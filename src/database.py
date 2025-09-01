import sqlite3
from datetime import datetime, timedelta
import json
import os

def get_db_connection():
    """Obtient une connexion à la base de données avec gestion des accès concurrents"""
    try:
        db_file = os.environ.get('DATABASE_FILE', 'data/users.db')
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        conn = sqlite3.connect(db_file, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None

def init_database():
    """Initialise la base de données SQLite avec les tables requises"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            subscription_type TEXT DEFAULT 'free',
            subscription_date DATETIME,
            expiry_date DATETIME,
            is_premium BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table des hashs malveillants
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS malware_hashes (
            hash_value TEXT PRIMARY KEY,
            malware_name TEXT NOT NULL,
            risk_level INTEGER DEFAULT 5,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table de l'historique des scans
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            target_path TEXT,
            scan_type TEXT,
            files_scanned INTEGER,
            threats_detected INTEGER,
            duration_seconds REAL,
            scan_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table des événements système
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            description TEXT,
            severity TEXT DEFAULT 'INFO'
        )
        ''')
        
        # Insérer des hashs malveillants par défaut
        default_hashes = [
            ("d41d8cd98f00b204e9800998ecf8427e", "Empty file", 1),
            ("e99a18c428cb38d5f260853678922e03", "Test malware signature", 5),
            ("5d41402abc4b2a76b9719d911017c592", "Another test signature", 7)
        ]
        
        cursor.executemany('''
        INSERT OR IGNORE INTO malware_hashes (hash_value, malware_name, risk_level)
        VALUES (?, ?, ?)
        ''', default_hashes)
        
        conn.commit()
        conn.close()
        print("Base de données SQLite initialisée avec succès")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données SQLite: {e}")
        return False

def get_user_subscription_status(email):
    """Récupère le statut d'abonnement depuis la base de données"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 'free', False
            
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT subscription_type, expiry_date, is_premium 
        FROM users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            subscription_type = user['subscription_type'] if user['subscription_type'] else 'free'
            expiry_date = user['expiry_date']
            is_premium = bool(user['is_premium']) if user['is_premium'] is not None else False
            
            # Vérifier si l'abonnement est encore valide
            if expiry_date:
                try:
                    # Essayer d'abord le format ISO
                    expiry_datetime = datetime.fromisoformat(expiry_date)
                except ValueError:
                    try:
                        # Essayer le format du serveur webhook
                        expiry_datetime = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        # Si les deux formats échouent, considérer comme expiré
                        return 'free', False
                
                if expiry_datetime > datetime.now():
                    return subscription_type, is_premium
        
        return 'free', False
    except Exception as e:
        print(f"Erreur lors de la récupération du statut d'abonnement: {e}")
        return 'free', False

def update_user_subscription(email, subscription_type, duration_days=30):
    """Met à jour l'abonnement d'un utilisateur"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        subscription_date = datetime.now()
        expiry_date = subscription_date + timedelta(days=duration_days)
        is_premium = subscription_type != 'free'
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Mettre à jour l'utilisateur existant
            cursor.execute('''
            UPDATE users 
            SET subscription_type = ?, subscription_date = ?, expiry_date = ?, 
                is_premium = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
            ''', (subscription_type, subscription_date.isoformat(), 
                 expiry_date.isoformat(), is_premium, email))
        else:
            # Créer un nouvel utilisateur
            cursor.execute('''
            INSERT INTO users (email, subscription_type, subscription_date, expiry_date, is_premium)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, subscription_type, subscription_date.isoformat(), 
                 expiry_date.isoformat(), is_premium))
        
        conn.commit()
        conn.close()
        print(f"Abonnement mis à jour pour: {email}, type: {subscription_type}")
        return True
        
    except Exception as e:
        print(f"Erreur mise à jour abonnement: {e}")
        return False

def add_malware_hash(hash_value, malware_name, risk_level=5):
    """Ajoute un hash malveillant à la base de données"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO malware_hashes (hash_value, malware_name, risk_level)
        VALUES (?, ?, ?)
        ''', (hash_value, malware_name, risk_level))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout du hash malveillant: {e}")
        return False

def check_hash(hash_value):
    """Vérifie si un hash est connu comme malveillant"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False, None, 0
            
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT malware_name, risk_level FROM malware_hashes WHERE hash_value = ?
        ''', (hash_value,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result['malware_name'], result['risk_level']
        
        return False, None, 0
    except Exception as e:
        print(f"Erreur lors de la vérification du hash: {e}")
        return False, None, 0

def add_scan_history(email, target_path, scan_type, files_scanned, threats_detected, duration_seconds):
    """Ajoute une entrée à l'historique des scans"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO scan_history (email, target_path, scan_type, files_scanned, threats_detected, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, target_path, scan_type, files_scanned, threats_detected, duration_seconds))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout à l'historique des scans: {e}")
        return False

def get_scan_history(email, limit=50):
    """Récupère l'historique des scans d'un utilisateur"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT target_path, scan_type, files_scanned, threats_detected, 
               duration_seconds, scan_date
        FROM scan_history 
        WHERE email = ?
        ORDER BY scan_date DESC
        LIMIT ?
        ''', (email, limit))
        
        user_history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return user_history
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique des scans: {e}")
        return []