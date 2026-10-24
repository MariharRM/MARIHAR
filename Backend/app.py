# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
Application Flask pour l'interface web yt-dlp.
Compatible avec le mode desktop PyWebView.
"""
import os
import sys
import subprocess
import json
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
from ytdlp_service import YTDLPService, HistoryManager


def get_resource_path(relative_path):
    """
    Obtient le chemin absolu des ressources, fonctionne pour le développement et PyInstaller.
    Cherche d'abord dans le dossier d'installation principal, puis dans _MEIPASS.
    """
    # D'abord, essayer le dossier d'installation principal (au-dessus de _internal)
    try:
        # En mode PyInstaller, sys._MEIPASS pointe vers _internal
        # Le dossier d'installation principal est un niveau au-dessus
        if hasattr(sys, '_MEIPASS'):
            install_dir = os.path.dirname(sys._MEIPASS)
            candidate_path = os.path.join(install_dir, relative_path)
            if os.path.exists(candidate_path):
                return candidate_path
    except Exception:
        pass

    # Ensuite, essayer le chemin normal (développement ou _MEIPASS)
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


# Configuration de l'application Flask
def create_app():
    """Factory function pour créer l'application Flask."""
    app = Flask(
        __name__,
        template_folder=get_resource_path('Frontend/templates'),
        static_folder=get_resource_path('Frontend/static')
    )
    CORS(app)

    # Désactiver le cache des templates pour forcer le rechargement
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    
    def get_app_data_dir() -> str:
        """
        Dossier persistant et inscriptible (évite Program Files / _internal en mode installé).
        """
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "MARIHAR")

    def get_downloads_dir() -> str:
        """
        Dossier de téléchargement par défaut.
        Utilise le dossier Downloads de l'utilisateur pour éviter les problèmes de permissions.
        """
        # Essayer d'abord le dossier Downloads standard
        user_profile = os.path.expanduser("~")
        downloads_dir = os.path.join(user_profile, "Downloads")
        
        # Si le dossier n'existe pas, essayer "Téléchargements" (français)
        if not os.path.exists(downloads_dir):
            downloads_dir = os.path.join(user_profile, "Téléchargements")
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(downloads_dir, exist_ok=True)
        return downloads_dir

    # Configuration - Ressources (lecture) vs données (écriture)
    BASE_DIR = get_resource_path('.')  # dossier des ressources packagées (souvent _internal)
    APP_DATA_DIR = get_app_data_dir()
    os.makedirs(APP_DATA_DIR, exist_ok=True)

    # Charger la configuration personnalisée
    CONFIG_PATH = os.path.join(APP_DATA_DIR, "config.json")
    def load_config():
        default_config = {"custom_ytdlp_path": None}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_config
        return default_config

    def save_config(config):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    config = load_config()

    # Déterminer le chemin de yt-dlp
    # Essayer d'abord dans Binaries (dossier d'installation principal)
    YTDLP_PATH = get_resource_path("Binaries/yt-dlp.exe")
    if not os.path.exists(YTDLP_PATH):
        # Fallback : essayer _internal/Binaries
        YTDLP_PATH = os.path.join(BASE_DIR, "Binaries", "yt-dlp.exe")

    if config.get("custom_ytdlp_path") and os.path.exists(config["custom_ytdlp_path"]):
        YTDLP_PATH = config["custom_ytdlp_path"]
    # Vérifier que yt-dlp existe localement, sinon utiliser le chemin de secours
    elif not os.path.exists(YTDLP_PATH):
        YTDLP_PATH = os.environ.get("YTDLP_PATH", "yt-dlp.exe")
    
    # Dossier Downloads dans le dossier personnel de l'utilisateur
    DOWNLOADS_DIR = get_downloads_dir()
    
    # Créer le dossier downloads s'il n'existe pas
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    # Initialiser le service
    downloads_index_path = os.path.join(APP_DATA_DIR, "downloads_index.json")
    ytdlp_service = YTDLPService(
        ytdlp_path=YTDLP_PATH,
        downloads_dir=DOWNLOADS_DIR,
        download_index_path=downloads_index_path
    )
    
    # Initialiser le gestionnaire d'historique
    history_file_path = os.path.join(APP_DATA_DIR, "history.json")
    history_manager = HistoryManager(history_file_path, max_items=100)
    
    return app, ytdlp_service, DOWNLOADS_DIR, save_config, history_manager


# Créer l'application et le service
app, ytdlp_service, DOWNLOADS_DIR, _save_config, history_manager = create_app()


@app.route("/")
def index():
    """Page principale."""
    import time
    # Forcer le rechargement en ajoutant un timestamp
    response = render_template("index.html", timestamp=int(time.time()))
    print(f"[FLASK] Page servie avec timestamp={int(time.time())}")
    return response


@app.after_request
def add_no_cache_headers(response):
    """Ajoute des headers no-cache pour forcer le rechargement des fichiers statiques."""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyse une URL et retourne immédiatement un ID de tâche.
    L'analyse se fait en arrière-plan pour éviter les timeouts.
    
    Body JSON: {"url": "https://youtu.be/..."}
    """
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify({"error": "URL manquante"}), 400
    
    url = data["url"]
    search_mode = data.get("search_mode")
    
    try:
        # Déterminer si c'est une recherche ou une URL
        is_search = not (url.startswith("http://") or url.startswith("https://"))
        item_type = "search" if is_search else "url"
        
        # Ajouter à l'historique
        history_manager.add_item(url, item_type)
        
        task_id = ytdlp_service.start_analysis(url, search_mode=search_mode)
        return jsonify({
            "success": True,
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/analyze/progress/<task_id>", methods=["GET"])
def get_analysis_progress(task_id):
    """
    Récupère la progression et les logs d'une analyse en cours.
    """
    try:
        progress = ytdlp_service.get_analysis_progress(task_id)
        return jsonify(progress)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/analyze/playlist-video", methods=["POST"])
def analyze_playlist_video():
    """
    Analyse une vidéo individuelle d'une playlist.
    
    Body JSON:
    {
        "url": "https://youtu.be/...",
        "playlist_task_id": "..."
    }
    """
    try:
        data = request.get_json()
        url = data.get("url")
        playlist_task_id = data.get("playlist_task_id")
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL manquante"
            }), 400
        
        # Démarrer l'analyse de la vidéo
        task_id = ytdlp_service.analyze_playlist_video(url, playlist_task_id)
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "Analyse démarrée"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/download", methods=["POST"])
def download():
    """
    Démarre un téléchargement avec les options spécifiées.
    
    Body JSON:
    {
        "url": "https://youtu.be/...",
        "options": {
            "video_format": "299",
            "audio_format": "140",
            "merge_format": "mkv",
            "write_subs": true,
            "sub_langs": ["fr", "en"],
            "embed_subs": true,
            "write_auto_subs": false,
            "embed_thumbnail": true,
            "download_sections": "*01:10-01:30",
            "extract_audio": false,
            "audio_format_out": "mp3"
        }
    }
    """
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify({"error": "URL manquante"}), 400
    
    url = data["url"]
    options = data.get("options", {})
    
    try:
        task_id = ytdlp_service.start_download(url, options)
        return jsonify({
            "success": True,
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/select-folder", methods=["GET"])
def select_folder():
    """
    Ouvre un sélecteur de dossier local (desktop) et retourne le chemin choisi.
    """
    try:
        import os
        import sys
        import tkinter as tk
        from tkinter import filedialog

        def _resource_path(rel_path: str) -> str:
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base, rel_path)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # Icône de l'application (évite l'icône Python par défaut)
        try:
            icon_path = _resource_path("Assets/Logo_marino.ico")
            if os.path.exists(icon_path):
                # tkinter sur Windows accepte .ico
                root.iconbitmap(icon_path)
        except Exception:
            pass

        selected = filedialog.askdirectory(title="Choisir le dossier de téléchargement")
        root.destroy()

        if not selected:
            return jsonify({"success": False, "cancelled": True}), 200

        return jsonify({
            "success": True,
            "path": selected
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/download/playlist", methods=["POST"])
def download_playlist():
    """
    Démarre le téléchargement d'une playlist avec les formats sélectionnés.
    
    Body JSON:
    {
        "playlist_title": "Ma Playlist",
        "videos": [
            {
                "id": "video1",
                "url": "https://...",
                "format_id": "137",
                "format_type": "video"
            }
        ],
        "options": {...}
    }
    """
    data = request.get_json()
    
    if not data or "videos" not in data:
        return jsonify({"error": "Liste de vidéos manquante"}), 400
    
    videos = data.get("videos", [])
    playlist_title = data.get("playlist_title", "Playlist")
    options = data.get("options", {})
    
    if not videos:
        return jsonify({"error": "Aucune vidéo sélectionnée"}), 400
    
    try:
        task_id = ytdlp_service.start_playlist_download(playlist_title, videos, options)
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Téléchargement de {len(videos)} vidéo(s) démarré"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    """
    Retourne la progression d'un téléchargement.
    """
    progress = ytdlp_service.get_progress(task_id)
    
    if not progress:
        return jsonify({
            "success": False,
            "error": "Tâche non trouvée"
        }), 404
    
    return jsonify({
        "success": True,
        "data": progress
    })


@app.route("/api/cancel/<task_id>", methods=["POST"])
def cancel_download(task_id):
    """
    Annule un téléchargement en cours.
    """
    success = ytdlp_service.cancel_download(task_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": "Impossible d'annuler la tâche"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Tâche annulée"
    })


@app.route("/api/pause/<task_id>", methods=["POST"])
def pause_download(task_id):
    """
    Met en pause un téléchargement en cours.
    """
    success = ytdlp_service.pause_download(task_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": "Impossible de mettre en pause la tâche"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Tâche mise en pause"
    })


@app.route("/api/resume/<task_id>", methods=["POST"])
def resume_download(task_id):
    """
    Reprend un téléchargement en pause.
    """
    success = ytdlp_service.resume_download(task_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": "Impossible de reprendre la tâche"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Tâche reprise"
    })


@app.route("/api/analyze/cancel/<task_id>", methods=["POST"])
def cancel_analysis(task_id):
    """
    Annule une analyse en cours.
    """
    success = ytdlp_service.cancel_analysis(task_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": "Impossible d'annuler l'analyse"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Analyse annulée"
    })


@app.route("/downloads/<path:filename>")
def serve_download(filename):
    """
    Sert les fichiers téléchargés.
    """
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)


@app.route("/api/downloads")
def list_downloads():
    """
    Liste les fichiers téléchargés encore présents, tous dossiers confondus.
    """
    try:
        files = ytdlp_service.get_downloaded_files()
        
        return jsonify({
            "success": True,
            "files": files
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/download-file")
def download_file_from_path():
    """
    Sert un fichier téléchargé via son chemin absolu.
    """
    path = request.args.get("path")
    if not path:
        return jsonify({"success": False, "error": "Paramètre path manquant"}), 400
    if not os.path.isfile(path):
        return jsonify({"success": False, "error": "Fichier introuvable"}), 404
    return send_file(path, as_attachment=True)


def _safe_get_ytdlp_path() -> str:
    """
    Récupère le chemin actif de yt-dlp depuis le service.
    (Évite les problèmes de portée avec les variables locales de create_app()).
    """
    try:
        return getattr(ytdlp_service, "ytdlp_path", "yt-dlp.exe")
    except Exception:
        return "yt-dlp.exe"


@app.route("/api/ytdlp/config", methods=["GET"])
def get_ytdlp_config():
    """
    Retourne la configuration actuelle de yt-dlp.
    """
    ytdlp_path = _safe_get_ytdlp_path()
    return jsonify({
        "ytdlp_active_path": ytdlp_path,
        "custom_ytdlp_path": getattr(ytdlp_service, "ytdlp_custom_path", None),
        "ytdlp_exists": os.path.exists(ytdlp_path),
        "downloads_dir": DOWNLOADS_DIR,
    })


@app.route("/api/ytdlp/custom-ytdlp-path", methods=["POST"])
def set_custom_ytdlp_path():
    """
    Enregistre le chemin absolu d'un yt-dlp.exe custom (sans copier dans Program Files),
    puis met à jour dynamiquement le service.
    Body JSON: { "path": "D:\\Outils\\yt-dlp.exe" }
    """
    print("[YTDLP API] Requête reçue: /api/ytdlp/custom-ytdlp-path")
    data = request.get_json(silent=True) or {}
    print(f"[YTDLP API] Données reçues: {data}")
    raw_path = data.get("path")
    if not raw_path or not isinstance(raw_path, str):
        print("[YTDLP API] Erreur: Paramètre path manquant")
        return jsonify({"success": False, "error": "Paramètre path manquant"}), 400

    custom_path = raw_path.strip().strip('"').strip("'")
    print(f"[YTDLP API] Chemin custom: {custom_path}")
    if not custom_path:
        print("[YTDLP API] Erreur: Chemin yt-dlp invalide")
        return jsonify({"success": False, "error": "Chemin yt-dlp invalide"}), 400

    if not os.path.exists(custom_path):
        print(f"[YTDLP API] Erreur: yt-dlp introuvable: {custom_path}")
        return jsonify({"success": False, "error": f"yt-dlp introuvable: {custom_path}"}), 404

    # Charger puis sauver config.json dans le même dossier que create_app()
    app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "MARIHAR")
    config_path = os.path.join(app_data_dir, "config.json")
    print(f"[YTDLP API] Chemin config: {config_path}")

    try:
        config = {"custom_ytdlp_path": None}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f) or config

        config["custom_ytdlp_path"] = custom_path
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"[YTDLP API] Config sauvegardée: {custom_path}")
    except Exception as e:
        print(f"[YTDLP API] Erreur enregistrement config: {str(e)}")
        return jsonify({"success": False, "error": f"Erreur enregistrement config: {str(e)}"}), 500

    try:
        # Mettre à jour le service en runtime
        ytdlp_service.set_ytdlp_path(custom_path)
        # Marque optionnelle pour /api/ytdlp/config
        setattr(ytdlp_service, "ytdlp_custom_path", custom_path)
        print(f"[YTDLP API] Service mis à jour avec succès")
    except Exception as e:
        print(f"[YTDLP API] Erreur application path: {str(e)}")
        return jsonify({"success": False, "error": f"Erreur application path: {str(e)}"}), 500

    print(f"[YTDLP API] Succès: Chemin enregistré {custom_path}")
    return jsonify({
        "success": True,
        "active_path": custom_path,
        "config_path": config_path,
        "message": f"Chemin enregistré: {custom_path}"
    })


def _run_update_ytdlp(update_cmd: list) -> tuple[bool, str]:
    """
    Lance la mise à jour de manière synchrone et retourne le résultat.
    Retourne (success, output) où success indique si la commande s'est terminée sans erreur.
    """
    try:
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace"
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(update_cmd, **kwargs)
        output = result.stdout if result.stdout else ""
        return (result.returncode == 0, output)
    except Exception as e:
        return (False, str(e))


@app.route("/api/ytdlp/update-auto", methods=["POST"])
def update_ytdlp_auto():
    """
    Met à jour yt-dlp de manière synchrone via: yt-dlp.exe -U
    Analyse la sortie pour déterminer le statut de la mise à jour.
    """
    print("[YTDLP API] Requête reçue: /api/ytdlp/update-auto")
    ytdlp_path = _safe_get_ytdlp_path()
    print(f"[YTDLP API] Chemin yt-dlp: {ytdlp_path}")
    if not ytdlp_path or not os.path.exists(ytdlp_path):
        print(f"[YTDLP API] Erreur: yt-dlp introuvable")
        return jsonify({"success": False, "error": "yt-dlp actif introuvable"}), 404

    update_cmd = [ytdlp_path, "-U"]
    print(f"[YTDLP API] Lancement mise à jour: {' '.join(update_cmd)}")

    # Lancer la mise à jour de manière synchrone et capturer la sortie
    success, output = _run_update_ytdlp(update_cmd)
    print(f"[YTDLP API] Sortie de yt-dlp -U:\n{output}")

    # Analyser la sortie pour déterminer le statut
    output_lower = output.lower()
    if "up to date" in output_lower or "déjà à jour" in output_lower:
        message = "yt-dlp est déjà à jour"
        status = "already_up_to_date"
    elif "updated" in output_lower or "mise à jour" in output_lower or "latest version" in output_lower:
        message = "Mise à jour de yt-dlp réussie"
        status = "updated"
    elif success:
        message = "Mise à jour terminée (statut inconnu)"
        status = "unknown"
    else:
        message = f"Erreur lors de la mise à jour: {output}"
        status = "error"

    print(f"[YTDLP API] Statut: {status}, Message: {message}")
    return jsonify({
        "success": success,
        "message": message,
        "status": status,
        "output": output,
        "path": ytdlp_path
    })


@app.route("/api/ytdlp/reset-to-default", methods=["POST"])
def reset_ytdlp_to_default():
    """
    Réinitialise yt-dlp à la version par défaut (intégrée dans le logiciel).
    Supprime le chemin personnalisé du config.json.
    """
    print("[YTDLP API] Requête reçue: /api/ytdlp/reset-to-default")

    # Charger et mettre à jour config.json
    app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "MARIHAR")
    config_path = os.path.join(app_data_dir, "config.json")
    print(f"[YTDLP API] Chemin config: {config_path}")

    try:
        config = {"custom_ytdlp_path": None}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f) or config

        config["custom_ytdlp_path"] = None
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("[YTDLP API] Config réinitialisée (custom_ytdlp_path = None)")
    except Exception as e:
        print(f"[YTDLP API] Erreur réinitialisation config: {str(e)}")
        return jsonify({"success": False, "error": f"Erreur réinitialisation config: {str(e)}"}), 500

    # Réinitialiser le service au chemin par défaut
    try:
        BASE_DIR = get_resource_path('.')
        default_path = os.path.join(BASE_DIR, "yt-dlp.exe")
        if not os.path.exists(default_path):
            default_path = os.environ.get("YTDLP_PATH", "yt-dlp.exe")

        ytdlp_service.set_ytdlp_path(default_path)
        setattr(ytdlp_service, "ytdlp_custom_path", None)
        print(f"[YTDLP API] Service réinitialisé à: {default_path}")
    except Exception as e:
        print(f"[YTDLP API] Erreur réinitialisation service: {str(e)}")
        return jsonify({"success": False, "error": f"Erreur réinitialisation service: {str(e)}"}), 500

    print("[YTDLP API] Succès: yt-dlp réinitialisé par défaut")
    return jsonify({"success": True, "message": "yt-dlp réinitialisé à la version par défaut"})


@app.route("/api/preview_subtitle", methods=["POST"])
def preview_subtitle():
    """
    Génère une image de prévisualisation des sous-titres.
    
    Body JSON: {
        "sub_style": {
            "color": "#ffffff",
            "outline_color": "#000000",
            "font_size": 28,
            "position": 85,
            "outline": 3,
            "font_style": 1
        }
    }
    """
    import subprocess
    import tempfile
    
    data = request.get_json()
    sub_style = data.get("sub_style", {})
    
    try:
        # Créer une image de test avec FFmpeg
        preview_file = os.path.join(DOWNLOADS_DIR, "subtitle_preview.png")
        
        # Paramètres de style
        def hex_to_ass_color(hex_color):
            hex_color = hex_color.lstrip('#')
            r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
            return f"&H00{b}{g}{r}".upper()
        
        color = hex_to_ass_color(sub_style.get('color', '#ffffff'))
        outline_color = hex_to_ass_color(sub_style.get('outline_color', '#000000'))
        font_size = sub_style.get('font_size', 28)
        position = sub_style.get('position', 85)
        outline = sub_style.get('outline', 3)
        font_style = sub_style.get('font_style', 1)
        
        bold = "-1" if font_style == 1 else "0"
        italic = "-1" if font_style == 2 else "0"
        
        # Déterminer l'alignment
        if position <= 30:
            y_pos = "h*0.15"
        elif position <= 45:
            y_pos = "h*0.35"
        elif position <= 60:
            y_pos = "h*0.50"
        elif position <= 75:
            y_pos = "h*0.65"
        else:
            y_pos = "h*0.85"
        
        # Créer l'image avec drawtext
        ffmpeg_path = get_resource_path("Binaries/ffmpeg.exe")

        cmd = [
            ffmpeg_path,
            "-f", "lavfi",
            "-i", "color=c=black:s=640x360:d=1",
            "-vf",
            f"drawtext=text='Exemple de sous-titre':fontcolor={sub_style.get('color', '#ffffff')}:"
            f"fontsize={font_size}:x=(w-text_w)/2:y={y_pos}:"
            f"borderw={outline}:bordercolor={sub_style.get('outline_color', '#000000')}",
            "-frames:v", "1",
            "-y",
            preview_file
        ]
        
        # Cacher la fenêtre console sous Windows
        startupinfo = None
        creationflags = 0
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            from subprocess import CREATE_NO_WINDOW
            creationflags = CREATE_NO_WINDOW
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        if result.returncode == 0 and os.path.exists(preview_file):
            return send_from_directory(DOWNLOADS_DIR, "subtitle_preview.png")
        else:
            return jsonify({"error": "Échec de la génération de la prévisualisation"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== HISTORY API ENDPOINTS ==========

@app.route("/api/history", methods=["GET"])
def get_history():
    """
    Récupère l'historique.
    
    Query parameters:
        - type: Filtrer par type ("url" ou "search"), optionnel
        - limit: Nombre maximum d'éléments à retourner, optionnel
    """
    try:
        item_type = request.args.get("type")
        limit = request.args.get("limit", type=int)
        
        history = history_manager.get_history(item_type=item_type, limit=limit)
        
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/history", methods=["POST"])
def add_to_history():
    """
    Ajoute un élément à l'historique.
    
    Body JSON: {
        "query": "URL ou recherche",
        "type": "url" | "search",
        "metadata": {...}  # optionnel
    }
    """
    try:
        data = request.get_json()
        
        if not data or "query" not in data:
            return jsonify({"error": "Requête invalide"}), 400
        
        query = data["query"]
        item_type = data.get("type", "url")
        metadata = data.get("metadata", {})
        
        item = history_manager.add_item(query, item_type, metadata)
        
        return jsonify({
            "success": True,
            "item": item
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/history/<item_id>", methods=["DELETE"])
def delete_history_item(item_id):
    """Supprime un élément spécifique de l'historique."""
    try:
        success = history_manager.delete_item(item_id)
        
        return jsonify({
            "success": success
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """Vide complètement l'historique."""
    try:
        history_manager.clear_history()
        
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print(f"Démarrage du serveur yt-dlp Web Interface...")
    print(f"yt-dlp path: {ytdlp_service.ytdlp_path}")
    print(f"Downloads dir: {DOWNLOADS_DIR}")
    print(f"Ouvrez http://localhost:5000 dans votre navigateur")

    # Désactiver le mode debug pour de meilleures performances
    # Écouter uniquement sur localhost pour la sécurité (pas d'accès réseau)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
