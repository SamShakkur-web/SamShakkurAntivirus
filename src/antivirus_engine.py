import os
import tempfile
import hashlib
import time
import shutil
import psutil
from datetime import datetime
import requests
from src.database import check_hash, add_scan_history

class LanguageManager:
    """Gestionnaire de langues pour l'interface multilingue"""
    
    def __init__(self, app_name="SamShakkurProtection", app_version="2.0"):
        self.app_name = app_name
        self.app_version = app_version
        self.languages = {
            'fr': self._french_translations(),
            'en': self._english_translations(),
            'es': self._spanish_translations(),
            'de': self._german_translations(),
            'ar': self._arabic_translations()
        }
        self.current_lang = 'fr'  # Langue par défaut
    
    def set_language(self, lang_code):
        """Définit la langue courante"""
        if lang_code in self.languages:
            self.current_lang = lang_code
            return True
        return False
    
    def get_available_languages(self):
        """Retourne les langues disponibles"""
        return list(self.languages.keys())
    
    def t(self, key, **kwargs):
        """Traduit une clé dans la langue courante"""
        try:
            translation = self.languages[self.current_lang].get(key, key)
            if kwargs:
                return translation.format(**kwargs)
            return translation
        except:
            return key
    
    def _french_translations(self):
        """Traductions françaises"""
        return {
            'app_title': f"{self.app_name} v{self.app_version} - Protection Avancée",
            'scan_tab': "🔍 Scan",
            'protection_tab': "🛡️ Protection",
            'reports_tab': "📊 Rapports",
            'status_ready': "🟢 Prêt - Système sécurisé",
            'protection_active': "🛡️ Protection active",
            'created_by': "Créé par Oumar Sampou",
            'scan_config': " Configuration du Scan ",
            'target_label': "Cible:",
            'browse_button': "Parcourir",
            'deep_scan': "Scan profond",
            'cloud_scan': "Scan cloud",
            'auto_quarantine': "Quarantaine auto",
            'full_scan': "🚀 Scan Complet",
            'quick_scan': "⚡ Scan Rapide",
            'clean_button': "🧹 Nettoyer",
            'results_title': " Résultats en Temps Réel ",
            'waiting_scan': "📊 En attente de scan...",
            'scan_complete': "🔍 Scan complet en cours...",
            'quick_scan_progress': "⚡ Scan rapide en cours...",
            'cleaning': "🧹 Nettoyage en cours...",
            'error': "Erreur",
            'select_target': "Sélectionnez une cible",
            'invalid_target': "❌ Cible invalide",
            'scan_report': "📋 RAPPORT DE SCAN - {app_name}",
            'target': "Cible: {target}",
            'date': "Date: {date}",
            'threats_detected': "🚨 MENACES DÉTECTÉES - Action recommandée!",
            'no_threats': "✅ Aucune menace détectée - Système sécurisé",
            'clean_activated': "Nettoyage",
            'clean_message': "Fonctionnalité de nettoyage avancée activée!",
            'status_threats': "📊 Statut: Menaces détectées!",
            'status_clean': "📊 Statut: Aucune menace",
            'hash_clean': "Hash propre",
            'hash_error': "Erreur hash",
            'hash_malware': "Hash connu: {malware_info}",
            'ai_normal': "IA: Comportement normal",
            'ai_suspicious': "IA: Comportement suspect (score: {score:.2f})",
            'ai_unavailable': "IA: Analyse non disponible",
            'heuristic_normal': "Heuristique: Normal",
            'heuristic_suspicious': "Heuristique: {reasons} (score: {score:.2f})",
            'heuristic_error': "Heuristique: Erreur - {error}",
            'cloud_unavailable': "Cloud: Service non disponible",
            'cloud_error': "Cloud: Erreur connexion",
            'cloud_no_detection': "Cloud: Aucune détection",
            'cloud_detection': "Cloud: {count} moteurs détectent",
            'memory_clean': "Memory: Aucune injection détectée",
            'memory_unavailable': "Memory: Analyse non disponible",
            'high_memory': "Mémoire élevée",
            'network_connections': "Connexions réseau excessivas",
            'real_time_active': "🛡️  Protection temps réel activée",
            'suspicious_process': "🚨 Processus suspect {process_name}: {behaviors}",
            'db_update': "📦 Mise à jour de la base de données...",
            'db_updated': "✅ Base de données à jour",
            'quarantine_success': "Fichier mis en quarantaine: {file_path}",
            'quarantine_error': "Erreur quarantaine: {error}",
            'payment_success': "✅ Paiement réussi! Votre abonnement est activé.",
            'payment_failed': "❌ Échec du paiement. Veuillez réessayer.",
            'payment_processing': "⏳ Traitement du paiement en cours...",
            'server_connected': "✅ Connecté au serveur de sécurité",
            'server_disconnected': "⚠️ Serveur de sécurité hors ligne - Mode local uniquement",
        }
    
    def _english_translations(self):
        """English translations"""
        return {
            'app_title': f"{self.app_name} v{self.app_version} - Advanced Protection",
            'scan_tab': "🔍 Scan",
            'protection_tab': "🛡️ Protection",
            'reports_tab': "📊 Reports",
            'status_ready': "🟢 Ready - System secured",
            'protection_active': "🛡️ Protection active",
            'created_by': "Created by Oumar Sampou",
            'scan_config': " Scan Configuration ",
            'target_label': "Target:",
            'browse_button': "Browse",
            'deep_scan': "Deep scan",
            'cloud_scan': "Cloud scan",
            'auto_quarantine': "Auto quarantine",
            'full_scan': "🚀 Full Scan",
            'quick_scan': "⚡ Quick Scan",
            'clean_button': "🧹 Clean",
            'results_title': " Real-Time Results ",
            'waiting_scan': "📊 Waiting for scan...",
            'scan_complete': "🔍 Full scan in progress...",
            'quick_scan_progress': "⚡ Quick scan in progress...",
            'cleaning': "🧹 Cleaning in progress...",
            'error': "Error",
            'select_target': "Select a target",
            'invalid_target': "❌ Invalid target",
            'scan_report': "📋 SCAN REPORT - {app_name}",
            'target': "Target: {target}",
            'date': "Date: {date}",
            'threats_detected': "🚨 THREATS DETECTED - Action required!",
            'no_threats': "✅ No threats detected - System secure",
            'clean_activated': "Cleaning",
            'clean_message': "Advanced cleaning feature activated!",
            'status_threats': "📊 Status: Threats detected!",
            'status_clean': "📊 Status: No threats",
            'hash_clean': "Clean hash",
            'hash_error': "Hash error",
            'hash_malware': "Known hash: {malware_info}",
            'ai_normal': "AI: Normal behavior",
            'ai_suspicious': "AI: Suspicious behavior (score: {score:.2f})",
            'ai_unavailable': "AI: Analysis unavailable",
            'heuristic_normal': "Heuristic: Normal",
            'heuristic_suspicious': "Heuristic: {reasons} (score: {score:.2f})",
            'heuristic_error': "Heuristic: Error - {error}",
            'cloud_unavailable': "Cloud: Service unavailable",
            'cloud_error': "Cloud: Connection error",
            'cloud_no_detection': "Cloud: No detection",
            'cloud_detection': "Cloud: {count} engines detect",
            'memory_clean': "Memory: No injection detected",
            'memory_unavailable': "Memory: Analysis unavailable",
            'high_memory': "High memory usage",
            'network_connections': "Excessive network connections",
            'real_time_active': "🛡️ Real-time protection activated",
            'suspicious_process': "🚨 Suspicious process {process_name}: {behaviors}",
            'db_update': "📦 Updating database...",
            'db_updated': "✅ Database updated",
            'quarantine_success': "File quarantined: {file_path}",
            'quarantine_error': "Quarantine error: {error}",
            'payment_success': "✅ Payment successful! Your subscription is activated.",
            'payment_failed': "❌ Payment failed. Please try again.",
            'payment_processing': "⏳ Processing payment...",
            'server_connected': "✅ Connected to security server",
            'server_disconnected': "⚠️ Security server offline - Local mode only",
        }
    
    def _spanish_translations(self):
        """Traducciones al español"""
        return {
            'app_title': f"{self.app_name} v{self.app_version} - Protección Avanzada",
            'scan_tab': "🔍 Escanear",
            'protection_tab': "🛡️ Protección",
            'reports_tab': "📊 Informes",
            'status_ready': "🟢 Listo - Sistema seguro",
            'protection_active': "🛡️ Protección activa",
            'created_by': "Creado por Oumar Sampou",
            'scan_config': " Configuración de Escaneo ",
            'target_label': "Objetivo:",
            'browse_button': "Examinar",
            'deep_scan': "Escaneo profundo",
            'cloud_scan': "Escaneo en la nube",
            'auto_quarantine': "Cuarentena automática",
            'full_scan': "🚀 Escaneo Completo",
            'quick_scan': "⚡ Escaneo Rápido",
            'clean_button': "🧹 Limpiar",
            'results_title': " Resultados en Tiempo Real ",
            'waiting_scan': "📊 Esperando escaneo...",
            'scan_complete': "🔍 Escaneo completo en progreso...",
            'quick_scan_progress': "⚡ Escaneo rápido en progreso...",
            'cleaning': "🧹 Limpieza en progreso...",
            'error': "Error",
            'select_target': "Seleccione un objetivo",
            'invalid_target': "❌ Objetivo inválido",
            'scan_report': "📋 INFORME DE ESCANEO - {app_name}",
            'target': "Objetivo: {target}",
            'date': "Fecha: {date}",
            'threats_detected': "🚨 AMENAZAS DETECTADAS - ¡Acción requerida!",
            'no_threats': "✅ No se detectaron amenazas - Sistema seguro",
            'clean_activated': "Limpieza",
            'clean_message': "¡Función de limpieza avanzada activada!",
            'status_threats': "📊 Estado: ¡Amenazas detectadas!",
            'status_clean': "📊 Estado: Sin amenazas",
            'hash_clean': "Hash limpio",
            'hash_error': "Error de hash",
            'hash_malware': "Hash conocido: {malware_info}",
            'ai_normal': "IA: Comportamiento normal",
            'ai_suspicious': "IA: Comportamiento sospechoso (puntuación: {score:.2f})",
            'ai_unavailable': "IA: Análisis no disponible",
            'heuristic_normal': "Heurística: Normal",
            'heuristic_suspicious': "Heurística: {reasons} (puntuación: {score:.2f})",
            'heuristic_error': "Heurística: Error - {error}",
            'cloud_unavailable': "Nube: Servicio no disponible",
            'cloud_error': "Nube: Error de conexión",
            'cloud_no_detection': "Nube: Sin detección",
            'cloud_detection': "Nube: {count} motores detectan",
            'memory_clean': "Memoria: No se detectó inyección",
            'memory_unavailable': "Memoria: Análisis no disponible",
            'high_memory': "Uso elevado de memoria",
            'network_connections': "Conexiones de red excesivas",
            'real_time_active': "🛡️ Protección en tiempo real activada",
            'suspicious_process': "🚨 Proceso sospechoso {process_name}: {behaviors}",
            'db_update': "📦 Actualizando base de datos...",
            'db_updated': "✅ Base de datos actualizada",
            'quarantine_success': "Archivo en cuantena: {file_path}",
            'quarantine_error': "Error de cuarentena: {error}",
            'payment_success': "✅ ¡Pago exitoso! Su suscripción está activada.",
            'payment_failed': "❌ Pago fallido. Por favor, intente nuevamente.",
            'payment_processing': "⏳ Procesando pago...",
            'server_connected': "✅ Conectado al servidor de seguridad",
            'server_disconnected': "⚠️ Servidor de seguridad fuera de línea - Solo modo local",
        }
    
    def _german_translations(self):
        """Deutsche Übersetzungen"""
        return {
            'app_title': f"{self.app_name} v{self.app_version} - Erweiterter Schutz",
            'scan_tab': "🔍 Scan",
            'protection_tab': "🛡️ Schutz",
            'reports_tab': "📊 Berichte",
            'status_ready': "🟢 Bereit - System gesichert",
            'protection_active': "🛡️ Schutz aktiv",
            'created_by': "Erstellt von Oumar Sampou",
            'scan_config': " Scan-Konfiguration ",
            'target_label': "Ziel:",
            'browse_button': "Durchsuchen",
            'deep_scan': "Tiefenscan",
            'cloud_scan': "Cloud-Scan",
            'auto_quarantine': "Auto-Quarantäne",
            'full_scan': "🚀 Vollständiger Scan",
            'quick_scan': "⚡ Schneller Scan",
            'clean_button': "🧹 Bereinigen",
            'results_title': " Echtzeit-Ergebnisse ",
            'waiting_scan': "📊 Warte auf Scan...",
            'scan_complete': "🔍 Vollständiger Scan läuft...",
            'quick_scan_progress': "⚡ Schneller Scan läuft...",
            'cleaning': "🧹 Bereinigung läuft...",
            'error': "Fehler",
            'select_target': "Wählen Sie ein Ziel",
            'invalid_target': "❌ Ungültiges Ziel",
            'scan_report': "📋 SCAN-BERICHT - {app_name}",
            'target': "Ziel: {target}",
            'date': "Datum: {date}",
            'threats_detected': "🚨 BEDROHUNGEN ERKANNT - Aktion erforderlich!",
            'no_threats': "✅ Keine Bedrohungen erkannt - System sicher",
            'clean_activated': "Bereinigung",
            'clean_message': "Erweiterte Bereinigungsfunktion activiert!",
            'status_threats': "📊 Status: Bedrohungen erkannt!",
            'status_clean': "📊 Status: Keine Bedrohungen",
            'hash_clean': "Sauberer Hash",
            'hash_error': "Hash-Fehler",
            'hash_malware': "Bekannter Hash: {malware_info}",
            'ai_normal': "KI: Normales Verhalten",
            'ai_suspicious': "KI: Verdächtiges Verhalten (Score: {score:.2f})",
            'ai_unavailable': "KI: Analyse nicht verfügbar",
            'heuristic_normal': "Heuristik: Normal",
            'heuristic_suspicious': "Heuristik: {reasons} (Score: {score:.2f})",
            'heuristic_error': "Heuristik: Fehler - {error}",
            'cloud_unavailable': "Cloud: Dienst nicht verfügbar",
            'cloud_error': "Cloud: Verbindungsfehler",
            'cloud_no_detection': "Cloud: Keine Erkennung",
            'cloud_detection': "Cloud: {count} Engines erkennen",
            'memory_clean': "Speicher: Keine Injektion erkannt",
            'memory_unavailable': "Speicher: Análisis nicht verfügbar",
            'high_memory': "Hohe Speichernutzung",
            'network_connections': "Übermäßige Netzwerkverbindungen",
            'real_time_active': "🛡️ Echtzeit-Schutz aktiviert",
            'suspicious_process': "🚨 Verdächtiger Prozess {process_name}: {behaviors}",
            'db_update': "📦 Aktualisiere Datenbank...",
            'db_updated': "✅ Datenbank aktualisiert",
            'quarantine_success': "Datei unter Quarantäne: {file_path}",
            'quarantine_error': "Quarantäne-Fehler: {error}",
            'payment_success': "✅ Zahlung erfolgreich! Ihr Abonnement ist aktiviert.",
            'payment_failed': "❌ Zahlung fehlgeschlagen. Bitte versuchen Sie es erneut.",
            'payment_processing': "⏳ Zahlung wird verarbeitet...",
            'server_connected': "✅ Mit Sicherheitsserver verbunden",
            'server_disconnected': "⚠️ Sicherheitsserver offline - Nur lokaler Modus",
        }
    
    def _arabic_translations(self):
        """الترجمات العربية"""
        return {
            'app_title': f"{self.app_name} v{self.app_version} - حماية متقدمة",
            'scan_tab': "🔍 فحص",
            'protection_tab': "🛡️ حماية",
            'reports_tab': "📊 تقارير",
            'status_ready': "🟢 جاهز - النظام آمن",
            'protection_active': "🛡️ حماية نشطة",
            'created_by': "تم إنشاؤه بواسطة عمر سامبو",
            'scan_config': " إعدادات الفحص ",
            'target_label': "الهدف:",
            'browse_button': "تصفح",
            'deep_scan': "فحص عميق",
            'cloud_scan': "فحص سحابي",
            'auto_quarantine': "حجر صحي تلقائي",
            'full_scan': "🚀 فحص كامل",
            'quick_scan': "⚡ فحص سريع",
            'clean_button': "🧹 تنظيف",
            'results_title': " النتائج في الوقت الحقيقي ",
            'waiting_scan': "📊 في انتظار الفحص...",
            'scan_complete': "🔍 فحص كامل قيد التقدم...",
            'quick_scan_progress': "⚡ فحص سريع قيد التقدم...",
            'cleaning': "🧹 تنظيف قيد التقدم...",
            'error': "خطأ",
            'select_target': "حدد هدفًا",
            'invalid_target': "❌ هدف غير صالح",
            'scan_report': "📋 تقرير الفحص - {app_name}",
            'target': "الهدف: {target}",
            'date': "التاريخ: {date}",
            'threats_detected': "🚨 تم اكتشاف تهديدات - إجراء مطلوب!",
            'no_threats': "✅ لم يتم اكتشاف أي تهديدات - النظام آمن",
            'clean_activated': "تنظيف",
            'clean_message': "تم تفعيل ميزة التنظيف المتقدمة!",
            'status_threats': "📊 الحالة: تم اكتشاف تهديدات!",
            'status_clean': "📊 الحالة: لا توجد تهديدات",
            'hash_clean': "تجزئة نظيفة",
            'hash_error': "خطأ في التجزئة",
            'hash_malware': "تجزئة معروفة: {malware_info}",
            'ai_normal': "الذكاء الاصطناعي: سلوك طبيعي",
            'ai_suspicious': "الذكاء الاصطناعي: سلوك مريب (النتيجة: {score:.2f})",
            'ai_unavailable': "الذكاء الاصطناعي: التحليل غير متاح",
            'heuristic_normal': "استدلالي: طبيعي",
            'heuristic_suspicious': "استدلالي: {reasons} (النتيجة: {score:.2f})",
            'heuristic_error': "استدلالي: خطأ - {error}",
            'cloud_unavailable': "السحابة: الخدمة غير متاحة",
            'cloud_error': "السحابة: خطأ في الاتصال",
            'cloud_no_detection': "السحابة: لا يوجد اكتشاف",
            'cloud_detection': "السحابة: {count} محرك اكتشف",
            'memory_clean': "الذاكرة: لم يتم اكتشاف حقن",
            'memory_unavailable': "الذاكرة: التحليل غير متاح",
            'high_memory': "استخدام ذاكرة مرتفع",
            'network_connections': "اتصالات شبكة مفرطة",
            'real_time_active': "🛡️ تم تفعيل الحماية في الوقت الحقيقي",
            'suspicious_process': "🚨 عملية مريبة {process_name}: {behaviors}",
            'db_update': "📦 تحديث قاعدة البيانات...",
            'db_updated': "✅ تم تحديث قاعدة البيانات",
            'quarantine_success': "تم حجر الملف: {file_path}",
            'quarantine_error': "خطأ في الحجر الصحي: {error}",
            'payment_success': "✅ تم الدفع بنجاح! تم تفعيل اشتراكك.",
            'payment_failed': "❌ فشل الدفع. يرجى المحاولة مرة أخرى.",
            'payment_processing': "⏳ معالجة الدفع...",
            'server_connected': "✅ متصل بخادم الأمان",
            'server_disconnected': "⚠️ خادم الأمان غير متصل - الوضع المحلي فقط",
        }

class SamShakkurAntivirus:
    """Classe principale de l'antivirus"""
    
    def __init__(self):
        self.language_manager = LanguageManager()
        self.scan_results = []
        self.threats_detected = 0
        self.files_scanned = 0
        self.scan_start_time = None
        self.scan_end_time = None
        self.current_user = None
        self.user_subscription = 'free'
        self.is_premium = False
        self.server_connected = False
        self.server_status = {}
    
    def set_user(self, email):
        """Définit l'utilisateur courant et récupère son statut d'abonnement"""
        self.current_user = email
        self.user_subscription, self.is_premium = get_user_subscription_status(email)
    
    def calculate_file_hash(self, file_path, algorithm="md5"):
        """Calcule le hash d'un fichier"""
        try:
            hash_func = hashlib.new(algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            return None
    
    def analyze_file_behavior(self, file_path):
        """Analyse le comportement d'un fichier (simulé)"""
        try:
            # Simulation d'analyse comportementale
            file_size = os.path.getsize(file_path)
            score = 0.0
            reasons = []
            
            # Règles heuristiques simples
            if file_size > 50 * 1024 * 1024:  # Fichiers > 50MB
                score += 0.2
                reasons.append("Fichier volumineux")
            
            if file_path.lower().endswith(('.exe', '.dll', '.bat', '.cmd', '.ps1')):
                score += 0.3
                reasons.append("Fichier exécutable")
            
            # Vérification des noms suspects
            suspicious_keywords = ['virus', 'malware', 'trojan', 'worm', 'keylogger', 'ransom', 'hack', 'crack']
            filename = os.path.basename(file_path).lower()
            for keyword in suspicious_keywords:
                if keyword in filename:
                    score += 0.5
                    reasons.append(f"Nom suspect: {keyword}")
                    break
            
            return {
                "score": min(score, 1.0),
                "reasons": reasons,
                "suspicious": score > 0.5
            }
        except Exception as e:
            return {
                "score": 0.0,
                "reasons": [f"Erreur d'analyse: {str(e)}"],
                "suspicious": False,
                "error": str(e)
            }
    
    def check_cloud_reputation(self, hash_value):
        """Vérifie la réputation d'un hash via le cloud (simulé)"""
        try:
            # Simulation de vérification cloud
            if not self.server_connected:
                return {"detections": 0, "engines": 65, "error": "Serveur non connecté"}
            
            # Vérifier d'abord localement
            is_malicious, malware_name, risk_level = check_hash(hash_value)
            if is_malicious:
                return {"detections": risk_level * 10, "engines": 65, "result": malware_name}
            
            # Simulation aléatoire pour la démo
            import random
            detections = random.randint(0, 5)
            return {"detections": detections, "engines": 65, "result": "Clean" if detections == 0 else "Suspicious"}
            
        except Exception as e:
            return {"detections": 0, "engines": 65, "error": str(e)}
    
    def scan_file(self, file_path, scan_options):
        """Scan un fichier unique et retourne les résultats"""
        result = {
            "file": file_path,
            "hash_md5": self.calculate_file_hash(file_path, "md5"),
            "hash_sha1": self.calculate_file_hash(file_path, "sha1"),
            "hash_sha256": self.calculate_file_hash(file_path, "sha256"),
            "malware_detected": False,
            "malware_info": None,
            "risk_level": 0,
            "behavior_analysis": None,
            "cloud_reputation": None,
            "heuristic_analysis": None
        }
        
        # Vérification par hash
        if result["hash_md5"]:
            is_malicious, malware_name, risk_level = check_hash(result["hash_md5"])
            if is_malicious:
                result["malware_detected"] = True
                result["malware_info"] = malware_name
                result["risk_level"] = risk_level
        
        # Analyse comportementale (si option activée ou si premium)
        if scan_options.get("deep_scan", False) or self.is_premium:
            result["behavior_analysis"] = self.analyze_file_behavior(file_path)
            if result["behavior_analysis"]["suspicious"]:
                result["malware_detected"] = True
                result["risk_level"] = max(result["risk_level"], int(result["behavior_analysis"]["score"] * 10))
                result["malware_info"] = result["malware_info"] or "Comportement suspect détecté"
        
        # Vérification cloud (si option activée)
        if scan_options.get("cloud_scan", False) and result["hash_md5"]:
            result["cloud_reputation"] = self.check_cloud_reputation(result["hash_md5"])
            if result["cloud_reputation"].get("detections", 0) > 10:
                result["malware_detected"] = True
                result["risk_level"] = max(result["risk_level"], 8)
                result["malware_info"] = result["malware_info"] or f"Détecté par {result['cloud_reputation']['detections']} moteurs"
        
        return result
    
    def scan_directory(self, target_path, scan_options, progress_callback=None):
        """Scan un répertoire entier"""
        self.scan_results = []
        self.threats_detected = 0
        self.files_scanned = 0
        self.scan_start_time = datetime.now()
        
        try:
            # Vérifier que le chemin existe
            if not os.path.exists(target_path):
                return False, f"Le chemin {target_path} n'existe pas"
            
            # Compter les fichiers pour la progression
            total_files = 0
            for root, dirs, files in os.walk(target_path):
                total_files += len(files)
            
            scanned_files = 0
            
            # Parcourir tous les fichiers
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Scanner le fichier
                        result = self.scan_file(file_path, scan_options)
                        self.scan_results.append(result)
                        self.files_scanned += 1
                        
                        if result["malware_detected"]:
                            self.threats_detected += 1
                        
                        # Mettre à jour la progression
                        scanned_files += 1
                        if progress_callback:
                            progress = int((scanned_files / total_files) * 100) if total_files > 0 else 100
                            progress_callback(progress, file_path, result)
                            
                    except Exception as e:
                        # En cas d'erreur sur un fichier, continuer avec les autres
                        error_result = {
                            "file": file_path,
                            "error": str(e),
                            "malware_detected": False
                        }
                        self.scan_results.append(error_result)
                        self.files_scanned += 1
            
            self.scan_end_time = datetime.now()
            
            # Enregistrer dans l'historique
            if self.current_user:
                duration = (self.scan_end_time - self.scan_start_time).total_seconds()
                add_scan_history(
                    self.current_user, 
                    target_path, 
                    "full" if scan_options.get("deep_scan") else "quick",
                    self.files_scanned,
                    self.threats_detected,
                    duration
                )
            
            return True, f"Scan terminé: {self.files_scanned} fichiers analysés, {self.threats_detected} menaces détectées"
            
        except Exception as e:
            return False, f"Erreur lors du scan: {str(e)}"
    
    def quarantine_file(self, file_path):
        """Met un fichier en quarantaine"""
        try:
            # Créer le répertoire de quarantaine s'il n'existe pas
            quarantine_dir = os.path.join(tempfile.gettempdir(), "antivirus_quarantine")
            os.makedirs(quarantine_dir, exist_ok=True)
            
            # Générer un nom de fichier unique pour la quarantaine
            filename = os.path.basename(file_path)
            quarantine_path = os.path.join(quarantine_dir, f"quarantine_{int(time.time())}_{filename}")
            
            # Déplacer le fichier
            shutil.move(file_path, quarantine_path)
            
            return True, quarantine_path
        except Exception as e:
            return False, str(e)
    
    def get_scan_report(self):
        """Génère un rapport de scan"""
        if not self.scan_start_time or not self.scan_end_time:
            return None
        
        duration = (self.scan_end_time - self.scan_start_time).total_seconds()
        
        return {
            "scanned_files": self.files_scanned,
            "threats_detected": self.threats_detected,
            "start_time": self.scan_start_time,
            "end_time": self.scan_end_time,
            "duration_seconds": duration,
            "results": self.scan_results
        }
    
    def cleanup_system(self):
        """Nettoie le système des fichiers détectés comme malveillants"""
        cleaned_files = 0
        errors = 0
        
        for result in self.scan_results:
            if result.get("malware_detected", False):
                success, message = self.quarantine_file(result["file"])
                if success:
                    cleaned_files += 1
                else:
                    errors += 1
        
        return cleaned_files, errors




