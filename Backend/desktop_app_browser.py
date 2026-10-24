# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
Application de bureau MARIHAR - Version Navigateur.
Utilise le navigateur par défaut au lieu de PyWebView.
Compatible avec toutes les versions de Python.
"""
import os
import sys
import threading
import time
import webbrowser
from app import app


def get_resource_path(relative_path):
    """
    Obtient le chemin absolu des ressources.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


def start_flask_app():
    """
    Démarre le serveur Flask en arrière-plan.
    """
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False
    )


def open_browser():
    """
    Ouvre le navigateur par défaut après un délai.
    """
    time.sleep(2)  # Attendre que Flask démarre
    webbrowser.open('http://127.0.0.1:5000')


def main():
    """
    Fonction principale.
    """
    print("=" * 60)
    print("  MARIHAR - Téléchargeur de Vidéos")
    print("=" * 60)
    print()
    print("[INFO] Démarrage du serveur Flask...")
    print("[INFO] Le navigateur va s'ouvrir automatiquement...")
    print()
    print("=" * 60)
    print("  URL: http://127.0.0.1:5000")
    print("  Appuyez sur CTRL+C pour arrêter le serveur")
    print("=" * 60)
    print()
    
    # Ouvrir le navigateur dans un thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Démarrer Flask (bloque le thread principal)
    try:
        start_flask_app()
    except KeyboardInterrupt:
        print("\n[INFO] Serveur arrêté.")
        sys.exit(0)


if __name__ == '__main__':
    main()
