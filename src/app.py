import streamlit as st
import os
import tempfile
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import sqlite3
import requests
import base64
import psutil
import warnings
import shutil
import stripe
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# Charger les variables d'environnement
load_dotenv()

# Import des composants de l'antivirus
from src.antivirus_engine import SamShakkurAntivirus, LanguageManager
from src.database import init_database, get_user_subscription_status, update_user_subscription, add_scan_history, get_scan_history

# Configuration de la page
st.set_page_config(
    page_title="SamShakkurProtection",
    page_icon="🛡️",
    layout="wide"
)

# Configuration
APP_NAME = "SamShakkurProtection"
APP_VERSION = "2.0"
APP_AUTHOR = "Oumar Sampou"

# Configuration Stripe - Chargement depuis les variables d'environnement
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Configuration de la base de données SQLite - Utilisation de la même base que le serveur webhook
DATABASE_FILE = os.getenv('DATABASE_FILE', 'data/users.db')
WEBHOOK_SERVER_URL = os.getenv('WEBHOOK_SERVER_URL', 'http://localhost:5000')

# Vérification de sécurité des clés Stripe
STRIPE_KEYS_CONFIGURED = True
if not stripe.api_key or "test" in stripe.api_key:
    STRIPE_KEYS_CONFIGURED = False
if not STRIPE_PUBLISHABLE_KEY or "test" in STRIPE_PUBLISHABLE_KEY:
    STRIPE_KEYS_CONFIGURED = False

# Comptes de paiement
PAYMENT_ACCOUNTS = {
    "orange_money": "+224 610595955",
    "mobile_money": "+224 661312038", 
    "paycard": "628404816"
}

# Options d'abonnement (cohérentes avec le serveur webhook)
SUBSCRIPTION_PLANS = {
    "monthly": {"price": 5.99, "interval": "month", "name": "Mensuel", "stripe_price_id": "price_monthly_test", "days": 30},
    "yearly": {"price": 59.00, "interval": "year", "name": "Annuel", "saving": "17%", "stripe_price_id": "price_yearly_test", "days": 365},
    "lifetime": {"price": 259.00, "interval": "lifetime", "name": "Accès Permanent", "stripe_price_id": "price_lifetime_test", "days": 3650}
}

# Style CSS avec badges Free/Pro
st.markdown("""
<style>
    .pro-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: black;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    .free-badge {
        background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    .premium-feature {
        background: linear-gradient(135deg, #fffaf0 0%, #fff5e6 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FFD700;
        margin: 10px 0;
    }
    .payment-option {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .payment-option:hover {
        border-color: #3498db;
        background-color: #f8f9fa;
    }
    .payment-option.selected {
        border-color: #27ae60;
        background-color: #e8f5e8;
    }
    .plan-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s;
        margin: 10px 0;
    }
    .plan-card:hover {
        border-color: #3498db;
        transform: translateY(-5px);
    }
    .plan-card.selected {
        border-color: #27ae60;
        background-color: #e8f5e8;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .plan-card h3 {
        margin-top: 0;
    }
    .price {
        font-size: 2rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .saving {
        color: #27ae60;
        font-weight: bold;
    }
    .scan-result-danger {
        background-color: #ffebee;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
        margin: 5px 0;
    }
    .scan-result-safe {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
        margin: 5px 0;
    }
    .scan-result-warning {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
        margin: 5px 0;
    }
    .stripe-element {
        border: 1px solid #ccc;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class AppState:
    """Classe pour gérer l'état de l'application"""
    def __init__(self):
        self.antivirus = None
        self.logged_in = False
        self.user_email = ""
        self.user_subscription = "free"
        self.user_is_premium = False
        
    def initialize(self):
        """Initialise l'application"""
        self.antivirus = SamShakkurAntivirus()
        init_database()
        
    def login(self, email):
        """Connecte un utilisateur"""
        self.user_email = email
        self.logged_in = True
        self.user_subscription, self.user_is_premium = get_user_subscription_status(email)
        self.antivirus.set_user(email)
        
    def logout(self):
        """Déconnecte l'utilisateur"""
        self.logged_in = False
        self.user_email = ""
        self.user_subscription = "free"
        self.user_is_premium = False

def login_section():
    """Section de connexion et d'inscription"""
    st.sidebar.header("🔐 Connexion")
    
    # Initialisation de l'état de session
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
        st.session_state.app_state.initialize()
    
    app_state = st.session_state.app_state
    
    # Si l'utilisateur est déjà connecté
    if app_state.logged_in:
        st.sidebar.success(f"Connecté en tant que: {app_state.user_email}")
        if app_state.user_is_premium:
            st.sidebar.markdown(f"<span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f"<span class='free-badge'>FREE</span>", unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Se déconnecter"):
            app_state.logout()
            st.rerun()
        
        return True
    
    # Formulaire de connexion
    with st.sidebar.form("login_form"):
        email = st.text_input("📧 Email", placeholder="votre@email.com")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
        submitted = st.form_submit_button("🔐 Se connecter / S'inscrire")
        
        if submitted and email:
            # Simulation d'authentification
            app_state.login(email)
            st.rerun()
    
    return app_state.logged_in

def subscription_section():
    """Section d'abonnement et de paiement"""
    st.header("💎 Passer à la version PRO")
    
    app_state = st.session_state.app_state
    
    # Vérifier la connexion
    if not app_state.logged_in:
        st.warning("Veuillez vous connecter pour accéder aux options d'abonnement.")
        return
    
    # Afficher le statut actuel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if app_state.user_is_premium:
            st.success("✅ Vous avez déjà un abonnement PRO actif!")
        else:
            st.info("ℹ️ Version Free active - Fonctionnalités limitées")
    
    with col2:
        if app_state.user_is_premium:
            st.markdown(f"<span class='pro-badge'>COMPTE PRO</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='free-badge'>COMPTE FREE</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Afficher les plans d'abonnement
    st.subheader("📋 Choisissez votre forfait")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.subheader("Mensuel")
            st.markdown(f'<div class="price">${SUBSCRIPTION_PLANS["monthly"]["price"]}</div>', unsafe_allow_html=True)
            st.write("Par mois")
            st.write("✅ Scan complet")
            st.write("✅ Protection temps réel")
            st.write("✅ Mises à jour quotidiennes")
            st.write("✅ Support prioritaire")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("Choisir Mensuel", key="monthly_btn", use_container_width=True):
                st.session_state.selected_plan = "monthly"
                st.session_state.show_payment = True
    
    with col2:
        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.subheader("Annuel")
            st.markdown(f'<div class="price">${SUBSCRIPTION_PLANS["yearly"]["price"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="saving">Économisez 17%</div>', unsafe_allow_html=True)
            st.write("Par an (équivaut à $4.99/mois)")
            st.write("✅ Tout inclus du forfait Mensuel")
            st.write("✅ Analyses cloud avancées")
            st.write("✅ Protection des transactions")
            st.write("✅ Sauvegarde automatique")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("Choisir Annuel", key="yearly_btn", use_container_width=True):
                st.session_state.selected_plan = "yearly"
                st.session_state.show_payment = True
    
    with col3:
        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.subheader("À vie")
            st.markdown(f'<div class="price">${SUBSCRIPTION_PLANS["lifetime"]["price"]}</div>', unsafe_allow_html=True)
            st.write("Paiement unique")
            st.write("✅ Tous les avantages du forfait Annuel")
            st.write("✅ Mises à jour à vie")
            st.write("✅ Support premium 24/7")
            st.write("✅ Licence pour 5 appareils")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("Choisir À vie", key="lifetime_btn", use_container_width=True):
                st.session_state.selected_plan = "lifetime"
                st.session_state.show_payment = True
    
    # Section de paiement
    if st.session_state.get('show_payment', False):
        st.markdown("---")
        st.subheader(f"💳 Paiement - Forfait {SUBSCRIPTION_PLANS[st.session_state.selected_plan]['name']}")
        
        # Options de paiement
        payment_method = st.radio(
            "Méthode de paiement:",
            ["Carte de crédit (Stripe)", "Orange Money", "Mobile Money", "Carte de paiement"],
            horizontal=True
        )
        
        if payment_method == "Carte de crédit (Stripe)":
            if not STRIPE_KEYS_CONFIGURED:
                st.warning("⚠️ Les clés Stripe ne sont pas configurées correctement. Utilisez une autre méthode de paiement.")
            else:
                # Intégration Stripe simplifiée
                st.info("🔒 Paiement sécurisé avec Stripe")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Numéro de carte", placeholder="4242 4242 4242 4242")
                    st.columns(2)[0].text_input("MM/AA", placeholder="12/25")
                    st.columns(2)[1].text_input("CVC", placeholder="123")
                
                with col2:
                    st.text_input("Nom sur la carte", placeholder="John Doe")
                    st.text_input("Pays", value="France")
                
                if st.button("Payer maintenant avec Stripe", type="primary"):
                    # Simulation de paiement réussi
                    success = process_payment(st.session_state.selected_plan)
                    if success:
                        st.success("✅ Paiement réussi! Votre abonnement PRO est maintenant actif.")
                        app_state.user_is_premium = True
                        app_state.user_subscription = st.session_state.selected_plan
                        st.session_state.show_payment = False
                        st.rerun()
                    else:
                        st.error("❌ Échec du paiement. Veuillez réessayer.")
        
        else:
            # Paiement mobile
            st.info(f"📱 Paiement via {payment_method}")
            account_info = PAYMENT_ACCOUNTS.get(
                payment_method.lower().replace(" ", "_"),
                "Information de compte non disponible"
            )
            
            st.write(f"**Numéro de compte:** {account_info}")
            st.write(f"**Montant à payer:** ${SUBSCRIPTION_PLANS[st.session_state.selected_plan]['price']}")
            st.write("**Instructions:** Effectuez le paiement et entrez l'ID de transaction ci-dessous.")
            
            transaction_id = st.text_input("ID de transaction", placeholder="Ex: OM123456789")
            
            if st.button("Confirmer le paiement", type="primary") and transaction_id:
                # Simulation de vérification de paiement
                success = process_mobile_payment(transaction_id, st.session_state.selected_plan)
                if success:
                    st.success("✅ Paiement confirmé! Votre abonnement PRO est maintenant actif.")
                    app_state.user_is_premium = True
                    app_state.user_subscription = st.session_state.selected_plan
                    st.session_state.show_payment = False
                    st.rerun()
                else:
                    st.error("❌ ID de transaction invalide. Veuillez vérifier et réessayer.")
        
        if st.button("Annuler", key="cancel_payment"):
            st.session_state.show_payment = False
            st.rerun()

def process_payment(plan_name):
    """Traite un paiement (simulation)"""
    app_state = st.session_state.app_state
    # En production, intégrer l'API Stripe ici
    time.sleep(2)  # Simulation de traitement
    return update_user_subscription(
        app_state.user_email, 
        plan_name, 
        SUBSCRIPTION_PLANS[plan_name]["days"]
    )

def process_mobile_payment(transaction_id, plan_name):
    """Traite un paiement mobile (simulation)"""
    app_state = st.session_state.app_state
    # Vérification simplifiée de l'ID de transaction
    if transaction_id and len(transaction_id) >= 5:
        time.sleep(2)  # Simulation de traitement
        return update_user_subscription(
            app_state.user_email, 
            plan_name, 
            SUBSCRIPTION_PLANS[plan_name]["days"]
        )
    return False

def render_scan_tab(language_manager):
    """Affiche l'onglet de scan"""
    st.header("🔍 Scan de Sécurité")
    
    app_state = st.session_state.app_state
    
    # Vérifier la connexion au serveur
    if app_state.antivirus.server_connected:
        st.success(language_manager.t('server_connected'))
    else:
        st.warning(language_manager.t('server_disconnected'))
    
    # Configuration du scan
    st.subheader(language_manager.t('scan_config'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_path = st.text_input(
            language_manager.t('target_label'), 
            placeholder="C:\\Windows\\System32" if os.name == 'nt' else "/usr/bin",
            help="Chemin du fichier ou répertoire à analyser"
        )
        
        # Bouton de sélection de fichier
        if st.button(language_manager.t('browse_button')):
            # Dans Streamlit Cloud, on ne peut pas utiliser file_uploader pour les répertoires
            # On utilise donc une approche simplifiée
            st.info("Environnement cloud - Entrez le chemin manuellement")
    
    with col2:
        deep_scan = st.checkbox(language_manager.t('deep_scan'), value=True)
        cloud_scan = st.checkbox(language_manager.t('cloud_scan'), 
                               value=app_state.antivirus.server_connected,
                               disabled=not app_state.antivirus.server_connected)
        auto_quarantine = st.checkbox(language_manager.t('auto_quarantine'), value=False)
    
    # Boutons d'action
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button(language_manager.t('full_scan'), type="primary", use_container_width=True):
            if target_path and os.path.exists(target_path):
                with st.spinner(language_manager.t('scan_complete')):
                    scan_options = {
                        "deep_scan": deep_scan,
                        "cloud_scan": cloud_scan,
                        "auto_quarantine": auto_quarantine
                    }
                    
                    def progress_callback(progress, file_path, result):
                        progress_bar.progress(progress)
                        status_text.text(f"Scan de: {os.path.basename(file_path)}")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success, message = app_state.antivirus.scan_directory(target_path, scan_options, progress_callback)
                    
                    if success:
                        progress_bar.progress(100)
                        status_text.text(language_manager.t('scan_complete'))
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning(language_manager.t('select_target'))
    
    with col2:
        if st.button(language_manager.t('quick_scan'), use_container_width=True):
            if target_path and os.path.exists(target_path):
                with st.spinner(language_manager.t('quick_scan_progress')):
                    # Simulation du scan rapide
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(101):
                        progress_bar.progress(i)
                        status_text.text(language_manager.t('quick_scan_progress'))
                        time.sleep(0.02)
                    
                    status_text.text(language_manager.t('scan_complete'))
                    
                    # Résultats simulés
                    app_state.antivirus.files_scanned = 150
                    app_state.antivirus.threats_detected = 0
                    st.rerun()
            else:
                st.warning(language_manager.t('select_target'))
    
    with col3:
        if st.button(language_manager.t('clean_button'), use_container_width=True):
            if hasattr(app_state.antivirus, 'threats_detected') and app_state.antivirus.threats_detected > 0:
                with st.spinner(language_manager.t('cleaning')):
                    # Mettre en quarantaine les fichiers malveillants
                    quarantined = 0
                    for result in app_state.antivirus.scan_results:
                        if result.get('status') in ['malicious', 'suspicious']:
                            success, _ = app_state.antivirus.quarantine_file(result['file'])
                            if success:
                                quarantined += 1
                    
                    st.success(f"{quarantined} fichiers mis en quarantaine!")
                    app_state.antivirus.threats_detected = 0
                    st.rerun()
            else:
                st.info(language_manager.t('clean_message'))
    
    # Résultats du scan
    st.subheader(language_manager.t('results_title'))
    
    if not hasattr(app_state.antivirus, 'scan_results') or not app_state.antivirus.scan_results:
        st.info(language_manager.t('waiting_scan'))
    else:
        # Résumé du scan
        summary = app_state.antivirus.get_scan_report()
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Fichiers analysés", summary['scanned_files'])
            with col2:
                st.metric("Menaces détectées", summary['threats_detected'])
            with col3:
                st.metric("Durée", f"{summary['duration_seconds']:.2f}s")
            with col4:
                if summary['threats_detected'] > 0:
                    st.error(language_manager.t('status_threats'))
                else:
                    st.success(language_manager.t('status_clean'))
        
        # Détails des résultats
        for result in app_state.antivirus.scan_results:
            if result.get('status') == 'error':
                with st.expander(f"❌ {os.path.basename(result['file'])} - Erreur", expanded=False):
                    st.error(f"Erreur: {result['error']}")
            
            elif result.get('status') == 'clean':
                with st.expander(f"✅ {os.path.basename(result['file'])} - Sain", expanded=False):
                    st.success(language_manager.t('hash_clean'))
                    if 'hash_md5' in result:
                        st.code(f"MD5: {result['hash_md5']}")
                    if 'hash_sha256' in result:
                        st.code(f"SHA256: {result['hash_sha256']}")
            
            elif result.get('status') in ['malicious', 'suspicious']:
                # Déterminer l'icône et la couleur en fonction du niveau de risque
                max_risk = max([t.get('risk', 0) for t in result.get('threats', [])], default=0)
                
                if max_risk >= 7:
                    icon = "🚨"
                    expander_class = "scan-result-danger"
                elif max_risk >= 4:
                    icon = "⚠️"
                    expander_class = "scan-result-warning"
                else:
                    icon = "🔍"
                    expander_class = "scan-result-warning"
                
                with st.expander(f"{icon} {os.path.basename(result['file'])} - Menace", expanded=True):
                    st.markdown(f'<div class="{expander_class}">', unsafe_allow_html=True)
                    
                    for threat in result.get('threats', []):
                        st.write(f"**{threat.get('type', 'Unknown').replace('_', ' ').title()}**")
                        st.write(f"Nom: {threat.get('name', 'Unknown')}")
                        st.write(f"Risque: {threat.get('risk', 0)}/10")
                        st.write(f"Description: {threat.get('description', 'No description')}")
                        st.markdown("---")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Bouton de quarantaine
                    if st.button("Mettre en quarantaine", key=f"quarantine_{result['file']}"):
                        success, message = app_state.antivirus.quarantine_file(result['file'])
                        if success:
                            st.success(language_manager.t('quarantine_success', file_path=result['file']))
                            app_state.antivirus.threats_detected -= len(result.get('threats', []))
                            st.rerun()
                        else:
                            st.error(language_manager.t('quarantine_error', error=message))

def render_protection_tab(language_manager):
    """Affiche l'onglet de protection"""
    st.header("🛡️ Protection en Temps Réel")
    
    app_state = st.session_state.app_state
    
    if not app_state.logged_in:
        st.warning("Veuillez vous connecter pour activer la protection en temps réel.")
        return
    
    # Statut de la protection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Statut de Protection")
        if app_state.user_is_premium:
            st.success("✅ Protection Premium Active")
            st.markdown(f"<span class='pro-badge'>PROTECTION MAXIMALE</span>", unsafe_allow_html=True)
        else:
            st.info("ℹ️ Protection Basique Active")
            st.markdown(f"<span class='free-badge'>PROTECTION ESSENTIELLE</span>", unsafe_allow_html=True)
            st.warning("Passez à la version PRO pour une protection complète")
    
    with col2:
        st.subheader("Statut du Système")
        # Informations système simulées
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        st.metric("Utilisation CPU", f"{cpu_usage}%")
        st.metric("Utilisation Mémoire", f"{memory_usage}%")
        
        if cpu_usage > 80:
            st.warning("⚠️ CPU élevé - Vérifiez les processus")
        if memory_usage > 80:
            st.warning("⚠️ Mémoire élevée - Optimisation recommandée")
    
    st.markdown("---")
    
    # Contrôles de protection
    st.subheader("Paramètres de Protection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Protection en temps réel
        real_time_protection = st.toggle(
            "Protection en temps réel", 
            value=app_state.user_is_premium,
            disabled=not app_state.user_is_premium,
            help="Activez la surveillance en temps réel (PRO uniquement)"
        )
        
        # Analyse comportementale
        behavior_analysis = st.toggle(
            "Analyse comportementale", 
            value=app_state.user_is_premium,
            disabled=not app_state.user_is_premium,
            help="Détecte les comportements suspects (PRO uniquement)"
        )
    
    with col2:
        # Protection web
        web_protection = st.toggle(
            "Protection web", 
            value=app_state.user_is_premium,
            disabled=not app_state.user_is_premium,
            help="Bloque les sites malveillants (PRO uniquement)"
        )
        
        # Protection des emails
        email_protection = st.toggle(
            "Protection email", 
            value=False,
            disabled=True,
            help="Bientôt disponible"
        )
    
    # Fonctionnalités PRO
    if not app_state.user_is_premium:
        st.markdown("---")
        st.subheader("🚀 Fonctionnalités PRO Exclusives")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="premium-feature">', unsafe_allow_html=True)
            st.write("**🔒 Chiffrement Avancé**")
            st.write("Protégez vos fichiers sensibles avec un chiffrement AES-256")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="premium-feature">', unsafe_allow_html=True)
            st.write("🌐 Protection Cloud")
            st.write("Analyses cloud en temps réel avec base de données mondiale")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="premium-feature">', unsafe_allow_html=True)
            st.write("🛡️ Pare-feu Intelligent")
            st.write("Contrôle avancé des connexions réseau entrantes/sortantes")
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("💎 Passer à la version PRO", type="primary"):
            st.session_state.selected_menu = "💎 Abonnement"
            st.rerun()

def render_reports_tab(language_manager):
    """Affiche l'onglet des rapports"""
    st.header("📊 Rapports et Historique")
    
    app_state = st.session_state.app_state
    
    if not app_state.logged_in:
        st.warning("Veuillez vous connecter pour accéder à vos rapports.")
        return
    
    # Statistiques personnelles
    st.subheader("📈 Vos Statistiques de Sécurité")
    
    # Récupérer l'historique des scans
    scan_history = get_scan_history(app_state.user_email)
    
    if scan_history:
        # Calculer les statistiques
        total_scans = len(scan_history)
        total_files = sum(scan['files_scanned'] for scan in scan_history)
        total_threats = sum(scan['threats_detected'] for scan in scan_history)
        avg_duration = sum(scan['duration_seconds'] for scan in scan_history) / total_scans if total_scans > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Scans effectués", total_scans)
        col2.metric("Fichiers analysés", total_files)
        col3.metric("Menaces bloquées", total_threats)
        col4.metric("Durée moyenne", f"{avg_duration:.2f}s")
        
        # Graphique de l'historique des menaces
        st.subheader("📊 Évolution des Menaces")
        
        # Préparer les données pour le graphique
        dates = [datetime.strptime(scan['scan_date'], '%Y-%m-%d %H:%M:%S') if isinstance(scan['scan_date'], str) else scan['scan_date'] for scan in scan_history]
        threats = [scan['threats_detected'] for scan in scan_history]
        
        # Créer un DataFrame pour le graphique
        df = pd.DataFrame({
            'Date': dates,
            'Menaces': threats
        })
        
        # Grouper par mois
        df['Mois'] = df['Date'].dt.to_period('M')
        monthly_data = df.groupby('Mois')['Menaces'].sum().reset_index()
        monthly_data['Mois'] = monthly_data['Mois'].astype(str)
        
        # Afficher le graphique
        st.bar_chart(monthly_data.set_index('Mois'))
        
        # Détails de l'historique
        st.subheader("📋 Détail des Scans")
        
        for scan in scan_history[:10]:  # Afficher les 10 derniers scans
            with st.expander(f"Scan du {scan['scan_date']} - {scan['target_path']}", expanded=False):
                col1, col2 = st.columns(2)
                col1.write(f"**Type:** {scan['scan_type']}")
                col2.write(f"**Fichiers:** {scan['files_scanned']}")
                col1.write(f"**Menaces:** {scan['threats_detected']}")
                col2.write(f"**Durée:** {scan['duration_seconds']:.2f}s")
    else:
        st.info("📝 Aucun scan enregistré. Effectuez votre premier scan pour voir les statistiques ici.")
    
    # Section de gestion de base de données (admin)
    if app_state.user_email == "admin@samshakkur.com":
        st.markdown("---")
        st.subheader("⚙️ Gestion de Base de Données (Admin)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Mettre à jour la base de signatures"):
                with st.spinner(language_manager.t('db_update')):
                    # Simulation de mise à jour
                    time.sleep(2)
                    st.success(language_manager.t('db_updated'))
        
        with col2:
            if st.button("📊 Statistiques de la base"):
                from src.database import get_db_connection
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Compter les signatures
                    cursor.execute("SELECT COUNT(*) FROM malware_hashes")
                    hash_count = cursor.fetchone()[0]
                    
                    # Compter les utilisateurs
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    st.info(f"Signatures: {hash_count} | Utilisateurs: {user_count}")

def main():
    # Initialiser la base de données
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
        st.session_state.app_state.initialize()
    
    app_state = st.session_state.app_state
    language_manager = app_state.antivirus.language_manager
    
    # Barre latérale avec connexion
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/3498db/ffffff?text=SamShakkur", width=150)
        st.markdown(f"### {APP_NAME} v{APP_VERSION}")
        
        # Sélecteur de langue
        lang_option = st.selectbox(
            "🌐 Langue",
            options=language_manager.get_available_languages(),
            format_func=lambda x: {
                'fr': 'Français', 
                'en': 'English', 
                'es': 'Español', 
                'de': 'Deutsch',
                'ar': 'العربية'
            }[x]
        )
        language_manager.set_language(lang_option)
        
        # Connexion utilisateur
        login_section()
        
        # Navigation
        st.markdown("---")
        st.subheader("📁 Navigation")
        
        if not app_state.logged_in:
            st.info("Connectez-vous pour accéder à toutes les fonctionnalités")
        
        # Menu de navigation
        menu_options = [
            language_manager.t('scan_tab'),
            language_manager.t('protection_tab'), 
            language_manager.t('reports_tab'),
            "💎 Abonnement"
        ]
        
        selected_menu = st.radio("Aller à:", menu_options)
    
    # Contenu principal en fonction de la sélection du menu
    if selected_menu == language_manager.t('scan_tab'):
        render_scan_tab(language_manager)
    elif selected_menu == language_manager.t('protection_tab'):
        render_protection_tab(language_manager)
    elif selected_menu == language_manager.t('reports_tab'):
        render_reports_tab(language_manager)
    elif selected_menu == "💎 Abonnement":
        subscription_section()
    
    # Pied de page
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"*{language_manager.t('created_by')}*")
    st.sidebar.caption(f"© 2024 {APP_NAME}. Tous droits réservés.")

if __name__ == "__main__":
    main()