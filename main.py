import sys
import os
import subprocess
from threading import Thread
import time

def start_webhook_server():
    """Démarre le serveur webhook en arrière-plan"""
    os.chdir('src')
    subprocess.run([sys.executable, 'webhook_server.py'])

def start_streamlit_app():
    """Démarre l'application Streamlit"""
    os.chdir('src')
    subprocess.run(['streamlit', 'run', 'app.py', '--server.port', '8501', '--server.address', 'localhost'])

if __name__ == "__main__":
    # Démarrer le serveur webhook dans un thread séparé
    webhook_thread = Thread(target=start_webhook_server)
    webhook_thread.daemon = True
    webhook_thread.start()
    
    # Attendre que le serveur webhook soit prêt
    time.sleep(3)
    
    # Démarrer l'application Streamlit
    start_streamlit_app()