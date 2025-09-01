from flask import Flask, request, jsonify
import stripe
import os
from datetime import datetime, timedelta
import hashlib
import json
import logging
from functools import wraps
import threading
import time
import sqlite3
import re
from cachetools import TTLCache
import secrets
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration depuis les variables d'environnement (obligatoire)
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY doit être défini dans les variables d'environnement")

STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("STRIPE_WEBHOOK_SECRET doit être défini dans les variables d'environnement")

DATABASE_FILE = os.environ.get('DATABASE_FILE', 'data/users.db')
MAX_SCAN_FILES = int(os.environ.get('MAX_SCAN_FILES', 1000))
MAX_CACHE_SIZE = int(os.environ.get('MAX_CACHE_SIZE', 1000))
CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))  # 5 minutes

stripe.api_key = STRIPE_SECRET_KEY

# Configuration des abonnements (cohérent avec Streamlit)
SUBSCRIPTION_PLANS = {
    "monthly": {"days": 30, "price": 5.99, "name": "Mensuel", "stripe_price_id": "price_monthly_test"},
    "yearly": {"days": 365, "price": 59.00, "name": "Annuel", "stripe_price_id": "price_yearly_test", "saving": "17%"},
    "lifetime": {"days": 365*10, "price": 259.00, "name": "Accès Permanent", "stripe_price_id": "price_lifetime_test"}
}

# Cache avec limite de taille et expiration
hash_cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=CACHE_TTL)

# Validation email avec regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Import des fonctions de base de données
from src.database import init_database, get_db_connection, update_user_subscription, check_hash, add_malware_hash, add_scan_history, get_user_subscription_status

# Décorateur pour la validation des données utilisateur
def validate_user_data(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if request.method in ['POST', 'PUT']:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Données JSON requises'}), 400
                
                # Validation de l'email
                if 'email' in data:
                    email = data['email']
                    if not isinstance(email, str) or not EMAIL_REGEX.match(email):
                        return jsonify({'error': 'Email invalide'}), 400
                
                # Validation du type d'abonnement
                if 'subscription_type' in data:
                    subscription_type = data['subscription_type']
                    if subscription_type not in ['free', 'monthly', 'yearly', 'lifetime']:
                        return jsonify({'error': 'Type d\'abonnement invalide'}), 400
        except Exception as e:
            logger.error(f"Erreur de validation: {e}")
            return jsonify({'error': 'Erreur de validation des données'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour la gestion des erreurs de base de données
def handle_db_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except sqlite3.Error as e:
            logger.error(f"Erreur base de données SQLite: {e}")
            return jsonify({'error': 'Erreur de base de données'}), 500
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return jsonify({'error': 'Erreur serveur'}), 500
    return decorated_function

# Décorateur pour la limitation de débit (rate limiting)
def rate_limit(requests_per_minute=60):
    def decorator(f):
        request_times = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Identifier le client par IP
            client_ip = request.remote_addr
            
            current_time = time.time()
            
            # Nettoyer les anciennes requêtes
            request_times[client_ip] = [
                t for t in request_times.get(client_ip, []) 
                if current_time - t < 60
            ]
            
            # Vérifier la limite
            if len(request_times[client_ip]) >= requests_per_minute:
                logger.warning(f"Rate limit dépassé pour: {client_ip}")
                return jsonify({'error': 'Trop de requêtes. Veuillez réessayer plus tard.'}), 429
            
            # Ajouter la requête actuelle
            request_times[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/webhook', methods=['POST'])
@rate_limit(30)  # 30 requêtes par minute maximum
def webhook_received():
    """Endpoint pour recevoir les webhooks Stripe avec vérification de signature"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        logger.error("Signature Stripe manquante")
        return 'Signature manquante', 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"Webhook reçu: {event['type']}")
        
        # Vérifier le timestamp pour prévenir les replay attacks
        event_time = event['created']
        current_time = time.time()
        if abs(current_time - event_time) > 300:  # 5 minutes de tolérance
            logger.warning(f"Webhook trop ancien: {event_time}, rejeté")
            return 'Webhook trop ancien', 400
            
    except ValueError as e:
        logger.error(f"Payload invalide: {e}")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Signature invalide: {e}")
        return 'Invalid signature', 400
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}")
        return 'Server error', 500

    # Gérer les différents types d'événements
    try:
        if event['type'] == 'checkout.session.completed':
            handle_checkout_session(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_cancelled(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        else:
            logger.info(f"Événement non traité: {event['type']}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'événement {event['type']}: {e}")
        return 'Server error', 500
    
    return jsonify(success=True)

def handle_checkout_session(session):
    """Active l'abonnement après paiement réussi"""
    try:
        customer_email = session['customer_details']['email']
        subscription_id = session.get('subscription')
        
        # Déterminer le type d'abonnement
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = subscription['items']['data'][0]['price']['id']
            
            # Mapper price_id au type d'abonnement
            if 'monthly' in price_id:
                plan_type = 'monthly'
                duration_days = SUBSCRIPTION_PLANS['monthly']['days']
            elif 'yearly' in price_id:
                plan_type = 'yearly'
                duration_days = SUBSCRIPTION_PLANS['yearly']['days']
            else:
                plan_type = 'monthly'
                duration_days = SUBSCRIPTION_PLANS['monthly']['days']
        else:
            # Pour les paiements uniques (lifetime)
            plan_type = 'lifetime'
            duration_days = SUBSCRIPTION_PLANS['lifetime']['days']
        
        # Mettre à jour la base de données
        success = update_user_subscription(customer_email, plan_type, duration_days)
        
        if success:
            logger.info(f"Abonnement activé pour: {customer_email}, plan: {plan_type}")
        else:
            logger.error(f"Erreur lors de l'activation de l'abonnement pour: {customer_email}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}")

def handle_subscription_cancelled(subscription):
    """Gère l'annulation d'abonnement"""
    try:
        customer_id = subscription['customer']
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer['email']
        
        # Mettre à jour la base de données
        success = update_user_subscription(customer_email, 'free', 0)
        
        if success:
            logger.info(f"Abonnement annulé pour: {customer_email}")
        else:
            logger.error(f"Erreur lors de l'annulation pour: {customer_email}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation: {e}")

def handle_subscription_updated(subscription):
    """Gère la mise à jour d'abonnement"""
    try:
        customer_id = subscription['customer']
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer['email']
        
        # Vérifier le statut de l'abonnement
        if subscription['status'] in ['active', 'trialing']:
            # Déterminer le type d'abonnement
            price_id = subscription['items']['data'][0]['price']['id']
            
            if 'monthly' in price_id:
                plan_type = 'monthly'
                duration_days = SUBSCRIPTION_PLANS['monthly']['days']
            elif 'yearly' in price_id:
                plan_type = 'yearly'
                duration_days = SUBSCRIPTION_PLANS['yearly']['days']
            else:
                plan_type = 'monthly'
                duration_days = SUBSCRIPTION_PLANS['monthly']['days']
            
            # Mettre à jour la base de données
            success = update_user_subscription(customer_email, plan_type, duration_days)
            
            if success:
                logger.info(f"Abonnement mis à jour pour: {customer_email}, plan: {plan_type}")
            else:
                logger.error(f"Erreur lors de la mise à jour pour: {customer_email}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'abonnement: {e}")

def handle_payment_failed(invoice):
    """Gère les échecs de paiement"""
    try:
        customer_id = invoice['customer']
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer['email']
        
        # Mettre à jour le statut de l'utilisateur
        success = update_user_subscription(customer_email, 'free', 0)
        
        if success:
            logger.info(f"Paiement échoué pour: {customer_email}, abonnement révoqué")
        else:
            logger.error(f"Erreur lors de la révocation pour: {customer_email}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'échec de paiement: {e}")

@app.route('/user/<email>', methods=['GET'])
@handle_db_errors
@rate_limit()
def get_user_status(email):
    """Endpoint pour vérifier le statut d'un utilisateur"""
    try:
        # Validation de l'email
        if not isinstance(email, str) or not EMAIL_REGEX.match(email):
            return jsonify({'error': 'Email invalide'}), 400
            
        subscription_status, is_premium = get_user_subscription_status(email)
        return jsonify({
            'email': email,
            'subscription_status': subscription_status,
            'is_premium': is_premium
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut utilisateur: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/user', methods=['POST'])
@validate_user_data
@handle_db_errors
@rate_limit(10)  # 10 requêtes par minute pour cet endpoint
def create_or_update_user():
    """Endpoint pour créer ou mettre à jour un utilisateur"""
    try:
        data = request.get_json()
        email = data['email']
        subscription_type = data.get('subscription_type', 'free')
        
        # Déterminer la durée en fonction du type d'abonnement
        if subscription_type == 'monthly':
            duration_days = SUBSCRIPTION_PLANS['monthly']['days']
        elif subscription_type == 'yearly':
            duration_days = SUBSCRIPTION_PLANS['yearly']['days']
        elif subscription_type == 'lifetime':
            duration_days = SUBSCRIPTION_PLANS['lifetime']['days']
        else:
            duration_days = 0  # Free
        
        success = update_user_subscription(email, subscription_type, duration_days)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Utilisateur créé/mis à jour avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la création/mise à jour'
            }), 500
    except Exception as e:
        logger.error(f"Erreur lors de la création/mise à jour de l'utilisateur: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/hash/check/<hash_value>', methods=['GET'])
@handle_db_errors
@rate_limit()
def check_hash_endpoint(hash_value):
    """Endpoint pour vérifier un hash contre la base de données malware"""
    try:
        # Validation du hash
        if not isinstance(hash_value, str) or len(hash_value) not in [32, 40, 64]:
            return jsonify({'error': 'Format de hash invalide'}), 400
            
        is_malicious, malware_name, risk_level = check_hash(hash_value)
        return jsonify({
            'hash': hash_value,
            'is_malicious': is_malicious,
            'malware_name': malware_name,
            'risk_level': risk_level
        })
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du hash: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/hash/add', methods=['POST'])
@validate_user_data
@handle_db_errors
@rate_limit(5)  # 5 requêtes par minute pour cet endpoint
def add_hash_endpoint():
    """Endpoint pour ajouter un hash malveillant"""
    try:
        data = request.get_json()
        hash_value = data.get('hash')
        malware_name = data.get('malware_name', 'Unknown')
        risk_level = data.get('risk_level', 5)
        
        # Validation des données
        if not hash_value or not isinstance(hash_value, str) or len(hash_value) not in [32, 40, 64]:
            return jsonify({'error': 'Hash invalide'}), 400
            
        if not malware_name or not isinstance(malware_name, str) or len(malware_name) > 255:
            return jsonify({'error': 'Nom de malware invalide'}), 400
            
        if not isinstance(risk_level, int) or risk_level < 1 or risk_level > 10:
            return jsonify({'error': 'Niveau de risque invalide (1-10)'}), 400
        
        success = add_malware_hash(hash_value, malware_name, risk_level)
        
        return jsonify({
            'success': success,
            'message': 'Hash ajouté avec succès' if success else 'Échec de l\'ajout du hash'
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du hash: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/scan/history', methods=['POST'])
@validate_user_data
@handle_db_errors
@rate_limit(20)
def add_scan_history_endpoint():
    """Endpoint pour ajouter une entrée à l'historique des scans"""
    try:
        data = request.get_json()
        email = data.get('email')
        target_path = data.get('target_path')
        scan_type = data.get('scan_type')
        files_scanned = data.get('files_scanned', 0)
        threats_detected = data.get('threats_detected', 0)
        duration_seconds = data.get('duration_seconds', 0)
        
        # Validation des données
        if not all([email, target_path, scan_type]):
            return jsonify({'error': 'Données manquantes'}), 400
            
        if not isinstance(files_scanned, int) or files_scanned < 0:
            return jsonify({'error': 'Nombre de fichiers scannés invalide'), 400
            
        if not isinstance(threats_detected, int) or threats_detected < 0:
            return jsonify({'error': 'Nombre de menaces détectées invalide'}), 400
            
        if not isinstance(duration_seconds, (int, float)) or duration_seconds < 0:
            return jsonify({'error': 'Durée invalide'}), 400
        
        # Limiter le nombre de fichiers scannés pour la sécurité
        if files_scanned > MAX_SCAN_FILES:
            files_scanned = MAX_SCAN_FILES
            logger.warning(f"Nombre de fichiers scannés limité à {MAX_SCAN_FILES} pour {email}")
        
        success = add_scan_history(email, target_path, scan_type, files_scanned, threats_detected, duration_seconds)
        
        return jsonify({
            'success': success,
            'message': 'Historique de scan ajouté avec succès' if success else 'Échec de l\'ajout'
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'historique de scan: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/scan/history/<email>', methods=['GET'])
@handle_db_errors
@rate_limit()
def get_scan_history(email):
    """Endpoint pour récupérer l'historique des scans d'un utilisateur"""
    try:
        # Validation de l'email
        if not isinstance(email, str) or not EMAIL_REGEX.match(email):
            return jsonify({'error': 'Email invalide'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT target_path, scan_type, files_scanned, threats_detected, 
               duration_seconds, scan_date
        FROM scan_history 
        WHERE email = ?
        ORDER BY scan_date DESC
        LIMIT 50
        ''', (email,))
        
        user_history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'email': email,
            'scan_history': user_history,
            'total_scans': len(user_history)
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique des scans: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/health', methods=['GET'])
@rate_limit()
def health_check():
    """Endpoint de santé"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Compter les utilisateurs
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()['count']
        
        # Compter les hashes malware
        cursor.execute('SELECT COUNT(*) as count FROM malware_hashes')
        malware_hashes_count = cursor.fetchone()['count']
        
        # Compter les scans historiques
        cursor.execute('SELECT COUNT(*) as count FROM scan_history')
        scan_history_count = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'healthy', 
            'timestamp': datetime.now().isoformat(),
            'database_file': DATABASE_FILE,
            'users_count': users_count,
            'malware_hashes_count': malware_hashes_count,
            'scan_history_count': scan_history_count,
            'stripe_configured': bool(STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET),
            'max_scan_files': MAX_SCAN_FILES,
            'cache_size': len(hash_cache),
            'cache_max_size': MAX_CACHE_SIZE
        })
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return jsonify({
            'status': 'unhealthy', 
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/hash/check/cached/<hash_value>', methods=['GET'])
@handle_db_errors
@rate_limit()
def check_hash_cached_endpoint(hash_value):
    """Endpoint pour vérifier un hash avec cache"""
    try:
        # Validation du hash
        if not isinstance(hash_value, str) or len(hash_value) not in [32, 40, 64]:
            return jsonify({'error': 'Format de hash invalide'}), 400
        
        # Vérifier le cache
        if hash_value in hash_cache:
            logger.info(f"Hash {hash_value} servi depuis le cache")
            result = hash_cache[hash_value]
            result['cached'] = True
            return jsonify(result)
        
        # Si pas dans le cache, faire la vérification
        is_malicious, malware_name, risk_level = check_hash(hash_value)
        result = {
            'hash': hash_value,
            'is_malicious': is_malicious,
            'malware_name': malware_name,
            'risk_level': risk_level,
            'cached': False
        }
        
        # Mettre en cache
        hash_cache[hash_value] = result
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du hash (cache): {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

if __name__ == '__main__':
    # Initialiser la base de données
    init_database()
    
    # Vérifier les statistiques initiales
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM users')
    users_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM malware_hashes')
    malware_hashes_count = cursor.fetchone()['count']
    
    conn.close()
    
    logger.info(f"Base de données initialisée: {users_count} utilisateurs, {malware_hashes_count} hashes malveillants")
    
    # Démarrer le serveur
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Démarrage du serveur webhook sur le port {port} (debug: {debug_mode})")
    logger.info(f"Clé Stripe configurée: {bool(STRIPE_SECRET_KEY)}")
    logger.info(f"Secret webhook configuré: {bool(STRIPE_WEBHOOK_SECRET)}")
    logger.info(f"Base de données: {DATABASE_FILE}")
    logger.info(f"Limite de fichiers scannés: {MAX_SCAN_FILES}")
    logger.info(f"Taille max du cache: {MAX_CACHE_SIZE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)