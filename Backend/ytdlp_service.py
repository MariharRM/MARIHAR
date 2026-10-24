# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
Service d'interaction avec yt-dlp pour l'analyse et le téléchargement de vidéos.
"""
import subprocess
import json
import re
import os
import sys
import uuid
import locale
from urllib.parse import quote
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from threading import Lock, Thread
import time

# Import yt-dlp Python API
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

# Import pour cacher la fenêtre console sous Windows
if sys.platform == 'win32':
    import ctypes
    from subprocess import CREATE_NO_WINDOW, SW_HIDE
else:
    CREATE_NO_WINDOW = 0


@dataclass
class DownloadTask:
    """Représente une tâche de téléchargement en cours."""
    id: str
    url: str
    process: Optional[subprocess.Popen] = None
    progress: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, downloading, completed, error, cancelled
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    output_dir: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    burn_subs: bool = False
    requested_sub_langs: List[str] = field(default_factory=list)
    requested_write_subs: bool = False
    requested_write_auto_subs: bool = False
    subs_only: bool = False


@dataclass
class AnalysisTask:
    """Représente une tâche d'analyse en cours."""
    id: str
    url: str
    logs: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, analyzing, completed, error, cancelled
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    thread: Optional[Thread] = None
    process: Optional[subprocess.Popen] = None
    start_time: float = field(default_factory=time.time)



class YTDLPService:
    """Service principal pour interagir avec yt-dlp."""

    def __init__(self, ytdlp_path: str = None, downloads_dir: str = "downloads", download_index_path: Optional[str] = None):
        # Définir le chemin par défaut vers yt-dlp.exe dans le dossier Binaries
        if ytdlp_path is None:
            ytdlp_path = self._get_binaries_path("yt-dlp.exe")

        self.ytdlp_path = ytdlp_path
        self.downloads_dir = downloads_dir
        self.download_index_path = download_index_path or os.path.join(os.path.dirname(os.path.abspath(downloads_dir)), "downloads_index.json")
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.active_analyses: Dict[str, AnalysisTask] = {}
        self.lock = Lock()

        # Créer le dossier de téléchargements s'il n'existe pas
        os.makedirs(downloads_dir, exist_ok=True)
        index_parent = os.path.dirname(self.download_index_path)
        if index_parent:
            os.makedirs(index_parent, exist_ok=True)

        # Configurer l'environnement pour Deno et FFmpeg
        self._setup_environment()

    def _get_binaries_path(self, filename: str) -> str:
        """
        Obtient le chemin vers un fichier dans le dossier Binaries.
        Cherche d'abord dans le dossier d'installation principal, puis dans _internal.
        """
        # D'abord, essayer le dossier d'installation principal (au-dessus de _internal)
        try:
            if hasattr(sys, '_MEIPASS'):
                install_dir = os.path.dirname(sys._MEIPASS)
                candidate_path = os.path.join(install_dir, 'Binaries', filename)
                if os.path.exists(candidate_path):
                    return candidate_path
        except Exception:
            pass

        # Ensuite, essayer le chemin normal (développement)
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_dir, 'Binaries', filename)

    def _get_binaries_dir(self) -> str:
        """
        Obtient le chemin du dossier Binaries.
        """
        try:
            if hasattr(sys, '_MEIPASS'):
                install_dir = os.path.dirname(sys._MEIPASS)
                candidate_dir = os.path.join(install_dir, 'Binaries')
                if os.path.exists(candidate_dir):
                    return candidate_dir
        except Exception:
            pass

        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_dir, 'Binaries')

    def set_ytdlp_path(self, new_path: str) -> None:
        """
        Met à jour dynamiquement le chemin vers yt-dlp.exe et reconfigure l'environnement.
        Utilisé par le mode "yt-dlp custom" + update auto.
        """
        normalized = str(new_path).strip()
        if not normalized:
            raise ValueError("Chemin yt-dlp invalide")

        # Vérifier l'existence quand on passe un chemin absolu (sinon on laisse passer si c'est juste 'yt-dlp')
        if os.path.isabs(normalized) or "\\" in normalized or "/" in normalized:
            if not os.path.exists(normalized):
                raise FileNotFoundError(f"yt-dlp introuvable: {normalized}")

        with self.lock:
            self.ytdlp_path = normalized
            self._setup_environment()

    def _setup_environment(self):
        """Configure l'environnement pour que yt-dlp trouve Deno et FFmpeg."""
        # Obtenir le dossier Binaries avec la nouvelle méthode
        binaries_dir = self._get_binaries_dir()
        
        # Ajouter le dossier Binaries au PATH pour Deno et FFmpeg (au début pour priorité)
        current_path = os.environ.get('PATH', '')
        if binaries_dir not in current_path:
            os.environ['PATH'] = binaries_dir + os.pathsep + current_path
        
        # Définir explicitement le chemin vers Deno
        deno_path = os.path.join(binaries_dir, 'deno.exe')
        if os.path.exists(deno_path):
            os.environ['DENO_PATH'] = deno_path
            # Variable supplémentaire pour yt-dlp
            os.environ['DENO_DIR'] = binaries_dir
        
        # Sous Windows, s'assurer que les subprocess n'ouvrent pas de fenêtre
        if sys.platform == 'win32':
            # Créer un STARTUPINFO pour cacher la fenêtre
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            self.startupinfo = None
        
        # Log pour debug
        print(f"[DEBUG] PATH configuré: {os.environ.get('PATH', '')[:100]}...")
        print(f"[DEBUG] DENO_PATH: {os.environ.get('DENO_PATH', 'NON DÉFINI')}")
        print(f"[DEBUG] Deno existe: {os.path.exists(deno_path)}")
    
    def _get_subprocess_kwargs(self, hide_window=True):
        """Retourne les arguments pour subprocess sans fenêtre sous Windows."""
        kwargs = {}
        if sys.platform == 'win32' and hide_window:
            kwargs['startupinfo'] = self.startupinfo
            # Utiliser CREATE_NO_WINDOW pour cacher complètement la fenêtre console
            # Cela fonctionne même quand l'application est compilée en exe
            kwargs['creationflags'] = CREATE_NO_WINDOW
        return kwargs

    def _get_text_decode_kwargs(self) -> Dict[str, Any]:
        """
        Retourne une configuration de décodage robuste pour éviter les erreurs Unicode.
        yt-dlp peut émettre des octets non UTF-8 sur certains contenus/plateformes.
        """
        return {
            "text": True,
            "encoding": "utf-8",
            "errors": "replace"
        }

    def _read_text_file_with_fallback(self, path: str) -> str:
        """
        Lit un fichier texte avec fallback d'encodage.
        Utilisé pour les sous-titres qui peuvent être en UTF-8, cp1252, latin-1, etc.
        """
        encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1", locale.getpreferredencoding(False)]
        last_error = None
        for enc in encodings:
            if not enc:
                continue
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if last_error:
                return f.read()
            return f.read()

    def _find_latest_media_file(self, min_ctime: float = 0.0) -> Optional[str]:
        """Trouve le fichier média le plus récent dans le dossier de téléchargement."""
        return self._find_latest_media_file_in_dir(self.downloads_dir, min_ctime=min_ctime)

    def _find_latest_media_file_in_dir(self, downloads_dir: str, min_ctime: float = 0.0, include_subs: bool = False) -> Optional[str]:
        """Trouve le fichier média le plus récent dans un dossier donné."""
        latest_file = None
        latest_ctime = 0.0
        extensions = [".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".aac", ".opus", ".wav"]
        if include_subs:
            extensions.extend([".srt", ".vtt", ".ass"])
        for filename in os.listdir(downloads_dir):
            if not filename.lower().endswith(tuple(extensions)):
                continue
            filepath = os.path.join(downloads_dir, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                ctime = os.path.getctime(filepath)
            except OSError:
                continue
            if ctime >= min_ctime and ctime >= latest_ctime:
                latest_ctime = ctime
                latest_file = filepath
        return latest_file

    def _find_subtitle_file_for_video(self, video_file: str, sub_langs: Optional[List[str]] = None, downloads_dir: Optional[str] = None) -> Optional[str]:
        """Trouve un fichier .srt correspondant à la vidéo."""
        if not video_file:
            return None
        subtitle_dir = downloads_dir or self.downloads_dir
        base_name = os.path.splitext(video_file)[0]
        base_filename = os.path.basename(base_name)
        lang_candidates = sub_langs or []

        # Priorité aux langues demandées
        for lang in lang_candidates:
            candidate = f"{base_name}.{lang}.srt"
            if os.path.exists(candidate):
                return candidate

        # Fallback sur n'importe quel .srt de la même vidéo
        for filename in os.listdir(subtitle_dir):
            filepath = os.path.join(subtitle_dir, filename)
            if not os.path.isfile(filepath):
                continue
            # Utiliser le nom de fichier uniquement pour la comparaison
            file_basename = os.path.splitext(filename)[0]
            if file_basename == base_filename and filename.lower().endswith(".srt"):
                return filepath
        return None

    def _download_subtitles_for_hardcode(self, task: DownloadTask, video_file: str, sub_langs: List[str]) -> bool:
        """
        Télécharge les sous-titres séparément après la vidéo pour éviter l'échec global 429.
        Stratégie: original -> auto, avec retries et backoff.
        Si video_file est None (mode subs_only), télécharge les sous-titres directement.
        """
        # Mode sous-titres uniquement: pas besoin de fichier vidéo
        if getattr(task, 'subs_only', False):
            return self._download_subtitles_only(task, sub_langs)

        if not video_file or not os.path.exists(video_file):
            return False
        if not sub_langs:
            task.logs.append("[WARNING] Hardcode demandé mais aucune langue de sous-titres sélectionnée.")
            return False

        task.status = "downloading_subs"
        task_output_dir = task.output_dir or self.downloads_dir
        output_template = os.path.join(task_output_dir, "%(title)s.%(ext)s")

        strategies = [
            ("--write-subs", "originaux"),
            ("--write-auto-sub", "automatiques"),
        ]

        backoff_seconds = [8, 20, 40]
        for flag, label in strategies:
            task.logs.append(f"[INFO] Tentative sous-titres {label} (mode séparé)...")
            
            # Télécharger chaque langue séparément pour éviter qu'un échec bloque les autres
            successful_langs = []
            for lang in sub_langs:
                task.logs.append(f"[INFO] Téléchargement sous-titres {label} pour langue: {lang}")
                for attempt, wait_sec in enumerate(backoff_seconds, start=1):
                    cmd = [
                        self.ytdlp_path,
                        "--skip-download",
                        "--no-warnings",
                        "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                        "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                        "--retries", "infinite",  # Retries illimités pour stabilité
                        "--sleep-requests", "3",
                        "--retry-sleep", "10",  # Dlai augment entre retries
                        "--sub-langs", lang,
                        "--sub-format", "srt",
                        "--convert-subs", "srt",
                        "--extractor-args", "youtube:player_client=android,web",
                        "-o", output_template,
                        flag,
                        task.url
                    ]
                    subprocess_kwargs = self._get_subprocess_kwargs()
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        **self._get_text_decode_kwargs(),
                        **subprocess_kwargs
                    )

                    # Reporter les dernières lignes utiles pour debug
                    stderr_tail = (result.stderr or "").strip().splitlines()[-5:]
                    for line in stderr_tail:
                        if line:
                            task.logs.append(line)

                    # Attendre un peu pour que le fichier soit écrit sur le disque
                    time.sleep(1)
                    
                    found_sub = self._find_subtitle_file_for_video(video_file, [lang], task_output_dir)
                    if result.returncode == 0 and found_sub:
                        task.logs.append(f"[SUCCESS] Sous-titres {label} récupérés pour {lang}: {os.path.basename(found_sub)}")
                        successful_langs.append(lang)
                        break  # Succès pour cette langue, passer à la suivante

                    combined = f"{result.stdout}\n{result.stderr}".lower()
                    is_429 = "http error 429" in combined or "too many requests" in combined
                    if attempt < len(backoff_seconds):
                        if is_429:
                            task.logs.append(f"[WARNING] Sous-titres limités (429) pour {lang}, nouvelle tentative dans {wait_sec}s...")
                        else:
                            task.logs.append(f"[WARNING] Échec tentative sous-titres ({label}) pour {lang}, retry dans {wait_sec}s...")
                        time.sleep(wait_sec)
                    else:
                        task.logs.append(f"[WARNING] Sous-titres {label} non disponibles pour {lang} après tous les essais")
            
            # Si au moins une langue a réussi, considérer comme succès
            if successful_langs:
                task.logs.append(f"[SUCCESS] Sous-titres {label} récupérés pour {len(successful_langs)}/{len(sub_langs)} langues: {', '.join(successful_langs)}")
                return True

        return self._find_subtitle_file_for_video(video_file, sub_langs, task_output_dir) is not None

    def _download_subtitles_only(self, task: DownloadTask, sub_langs: List[str]) -> bool:
        """
        Télécharge uniquement les sous-titres sans la vidéo.
        Stratégie: original -> auto, avec retries et backoff.
        Si sub_langs est vide, télécharge tous les sous-titres disponibles.
        """
        if not sub_langs:
            task.logs.append("[INFO] Téléchargement de tous les sous-titres disponibles (aucune langue spécifique sélectionnée).")
            # Télécharger tous les sous-titres disponibles sans restriction de langue
            lang_value = "all"
        else:
            lang_value = ",".join(sub_langs)

        task.status = "downloading_subs"
        task_output_dir = task.output_dir or self.downloads_dir
        output_template = os.path.join(task_output_dir, "%(title)s.%(ext)s")

        strategies = [
            ("--write-subs", "originaux"),
            ("--write-auto-sub", "automatiques"),
        ]

        backoff_seconds = [8, 20, 40]
        for flag, label in strategies:
            task.logs.append(f"[INFO] Tentative sous-titres {label} (mode uniquement)...")
            
            # Télécharger chaque langue séparément pour éviter qu'un échec bloque les autres
            successful_langs = []
            for lang in sub_langs:
                task.logs.append(f"[INFO] Téléchargement sous-titres {label} pour langue: {lang}")
                for attempt, wait_sec in enumerate(backoff_seconds, start=1):
                    cmd = [
                        self.ytdlp_path,
                        "--skip-download",
                        "--no-warnings",
                        "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                        "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                        "--retries", "infinite",  # Retries illimités pour stabilité
                        "--sleep-requests", "3",
                        "--retry-sleep", "10",  # Dlai augment entre retries
                        "--sub-langs", lang,
                        "--sub-format", "srt",
                        "--convert-subs", "srt",
                        "--extractor-args", "youtube:player_client=android,web",
                        "-o", output_template,
                        flag,
                        task.url
                    ]
                    subprocess_kwargs = self._get_subprocess_kwargs()
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        **self._get_text_decode_kwargs(),
                        **subprocess_kwargs
                    )

                    # Reporter les dernières lignes utiles pour debug
                    stderr_tail = (result.stderr or "").strip().splitlines()[-5:]
                    for line in stderr_tail:
                        if line:
                            task.logs.append(line)

                    # Attendre un peu pour que le fichier soit écrit sur le disque
                    time.sleep(1)
                    
                    # Trouver les fichiers de sous-titres téléchargés pour cette langue
                    found_subs = self._find_subtitle_files(task_output_dir, [lang], task.created_at)
                    if result.returncode == 0 and found_subs:
                        for sub_file in found_subs:
                            task.logs.append(f"[SUCCESS] Sous-titre {label} récupéré pour {lang}: {os.path.basename(sub_file)}")
                            self._register_download_file(sub_file)
                        successful_langs.append(lang)
                        break  # Succès pour cette langue, passer à la suivante

                    combined = f"{result.stdout}\n{result.stderr}".lower()
                    is_429 = "http error 429" in combined or "too many requests" in combined
                    if attempt < len(backoff_seconds):
                        if is_429:
                            task.logs.append(f"[WARNING] Sous-titres limités (429) pour {lang}, nouvelle tentative dans {wait_sec}s...")
                        else:
                            task.logs.append(f"[WARNING] Échec tentative sous-titres ({label}) pour {lang}, retry dans {wait_sec}s...")
                        time.sleep(wait_sec)
                    else:
                        task.logs.append(f"[WARNING] Sous-titres {label} non disponibles pour {lang} après tous les essais")
            
            # Si au moins une langue a réussi, considérer comme succès
            if successful_langs:
                task.logs.append(f"[SUCCESS] Sous-titres {label} récupérés pour {len(successful_langs)}/{len(sub_langs)} langues: {', '.join(successful_langs)}")
                return True

        # Vérifier si des sous-titres ont été téléchargés malgré tout
        found_subs = self._find_subtitle_files(task_output_dir, sub_langs if sub_langs else None, task.created_at)
        if found_subs:
            for sub_file in found_subs:
                self._register_download_file(sub_file)
            return True
        return False

    def _find_subtitle_files(self, downloads_dir: str, sub_langs: List[str], min_ctime: float) -> List[str]:
        """Trouve tous les fichiers de sous-titres récents dans le dossier."""
        found_files = []
        for filename in os.listdir(downloads_dir):
            if not filename.lower().endswith((".srt", ".vtt", ".ass")):
                continue
            filepath = os.path.join(downloads_dir, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                ctime = os.path.getctime(filepath)
            except OSError:
                continue
            if ctime >= min_ctime:
                found_files.append(filepath)
        return found_files

    def _resolve_output_dir(self, options: Dict[str, Any]) -> str:
        """Résout et valide le dossier de sortie demandé par l'utilisateur."""
        raw_output = options.get("output_dir")
        if raw_output and str(raw_output).strip():
            output_dir = os.path.abspath(os.path.expanduser(str(raw_output).strip()))
        else:
            output_dir = self.downloads_dir
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _load_download_index(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.download_index_path):
                return []
            with open(self.download_index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_download_index(self, entries: List[Dict[str, Any]]) -> None:
        with open(self.download_index_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def _register_download_file(self, file_path: str) -> None:
        if not file_path or not os.path.isfile(file_path):
            return
        abs_path = os.path.abspath(file_path)
        entries = self._load_download_index()
        # Supprimer ancien enregistrement même chemin (on garde le plus récent)
        entries = [e for e in entries if e.get("path") != abs_path]
        stat = os.stat(abs_path)
        entries.append({
            "name": os.path.basename(abs_path),
            "path": abs_path,
            "size": stat.st_size,
            "created": stat.st_ctime,
        })
        # Limiter la taille du registre
        entries.sort(key=lambda x: x.get("created", 0), reverse=True)
        self._save_download_index(entries[:2000])

    def get_downloaded_files(self) -> List[Dict[str, Any]]:
        """
        Retourne les téléchargements encore existants, peu importe leur dossier.
        Affiche uniquement les fichiers enregistrés dans l'index (téléchargés par MARIHAR).
        Filtre uniquement les fichiers audio, vidéo et sous-titres.
        """
        entries = self._load_download_index()
        valid_entries = []
        
        # Extensions de fichiers valides (audio, vidéo, sous-titres)
        valid_extensions = {
            # Vidéo
            '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.ts', '.m2ts',
            # Audio
            '.mp3', '.m4a', '.aac', '.flac', '.wav', '.ogg', '.wma', '.opus', '.aiff', '.alac',
            # Sous-titres
            '.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx', '.json'
        }
        
        for e in entries:
            path = e.get("path")
            if not path or not os.path.isfile(path):
                continue
            try:
                stat = os.stat(path)
            except OSError:
                continue
            
            # Vérifier l'extension du fichier
            file_ext = os.path.splitext(path)[1].lower()
            if file_ext not in valid_extensions:
                continue
            
            valid_entries.append({
                "name": os.path.basename(path),
                "path": path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "directory": os.path.dirname(path),
                "download_url": f"/api/download-file?path={quote(path)}"
            })
        valid_entries.sort(key=lambda x: x["created"], reverse=True)
        # Nettoyer le registre des entrées supprimées
        compact_entries = [
            {"name": e["name"], "path": e["path"], "size": e["size"], "created": e["created"]}
            for e in valid_entries
        ]
        self._save_download_index(compact_entries)
        return valid_entries
    
    def start_analysis(self, url: str, search_mode: Optional[str] = None) -> str:
        """
        Démarre une analyse en arrière-plan et retourne l'ID de la tâche.
        """
        # Si ce n'est pas une URL, on considère que c'est une recherche
        if not self._is_url(url):
            # Utiliser le mode de recherche spécifié ou ytsearch20 par défaut
            prefix = search_mode if search_mode else "ytsearch20"
            url = f"{prefix}:{url}"
            
        task_id = str(uuid.uuid4())
        task = AnalysisTask(id=task_id, url=url)
        
        with self.lock:
            self.active_analyses[task_id] = task
        
        # Démarrer l'analyse dans un thread séparé
        thread = Thread(target=self._run_analysis, args=(task_id, url))
        thread.daemon = True
        thread.start()
        task.thread = thread
        
        return task_id

    def _is_url(self, text: str) -> bool:
        """Vérifie si le texte est une URL ou un identifiant reconnu par yt-dlp."""
        text = text.strip()
        # Regex simple pour URL
        url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
            r'localhost|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # Si ça commence par un protocole supporté par yt-dlp
        yt_dlp_prefixes = ('ytsearch', 'gvsearch', 'scsearch', 'yvsearch', 'ytsearchdate', 'vimeo', 'facebook', 'instagram', 'twitter', 'tiktok', 'youtube')
        
        if any(text.lower().startswith(prefix) for prefix in yt_dlp_prefixes):
            return True
            
        return re.match(url_regex, text) is not None
    
    def _run_analysis(self, task_id: str, url: str):
        """
        Exécute l'analyse dans un thread séparé.
        """
        task = self.active_analyses.get(task_id)
        if not task:
            return
        
        task.status = "analyzing"
        task.start_time = time.time()
        task.logs.append(f"[INFO] Démarrage de l'analyse de: {url}")
        
        try:
            # Utiliser subprocess pour avoir les logs en temps réel
            cmd = [
                self.ytdlp_path,
                "-J",
                "--no-warnings",
                "--newline",
                "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                url
            ]
            
            task.logs.append(f"[CMD] {' '.join(cmd)}")
            
            # Lancer le processus
            subprocess_kwargs = self._get_subprocess_kwargs()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **self._get_text_decode_kwargs(),
                bufsize=1,
                universal_newlines=True,
                **subprocess_kwargs
            )
            task.process = process
            
            # Lire stderr en temps réel pour les logs
            import threading
            def read_stderr():
                for line in process.stderr:
                    line = line.strip()
                    if line:
                        task.logs.append(line)
            
            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()
            
            # Attendre la fin avec timeout de 8 heure (pas de restriction)
            try:
                stdout, _ = process.communicate(timeout=28800)
                
                if process.returncode == 0:
                    data = json.loads(stdout)
                    task.logs.append("[SUCCESS] Analyse terminée avec succès")
                    
                    # Vérifier si c'est une erreur de yt-dlp (vidéo privée, géobloquée, etc.)
                    if data.get('extractor') == 'generic' and not data.get('formats'):
                        raise Exception("URL non supportée ou vidéo inaccessible")
                    
                    # Informations détaillées sur la vidéo avec gestion des caractères spéciaux
                    title = data.get('title', 'N/A')
                    if title:
                        title = str(title).encode('utf-8', errors='replace').decode('utf-8')
                    task.logs.append(f"[INFO] Titre: {title}")
                    
                    uploader = data.get('uploader', 'N/A')
                    if uploader:
                        uploader = str(uploader).encode('utf-8', errors='replace').decode('utf-8')
                    task.logs.append(f"[INFO] Uploader: {uploader}")
                    
                    task.logs.append(f"[INFO] Durée: {self._format_duration(data.get('duration'))}")
                    task.logs.append(f"[INFO] Vues: {data.get('view_count', 'N/A')}")
                    task.logs.append(f"[INFO] Plateforme: {data.get('extractor', 'N/A')}")
                    
                    # Avertissements spécifiques
                    if data.get('age_limit'):
                        task.logs.append(f"[WARN] Limite d'âge: {data.get('age_limit')}+")
                    if data.get('availability'):
                        task.logs.append(f"[INFO] Disponibilité: {data.get('availability')}")
                    
                    # Log du nombre de formats trouvés
                    formats_count = len(data.get('formats', []))
                    task.logs.append(f"[INFO] {formats_count} formats trouvés")
                    
                    # Logs techniques détaillés
                    task.logs.append(f"[TECH] ID vidéo: {data.get('id', 'N/A')}")
                    task.logs.append(f"[TECH] URL: {data.get('webpage_url', url)}")
                    task.logs.append(f"[TECH] Type: {data.get('_type', 'video')}")
                    
                    # Informations sur les formats bruts
                    for i, fmt in enumerate(data.get('formats', [])[:5]):  # Limiter à 5 pour éviter trop de logs
                        fmt_id = fmt.get('format_id', 'N/A')
                        vcodec = fmt.get('vcodec', 'none')
                        acodec = fmt.get('acodec', 'none')
                        res = fmt.get('resolution', 'N/A')
                        proto = fmt.get('protocol', 'N/A')
                        task.logs.append(f"[TECH] Format {i+1}: {fmt_id} | {res} | v:{vcodec} | a:{acodec} | {proto}")
                    
                    if formats_count > 5:
                        task.logs.append(f"[TECH] ... et {formats_count - 5} formats supplémentaires")
                    
                    # Vérifier si c'est une playlist
                    is_playlist = data.get('_type') == 'playlist' or ('entries' in data and len(data.get('entries', [])) > 1)
                    
                    if is_playlist:
                        # Pour les playlists, lancer yt-dlp -F pour obtenir tous les formats
                        task.logs.append("")
                        task.logs.append("[INFO] Analyse complète des formats de la playlist...")
                        task.logs.append("")
                        
                        # Lancer yt-dlp -F pour afficher tous les formats comme en CMD
                        cmd_f = [
                            self.ytdlp_path,
                            "-F",
                            "--no-warnings",
                            "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                            "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                            url
                        ]
                        
                        task.logs.append(f"[CMD] {' '.join(cmd_f)}")
                        task.logs.append("")
                        
                        # Obtenir les paramètres subprocess
                        subprocess_kwargs = self._get_subprocess_kwargs()
                        
                        process_f = subprocess.Popen(
                            cmd_f,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            **self._get_text_decode_kwargs(),
                            bufsize=1,
                            universal_newlines=True,
                            **subprocess_kwargs
                        )
                        
                        # Lire et afficher la sortie en temps réel
                        current_video = None
                        video_formats = {}  # Stocker les formats par vidéo
                        
                        for line in process_f.stdout:
                            line = line.rstrip()
                            if line:
                                # Afficher dans les logs
                                if 'Extracting URL' in line or 'Downloading' in line:
                                    task.logs.append(f"[INFO] {line}")
                                elif 'Available formats' in line:
                                    task.logs.append(f"[INFO] {line}")
                                    # Extraire l'ID de la vidéo avec une regex
                                    import re
                                    match = re.search(r'Available formats for ([\w-]+):', line)
                                    if match:
                                        current_video = match.group(1)
                                        video_formats[current_video] = []
                                        task.logs.append(f"[DEBUG] Vidéo détectée: {current_video}")
                                elif line.startswith('ID') or line.startswith('─'):
                                    # Ligne d'en-tête ou séparateur
                                    task.logs.append(line)
                                elif line.strip() and not line.startswith('['):
                                    # Ligne de format
                                    task.logs.append(line)
                                    if current_video:
                                        video_formats[current_video].append(line)
                                else:
                                    task.logs.append(line)
                        
                        process_f.wait()
                        
                        if process_f.returncode == 0:
                            task.logs.append("")
                            task.logs.append("[SUCCESS] Analyse complète des formats terminée")
                            task.logs.append(f"[DEBUG] {len(video_formats)} vidéos avec formats analysés")
                            for vid_id, formats in video_formats.items():
                                task.logs.append(f"[DEBUG] Vidéo {vid_id}: {len(formats)} formats")
                        
                        # Parser les informations de base de la playlist
                        result = self._parse_playlist_info_flat(data)
                        
                        # Ajouter les formats analysés à chaque vidéo
                        formats_added = 0
                        for video in result.get('playlist_entries', []):
                            video_id = video.get('id')
                            if video_id and video_id in video_formats:
                                video['available_formats'] = video_formats[video_id]
                                video['formats_analyzed'] = True
                                formats_added += 1
                        
                        task.logs.append(f"[DEBUG] {formats_added} vidéos ont reçu leurs formats")
                    else:
                        result = self._parse_video_info(data)
                    
                    # Log des formats parsés
                    task.logs.append(f"[INFO] {len(result.get('video_formats', []))} formats vidéo")
                    task.logs.append(f"[INFO] {len(result.get('audio_formats', []))} formats audio")
                    task.logs.append(f"[INFO] {len(result.get('combined_formats', []))} formats combinés")
                    
                    task.result = result
                    task.status = "completed"
                else:
                    task.status = "error"
                    task.error_message = "Erreur lors de l'analyse"
                    task.logs.append(f"[ERROR] Code de retour: {process.returncode}")
                    
            except subprocess.TimeoutExpired:
                process.kill()
                task.status = "error"
                task.error_message = "Timeout - L'analyse a pris trop de temps (1 heure max)"
                task.logs.append("[ERROR] Timeout après 1 heure")
            except json.JSONDecodeError as e:
                task.status = "error"
                task.error_message = f"Erreur de parsing JSON: {str(e)}"
                task.logs.append(f"[ERROR] Réponse invalide de yt-dlp: {str(e)}")
            except UnicodeDecodeError as e:
                task.status = "error"
                task.error_message = "Erreur d'encodage - caractères spéciaux non supportés"
                task.logs.append(f"[ERROR] Problème d'encodage: {str(e)}")
            except OSError as e:
                task.status = "error"
                task.error_message = f"Erreur système: {str(e)}"
                task.logs.append(f"[ERROR] Erreur système: {str(e)}")
                
        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.logs.append(f"[ERROR] {type(e).__name__}: {str(e)}")
    
    def get_analysis_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Récupère la progression d'une analyse.
        """
        with self.lock:
            task = self.active_analyses.get(task_id)
        
        if not task:
            return {
                "success": False,
                "error": "Tâche non trouvée"
            }
        
        # Calculer le temps écoulé
        elapsed_time = time.time() - task.start_time
        
        return {
            "success": True,
            "status": task.status,
            "logs": task.logs[-50:],  # Dernières 50 lignes
            "result": task.result,
            "error_message": task.error_message,
            "elapsed_time": elapsed_time
        }
    
    def cancel_analysis(self, task_id: str) -> bool:
        """
        Annule une analyse en cours.
        """
        with self.lock:
            task = self.active_analyses.get(task_id)
        
        if not task:
            return False
        
        if task.status not in ("pending", "analyzing"):
            return False
        
        try:
            if task.process:
                task.process.terminate()
                try:
                    task.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    task.process.kill()
            task.status = "cancelled"
            task.logs.append("[INFO] Analyse annulée par l'utilisateur")
            return True
        except Exception as e:
            task.logs.append(f"[ERROR] Erreur lors de l'annulation: {str(e)}")
            return False
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL YouTube et retourne toutes les métadonnées.
        Équivalent à yt-dlp -J URL
        """
        # Essayer d'abord l'API Python yt-dlp (meilleure gestion de Deno)
        if YTDLP_AVAILABLE:
            try:
                return self._analyze_with_api(url)
            except Exception as e:
                print(f"API Python failed, fallback to subprocess: {e}")
        
        # Fallback vers subprocess
        return self._analyze_with_subprocess(url)
    
    def _analyze_with_api(self, url: str) -> Dict[str, Any]:
        """Utilise l'API Python yt_dlp pour l'analyse."""
        # Première passe : détecter le type de contenu rapidement
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Rapide pour détecter le type
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Vérifier si c'est une playlist
            if info.get('_type') == 'playlist' or ('entries' in info and len(info.get('entries', [])) > 1):
                # C'est une playlist - parser sans limite
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=False)
                    return self._parse_playlist_info_flat(info)
            
            # C'est une vidéo simple - analyse complète
            ydl_opts_full = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts_full) as ydl_full:
                info_full = ydl_full.extract_info(url, download=False)
                return self._parse_video_info(info_full)
    
    def _analyze_with_subprocess(self, url: str) -> Dict[str, Any]:
        """Utilise subprocess comme fallback."""
        # S'assurer que l'environnement est configuré
        self._setup_environment()
        
        try:
            cmd = [
                self.ytdlp_path,
                "-J",
                "--no-warnings",
                "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                url
            ]
            
            # Utiliser les paramètres pour cacher la fenêtre sous Windows
            subprocess_kwargs = self._get_subprocess_kwargs()
            
            print(f"[DEBUG] Exécution: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                **self._get_text_decode_kwargs(),
                timeout=120,  # Augmenté à 120 secondes pour les playlists
                **subprocess_kwargs
            )
            
            print(f"[DEBUG] Return code: {result.returncode}")
            print(f"[DEBUG] Stderr: {result.stderr[:200] if result.stderr else 'None'}")
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Erreur inconnue"
                raise Exception(f"yt-dlp error: {error_msg}")
            
            # Vérifier si Deno a été utilisé
            if 'jsc:deno' in result.stderr or 'Solving JS challenges' in result.stderr:
                print("[DEBUG] ✓ Deno a été utilisé avec succès!")
            else:
                print("[DEBUG] ⚠ Deno n'a pas été utilisé - pistes audio limitées")
            
            data = json.loads(result.stdout)
            
            # Vérifier si c'est une playlist
            if data.get('_type') == 'playlist' or 'entries' in data:
                return self._parse_playlist_info_flat(data)
            
            return self._parse_video_info(data)
            
        except subprocess.TimeoutExpired:
            raise Exception("Timeout lors de l'analyse de l'URL")
        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de parsing JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur d'analyse: {str(e)}")
    
    def _parse_video_info(self, data: Dict) -> Dict[str, Any]:
        """Parse les données JSON de yt-dlp et les structure."""
        
        # Informations générales
        info = {
            "video_id": data.get("id"),
            "title": data.get("title"),
            "uploader": data.get("uploader"),
            "duration": self._format_duration(data.get("duration")),
            "view_count": data.get("view_count"),
            "upload_date": data.get("upload_date"),
            "description": data.get("description"),
            "thumbnail": data.get("thumbnail"),
            "webpage_url": data.get("webpage_url"),
        }
        
        # Formats vidéo et audio
        video_formats = []
        audio_formats = []
        combined_formats = []
        
        for fmt in data.get("formats", []):
            format_info = {
                "format_id": fmt.get("format_id"),
                "ext": fmt.get("ext"),
                "resolution": fmt.get("resolution"),
                "fps": fmt.get("fps"),
                "vcodec": fmt.get("vcodec"),
                "acodec": fmt.get("acodec"),
                "vbr": fmt.get("vbr"),
                "abr": fmt.get("abr"),
                "asr": fmt.get("asr"),
                "filesize": self._format_filesize(fmt.get("filesize") or fmt.get("filesize_approx")),
                "protocol": fmt.get("protocol"),
                "quality": fmt.get("quality_label") or fmt.get("format_note"),
                "language": fmt.get("language"),
                "language_preference": fmt.get("language_preference"),
                "default": fmt.get("default"),
                "original": fmt.get("original"),
            }
            
            # Déterminer le type de format
            vcodec = fmt.get("vcodec") or "none"
            acodec = fmt.get("acodec") or "none"
            format_id = fmt.get("format_id", "")
            protocol = fmt.get("protocol", "")
            resolution = fmt.get("resolution", "")
            width = fmt.get("width", 0)
            height = fmt.get("height", 0)
            
            # Normaliser les codecs
            vcodec_lower = str(vcodec).lower()
            acodec_lower = str(acodec).lower()
            
            # Détecter si c'est un format vidéo
            has_video = (
                vcodec_lower not in ["none", "unknown", "", "null"] and 
                not vcodec_lower.startswith("none")
            ) or (
                resolution and 
                resolution != "unknown" and 
                "x" in str(resolution)
            ) or (
                width and height and int(width) > 0 and int(height) > 0
            )
            
            # Détecter si c'est un format audio
            has_audio = (
                acodec_lower not in ["none", "unknown", "", "null"] and
                not acodec_lower.startswith("none")
            )
            
            # Log pour débogage
            print(f"[DEBUG] Format {format_id}: vcodec={vcodec}, acodec={acodec}, has_video={has_video}, has_audio={has_audio}")
            
            # Déterminer le type de format final
            if has_video and has_audio:
                combined_formats.append(format_info)
            elif has_video and not has_audio:
                video_formats.append(format_info)
            elif has_audio and not has_video:
                audio_formats.append(format_info)
            elif protocol in ["m3u8", "m3u8_native", "http_dash_segments"]:
                video_formats.append(format_info)
            elif format_id:
                combined_formats.append(format_info)
        
        # Trier les formats avec gestion des valeurs None
        def safe_int(value, default=0):
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        video_formats.sort(
            key=lambda x: (
                self._parse_resolution(x.get("resolution") or "0x0"), 
                safe_int(x.get("fps"), 0)
            ), 
            reverse=True
        )
        audio_formats.sort(
            key=lambda x: (
                x.get("language") or "", 
                safe_int(x.get("abr"), 0)
            ), 
            reverse=True
        )
        
        info["video_formats"] = video_formats
        info["audio_formats"] = audio_formats
        info["combined_formats"] = combined_formats
        
        # Si aucun format n'est trouvé, ajouter un message d'information
        total_formats = len(video_formats) + len(audio_formats) + len(combined_formats)
        if total_formats == 0 and data.get("formats"):
            # Les formats existent mais n'ont pas été classés - les ajouter comme combinés
            for fmt in data.get("formats", []):
                format_info = {
                    "format_id": fmt.get("format_id", "unknown"),
                    "ext": fmt.get("ext", "unknown"),
                    "resolution": fmt.get("resolution", "unknown"),
                    "fps": fmt.get("fps"),
                    "vcodec": fmt.get("vcodec"),
                    "acodec": fmt.get("acodec"),
                    "vbr": fmt.get("vbr"),
                    "abr": fmt.get("abr"),
                    "filesize": self._format_filesize(fmt.get("filesize") or fmt.get("filesize_approx")),
                    "protocol": fmt.get("protocol", "unknown"),
                    "quality": fmt.get("quality_label") or fmt.get("format_note", "unknown"),
                }
                combined_formats.append(format_info)
            info["combined_formats"] = combined_formats
        
        # Sous-titres
        subtitles = data.get("subtitles", {})
        automatic_captions = data.get("automatic_captions", {})
        
        info["subtitles"] = self._parse_subtitles(subtitles, "original")
        info["automatic_captions"] = self._parse_subtitles(automatic_captions, "auto")
        
        # Informations supplémentaires pour le frontend
        info["availability"] = data.get("availability", "unknown")
        info["age_limit"] = data.get("age_limit")
        info["is_live"] = data.get("is_live", False)
        
        return info
    
    def _parse_subtitles(self, subs: Dict, sub_type: str) -> List[Dict]:
        """Parse les informations de sous-titres."""
        result = []
        for lang, formats in subs.items():
            formats_list = [f.get("ext") for f in formats if f.get("ext")]
            result.append({
                "language": lang,
                "formats": list(set(formats_list)),
                "type": sub_type
            })
        return result
    
    def _format_duration(self, seconds: Optional[Union[int, float, str]]) -> str:
        """Formate la durée en secondes vers HH:MM:SS."""
        if not seconds:
            return "00:00"
        try:
            # Gérer les différents types d'entrée
            if isinstance(seconds, str):
                seconds = float(seconds)
            # Convertir en entier pour éviter les problèmes avec les floats
            seconds = int(float(seconds))
            if seconds < 0:
                return "00:00"
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"
        except (ValueError, TypeError):
            return "00:00"
    
    def _format_filesize(self, size: Optional[Union[int, float, str]]) -> str:
        """Formate la taille en bytes vers format lisible."""
        if not size:
            return "N/A"
        try:
            # Gérer les différents types d'entrée
            if isinstance(size, str):
                size = float(size)
            size = float(size)
            if size <= 0:
                return "N/A"
            for unit in ['B', 'KiB', 'MiB', 'GiB']:
                if size < 1024:
                    return f"{size:.2f}{unit}"
                size /= 1024
            return f"{size:.2f}TiB"
        except (ValueError, TypeError):
            return "N/A"
    
    def _parse_resolution(self, resolution: str) -> int:
        """Parse une résolution et retourne le nombre de pixels."""
        if not resolution or resolution == "unknown":
            return 0
        try:
            if "x" in str(resolution):
                parts = str(resolution).split("x")
                if len(parts) == 2:
                    w = int(parts[0]) if parts[0].isdigit() else 0
                    h = int(parts[1]) if parts[1].isdigit() else 0
                    return w * h
        except:
            pass
        return 0
    
    def start_download(self, url: str, options: Dict[str, Any]) -> str:
        """
        Démarre un téléchargement avec les options spécifiées.
        Retourne l'ID de la tâche.
        """
        task_id = str(uuid.uuid4())
        
        output_dir = self._resolve_output_dir(options)

        # Construire la commande yt-dlp
        cmd = [self.ytdlp_path, "--newline", "--progress", "--no-warnings"]
        
        # Optimisations réseau pour compatibilité Windows 10+
        # Forcer IPv4 pour éviter les problèmes de résolution DNS IPv6
        cmd.extend(["--force-ipv4"])
        # Timeout augmenté pour les connexions lentes
        cmd.extend(["--socket-timeout", "60"])
        # Retries significativement augmentés pour les connexions instables
        cmd.extend(["--retries", "infinite", "--fragment-retries", "infinite"])
        # Continuer même en cas d'erreurs de fragments
        cmd.extend(["--skip-unavailable-fragments"])
        # Réduire les fragments concurrents pour les PC avec peu de ressources
        cmd.extend(["--concurrent-fragments", "3"])
        # Ajouter des options pour contourner les problèmes de pare-feu/proxy
        cmd.extend(["--no-check-certificate"])
        # Permettre la reprise des téléchargements interrompus
        cmd.extend(["--continue"])
        # Ignorer les erreurs non critiques pour continuer le téléchargement
        cmd.extend(["--ignore-errors"])
        # Délai entre les retries pour éviter la saturation
        cmd.extend(["--retry-sleep", "10"])
        
        # Options pour les playlists
        cmd.extend(["--yes-playlist"])  # Toujours télécharger les playlists

        # Incrustation des sous-titres (hardcoding/burn-in)
        # Cette option nécessite un traitement FFmpeg après le téléchargement
        burn_subs = options.get("burn_subs", False)
        write_auto_subs = options.get("write_auto_subs", False)
        write_subs = options.get("write_subs", False)
        sub_langs = options.get("sub_langs") or []
        burn_subtitle_lang = options.get("burn_subtitle_lang", None)  # Sous-titre spécifique à incruster

        # Options de format
        video_format = options.get("video_format")
        audio_format = options.get("audio_format")

        # Déterminer le mode: sous-titres uniquement ou avec vidéo
        # Si aucun format n'est sélectionné mais des sous-titres sont demandés,
        # passer automatiquement en mode sous-titres uniquement
        subs_only = options.get("subs_only", False)
        if not subs_only and not video_format and not audio_format and (write_subs or write_auto_subs):
            subs_only = True

        # Si mode sous-titres uniquement, on saute le téléchargement vidéo
        if subs_only:
            cmd.append("--skip-download")
        else:
            # Mode normal avec vidéo
            if video_format and audio_format:
                cmd.extend(["-f", f"{video_format}+{audio_format}"])
            elif video_format:
                cmd.extend(["-f", video_format])
            elif audio_format:
                cmd.extend(["-f", audio_format])
            else:
                # Aucun format sélectionné: utiliser le meilleur format par défaut
                # (nécessaire pour burn_subs ou téléchargement normal)
                cmd.extend(["-f", "best"])

        # Pour éviter les erreurs 429, on télécharge toujours les sous-titres séparément
        # après la vidéo, sauf si l'utilisateur ne demande pas de sous-titres du tout.
        # Cela utilise la même logique robuste que le mode hardcode.
        download_subs_in_main = False

        # Si l'utilisateur demande l'incrustation mais pas le téléchargement de sous-titres,
        # on force les sous-titres auto pour rendre le hardcode possible.
        if burn_subs and not (write_subs or write_auto_subs):
            write_auto_subs = True
        # En hardcode, on active aussi les sous-titres auto en fallback
        # si les sous-titres "originaux" sont rate-limités (HTTP 429).
        if burn_subs and write_subs and not write_auto_subs:
            write_auto_subs = True

        # Sous-titres - téléchargés séparément après la vidéo pour éviter 429
        # On ne les télécharge plus dans le processus principal
        if download_subs_in_main and write_subs:
            cmd.append("--write-subs")
        if download_subs_in_main and write_auto_subs:
            cmd.append("--write-auto-sub")
        if download_subs_in_main and (write_subs or write_auto_subs):
            if sub_langs:
                cmd.extend(["--sub-langs", ",".join(sub_langs)])
            cmd.extend(["--sleep-requests", "2", "--retry-sleep", "2"])
            cmd.extend(["--sub-format", "srt"])
            cmd.extend(["--convert-subs", "srt"])
        
        # Thumbnail
        if options.get("embed_thumbnail"):
            cmd.append("--embed-thumbnail")
        
        # Section de téléchargement
        if options.get("download_sections"):
            cmd.extend(["--download-sections", options["download_sections"]])
        
        # Extraction audio uniquement
        if options.get("extract_audio"):
            cmd.extend(["-x", "--audio-format", options.get("audio_format_out", "mp3")])
        
        # Dossier de sortie
        cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])
        
        # URL
        cmd.append(url)
        
        # Créer la tâche
        task = DownloadTask(id=task_id, url=url)
        task.output_dir = output_dir
        task.burn_subs = burn_subs
        task.requested_sub_langs = sub_langs
        task.requested_write_subs = write_subs
        task.requested_write_auto_subs = write_auto_subs
        task.subs_only = subs_only
        task.progress = {"percent": 0}  # Initialize progress
        task.logs.append(f"[INFO] Dossier de sortie: {output_dir}")
        if subs_only:
            task.logs.append("[INFO] Mode sous-titres uniquement: téléchargement des sous-titres sans vidéo")
        elif burn_subs:
            task.logs.append("[INFO] Mode incrustation: vidéo d'abord, sous-titres brûlés ensuite (anti-429)")
        elif write_subs or write_auto_subs:
            task.logs.append("[INFO] Mode téléchargement séparé: vidéo d'abord, sous-titres SRT ensuite (anti-429)")
        
        # Stocker les options de style des sous-titres si présentes
        if options.get("sub_style"):
            task.sub_style = options["sub_style"]
        
        # Stocker le sous-titre spécifique à incruster si présent
        if burn_subtitle_lang:
            task.burn_subtitle_lang = burn_subtitle_lang
        
        with self.lock:
            self.active_downloads[task_id] = task
        
        # Lancer le processus
        try:
            # Utiliser les paramètres pour cacher la fenêtre sous Windows
            subprocess_kwargs = self._get_subprocess_kwargs()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **self._get_text_decode_kwargs(),
                bufsize=1,
                universal_newlines=True,
                **subprocess_kwargs
            )
            
            task.process = process
            task.status = "downloading"
            
            # Démarrer le thread de lecture de la sortie
            import threading
            threading.Thread(
                target=self._read_output,
                args=(task, task.burn_subs, task.requested_sub_langs),
                daemon=True
            ).start()
            
            return task_id
            
        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            raise
    
    def start_playlist_download(self, playlist_title: str, videos: List[Dict], options: Dict[str, Any]) -> str:
        """
        Démarre le téléchargement d'une playlist avec les formats sélectionnés.
        
        Args:
            playlist_title: Titre de la playlist
            videos: Liste des vidéos avec leurs formats sélectionnés
            options: Options globales de téléchargement
        """
        task_id = str(uuid.uuid4())
        output_dir = self._resolve_output_dir(options)
        
        # Créer la tâche
        task = DownloadTask(id=task_id, url=f"[Playlist] {playlist_title}")
        task.status = "downloading"
        task.total_videos = len(videos)
        task.output_dir = output_dir
        task.logs.append(f"[INFO] Dossier de sortie: {output_dir}")
        
        with self.lock:
            self.active_downloads[task_id] = task
        
        # Lancer le téléchargement dans un thread séparé
        import threading
        thread = threading.Thread(
            target=self._download_playlist_videos,
            args=(task, videos, options)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _download_playlist_videos(self, task: DownloadTask, videos: List[Dict], options: Dict[str, Any]):
        """
        Télécharge chaque vidéo de la playlist avec son format sélectionné.
        """
        total = len(videos)
        output_dir = task.output_dir or self.downloads_dir
        
        for index, video in enumerate(videos, 1):
            if task.status == "cancelled":
                break
            
            # Wait if paused (for playlist downloads)
            while task.status == "paused":
                import time
                time.sleep(0.5)
            
            # If task was paused and resumed, skip already downloaded videos
            if hasattr(task, 'paused_progress') and task.paused_progress:
                # Calculate which video we should be at based on progress
                video_progress = (index / total) * 100
                if video_progress <= task.paused_progress:
                    task.logs.append(f"[INFO] Vidéo {index}/{total} déjà téléchargée, passage")
                    continue
            
            video_url = video.get("url")
            # Ensure we're using the YouTube URL, not redirect URLs
            if video_url and "videoplayback" in video_url:
                # Extract video ID from redirect URL or use the ID field
                video_id = video.get("id")
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    # Try to extract video ID from the redirect URL
                    import re
                    id_match = re.search(r'[&?]id=([^&]+)', video_url)
                    if id_match:
                        video_url = f"https://www.youtube.com/watch?v={id_match.group(1)}"
            format_id = video.get("format_id")
            video_id = video.get("id", "unknown")
            
            task.logs.append(f"[INFO] Téléchargement de la vidéo {index}/{total}: {video_id}")
            task.current_video = index
            
            try:
                # Construire la commande pour cette vidéo
                cmd = [self.ytdlp_path, "--newline", "--progress", "--no-warnings"]
                
                # Optimisations réseau pour compatibilité Windows 10+
                cmd.extend(["--force-ipv4"])
                cmd.extend(["--socket-timeout", "60"])
                cmd.extend(["--retries", "infinite", "--fragment-retries", "infinite"])
                cmd.extend(["--skip-unavailable-fragments"])
                cmd.extend(["--concurrent-fragments", "3"])
                cmd.extend(["--no-check-certificate"])
                # Remove --continue flag for playlist downloads to avoid "already downloaded" issues
                # cmd.extend(["--continue"])
                cmd.extend(["--ignore-errors"])
                cmd.extend(["--retry-sleep", "10"])
                cmd.extend(["--no-overwrites"])
                
                # Format spécifique ou meilleur format par défaut
                if format_id:
                    cmd.extend(["-f", format_id])
                else:
                    cmd.extend(["-f", "best"])
                
                # Options globales
                write_auto_subs = options.get("write_auto_subs", False)
                write_subs = options.get("write_subs", False)
                sub_langs = options.get("sub_langs") or []
                
                # Section de téléchargement (extract)
                if options.get("download_sections"):
                    cmd.extend(["--download-sections", options["download_sections"]])
                
                if write_subs:
                    cmd.append("--write-subs")
                if write_auto_subs:
                    cmd.append("--write-auto-sub")
                if write_subs or write_auto_subs:
                    if sub_langs:
                        cmd.extend(["--sub-langs", ",".join(sub_langs)])
                    cmd.extend(["--sub-format", "srt"])
                    cmd.extend(["--convert-subs", "srt"])
                
                if options.get("embed_thumbnail"):
                    cmd.append("--embed-thumbnail")
                
                if options.get("extract_audio"):
                    cmd.extend(["-x", "--audio-format", "mp3"])
                
                # Dossier de sortie - use video ID in filename to avoid conflicts
                cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])
                # Add --id flag to include video ID in filename for better uniqueness
                cmd.append("--id")
                
                # URL
                cmd.append(video_url)
                
                # Exécuter le téléchargement
                subprocess_kwargs = self._get_subprocess_kwargs()
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    **self._get_text_decode_kwargs(),
                    bufsize=1,
                    universal_newlines=True,
                    **subprocess_kwargs
                )
                
                # Store the process in the task for pause/resume functionality
                task.process = process
                
                # Lire la sortie
                for line in process.stdout:
                    # Check if paused during download
                    if task.status == "paused":
                        task.logs.append(f"[INFO] Téléchargement interrompu par pause")
                        process.terminate()
                        process.wait(timeout=2)
                        break
                    line = line.strip()
                    if line:
                        task.logs.append(line)
                        self._parse_progress_line(task, line)
                
                process.wait()
                
                # Only mark as failed if not paused
                if task.status != "paused":
                    if process.returncode == 0:
                        task.logs.append(f"[SUCCESS] Vidéo {index}/{total} téléchargée avec succès")
                        latest_file = self._find_latest_media_file_in_dir(output_dir, min_ctime=task.created_at)
                        if latest_file:
                            self._register_download_file(latest_file)
                    else:
                        task.logs.append(f"[ERROR] Échec du téléchargement de la vidéo {index}/{total}")
                
            except Exception as e:
                task.logs.append(f"[ERROR] Erreur lors du téléchargement de {video_id}: {str(e)}")
        
        # Marquer comme terminé seulement si pas en pause
        if task.status != "cancelled" and task.status != "paused":
            task.status = "completed"
            task.progress = 100
            # Count successful downloads by checking logs for success messages
            success_count = sum(1 for log in task.logs if "[SUCCESS] Vidéo" in log and "téléchargée avec succès" in log)
            failed_count = total - success_count
            if failed_count == 0:
                task.logs.append(f"[SUCCESS] Playlist téléchargée - {total} vidéo(s)")
            elif success_count == 0:
                task.logs.append(f"[ERROR] Playlist échouée - {failed_count} vidéo(s) n'ont pas pu être téléchargées")
            else:
                task.logs.append(f"[PARTIAL] Playlist partiellement téléchargée - {success_count}/{total} vidéo(s) réussies, {failed_count} échouée(s)")
    
    def _read_output(self, task: DownloadTask, burn_subs=False, sub_langs=None):
        """Lit la sortie du processus yt-dlp et met à jour la progression."""
        if not task.process or not task.process.stdout:
            return
        effective_sub_langs = sub_langs or task.requested_sub_langs or []
        
        for line in task.process.stdout:
            # Check if paused during download (before process completes)
            if task.status == "paused":
                task.logs.append(f"[INFO] Téléchargement interrompu par pause")
                task.process.terminate()
                task.process.wait(timeout=2)
                break
            line = line.strip()
            if line:
                task.logs.append(line)
                self._parse_progress_line(task, line)
        
        # Attendre la fin du processus
        task.process.wait()
        
        # If paused, don't treat as error - just keep status as paused
        if task.status == "paused":
            return
        
        if task.status != "cancelled":
            if task.process.returncode == 0:
                # Mode sous-titres uniquement: pas de fichier vidéo
                if getattr(task, 'subs_only', False):
                    subtitle_ok = self._download_subtitles_for_hardcode(task, None, effective_sub_langs)
                    if subtitle_ok:
                        task.logs.append("[SUCCESS] Sous-titres téléchargés avec succès.")
                    else:
                        if effective_sub_langs:
                            task.logs.append("[WARNING] Sous-titres non disponibles après retries (429).")
                        else:
                            task.logs.append("[WARNING] Téléchargement de sous-titres ignoré: aucune langue sélectionnée.")
                    task.status = "completed"
                else:
                    # Mode normal avec vidéo
                    if not task.output_file or not os.path.exists(task.output_file):
                        task.output_file = self._find_latest_media_file_in_dir(task.output_dir or self.downloads_dir, min_ctime=task.created_at)
                    # Si incrustation demandée ou sous-titres séparés demandés, télécharger les sous-titres
                    if burn_subs or (task.requested_write_subs or task.requested_write_auto_subs):
                        subtitle_ok = self._download_subtitles_for_hardcode(task, task.output_file, effective_sub_langs)
                        if burn_subs:
                            # Mode incrustation
                            if subtitle_ok:
                                self._burn_subtitles(task, effective_sub_langs, task.output_dir or self.downloads_dir)
                            else:
                                if effective_sub_langs:
                                    task.logs.append("[WARNING] Sous-titres non disponibles après retries (429). Vidéo conservée sans incrustation.")
                                else:
                                    task.logs.append("[WARNING] Incrustation ignorée: sélectionnez au moins une langue de sous-titres.")
                                task.status = "completed"
                        else:
                            # Mode sous-titres séparés
                            if subtitle_ok:
                                task.logs.append("[SUCCESS] Sous-titres téléchargés séparément avec succès.")
                                # Enregistrer les fichiers de sous-titres dans l'index
                                found_subs = self._find_subtitle_files(task.output_dir or self.downloads_dir, effective_sub_langs, task.created_at)
                                for sub_file in found_subs:
                                    self._register_download_file(sub_file)
                            else:
                                if effective_sub_langs:
                                    task.logs.append("[WARNING] Sous-titres non disponibles après retries (429).")
                                else:
                                    task.logs.append("[WARNING] Téléchargement de sous-titres ignoré: aucune langue sélectionnée.")
                            if task.output_file and os.path.isfile(task.output_file):
                                self._register_download_file(task.output_file)
                            task.status = "completed"
                    else:
                        if task.output_file and os.path.isfile(task.output_file):
                            self._register_download_file(task.output_file)
                        task.status = "completed"
            else:
                subtitle_rate_limited = any(
                    ("Unable to download video subtitles" in log) or ("HTTP Error 429" in log)
                    for log in task.logs[-100:]
                )
                if subtitle_rate_limited:
                    if not task.output_file or not os.path.exists(task.output_file):
                        task.output_file = self._find_latest_media_file_in_dir(task.output_dir or self.downloads_dir, min_ctime=task.created_at)
                    output_exists = bool(task.output_file and os.path.exists(task.output_file))
                    if output_exists:
                        if burn_subs:
                            task.logs.append("[WARNING] Sous-titres limités (429), tentative d'incrustation avec sous-titres disponibles.")
                            self._burn_subtitles(task, effective_sub_langs, task.output_dir or self.downloads_dir)
                        else:
                            if task.output_file and os.path.isfile(task.output_file):
                                self._register_download_file(task.output_file)
                            task.logs.append("[WARNING] Sous-titres indisponibles (429), vidéo téléchargée sans sous-titres.")
                            task.status = "completed"
                    else:
                        task.status = "error"
                        task.error_message = "Le téléchargement vidéo a échoué (sous-titres limités 429)"
                else:
                    task.status = "error"
                    task.error_message = "Le téléchargement a échoué"
    
    def _classify_error(self, line: str) -> str:
        """
        Classifie les erreurs pour dterminer si elles sont temporaires ou bloquantes.
        
        Retourne:
            "ssl_error": Erreur SSL temporaire (peut tre rcupre)
            "network_error": Erreur rseau temporaire (peut tre rcupre)
            "fragment_error": Erreur de fragment (peut tre rcupre)
            "blocking_error": Erreur bloquante (ncessite une intervention)
            None: Pas une erreur ou erreur inconnue
        """
        line_lower = line.lower()
        
        # SSL errors - typically temporary
        ssl_patterns = [
            "ssl: bad_record_mac",
            "ssl: wrong_version_number",
            "ssl: certificate_verify_failed",
            "ssl: decryption_failed",
            "tls",
            "handshake",
        ]
        for pattern in ssl_patterns:
            if pattern in line_lower:
                return "ssl_error"
        
        # Network errors - typically temporary
        network_patterns = [
            "connection reset",
            "connection timed out",
            "timeout",
            "network is unreachable",
            "no route to host",
            "temporary failure",
            "503 service unavailable",
            "502 bad gateway",
            "504 gateway timeout",
        ]
        for pattern in network_patterns:
            if pattern in line_lower:
                return "network_error"
        
        # Fragment errors - can be recovered
        fragment_patterns = [
            "fragment",
            "download interrupted",
            "incomplete",
        ]
        for pattern in fragment_patterns:
            if pattern in line_lower:
                return "fragment_error"
        
        # Blocking errors - cannot be recovered automatically
        blocking_patterns = [
            "404 not found",
            "429 too many requests",
            "403 forbidden",
            "authentication required",
            "video not available",
            "private video",
            "geo-restricted",
            "copyright",
        ]
        for pattern in blocking_patterns:
            if pattern in line_lower:
                return "blocking_error"
        
        return None

    def _burn_subtitles(self, task: DownloadTask, sub_langs, downloads_dir):
        """Incruste les sous-titres dans la vidéo via FFmpeg."""
        try:
            task.status = "burning_subs"
            task.progress = {"percent": 50, "status": "Incrustation en cours"}  # Set progress to 50% during burning
            task.logs.append("[INFO] Incrustation des sous-titres en cours...")

            # Chercher le fichier vidéo téléchargé dans le dossier downloads
            video_file = None
            for filename in os.listdir(downloads_dir):
                if filename.endswith(('.mp4', '.mkv', '.webm')) and not filename.endswith('_burned.mp4'):
                    filepath = os.path.join(downloads_dir, filename)
                    # Vérifier si c'est le fichier le plus récent
                    if video_file is None or os.path.getctime(filepath) > os.path.getctime(video_file):
                        video_file = filepath

            if not video_file or not os.path.exists(video_file):
                task.logs.append("[ERROR] Fichier vidéo non trouvé pour incrustation")
                task.status = "completed"
                return

            task.logs.append(f"[INFO] Vidéo trouvée: {os.path.basename(video_file)}")

            # Chercher le fichier de sous-titres
            base_name = os.path.splitext(video_file)[0]
            sub_file = None
            
            # Si un sous-titre spécifique est demandé pour l'incrustation, utiliser celui-ci
            burn_lang = getattr(task, 'burn_subtitle_lang', None)
            if burn_lang:
                potential_sub = f"{base_name}.{burn_lang}.srt"
                if os.path.exists(potential_sub):
                    sub_file = potential_sub
                    task.logs.append(f"[INFO] Fichier sous-titres sélectionné pour incrustation: {os.path.basename(sub_file)}")
                else:
                    task.logs.append(f"[WARNING] Sous-titre spécifié ({burn_lang}) non trouvé, recherche d'alternative...")
            
            # Si pas de sous-titre spécifique ou non trouvé, chercher dans les langues demandées
            if not sub_file:
                for lang in sub_langs:
                    potential_sub = f"{base_name}.{lang}.srt"
                    if os.path.exists(potential_sub):
                        sub_file = potential_sub
                        task.logs.append(f"[INFO] Fichier sous-titres trouvé: {os.path.basename(sub_file)}")
                        break

            if not sub_file:
                # Chercher n'importe quel fichier srt
                for filename in os.listdir(downloads_dir):
                    if filename.endswith('.srt'):
                        sub_file = os.path.join(downloads_dir, filename)
                        task.logs.append(f"[INFO] Fichier sous-titres alternatif trouvé: {filename}")
                        break

            if not sub_file:
                task.logs.append("[WARNING] Fichier de sous-titres non trouvé, incrustation ignorée")
                task.status = "completed"
                return

            # Créer le fichier de sortie temporaire
            output_file = f"{base_name}_burned.mp4"

            # Récupérer les options de style personnalisées
            sub_style = getattr(task, 'sub_style', None) or {}

            # Couleurs par défaut
            def hex_to_ass_color(hex_color):
                """Convertit #RRGGBB en &HBBGGRR00 pour ASS."""
                hex_color = hex_color.lstrip('#')
                r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
                return f"&H00{b}{g}{r}".upper()

            color = hex_to_ass_color(sub_style.get('color', '#ffffff'))
            outline_color = hex_to_ass_color(sub_style.get('outline_color', '#000000'))
            font_size = sub_style.get('font_size', 28)
            position = sub_style.get('position', 85)  # Défaut: bas (85%)
            outline = sub_style.get('outline', 3)
            font_style = sub_style.get('font_style', 1)  # 0=normal, 1=gras, 2=italique

            # Style bold/italic
            bold = "-1" if font_style == 1 else "0"
            italic = "-1" if font_style == 2 else "0"

            # Utiliser un chemin relatif pour éviter les problèmes d'espaces
            original_dir = os.getcwd()
            video_dir = os.path.dirname(video_file)
            os.chdir(video_dir)
            video_name = os.path.basename(video_file)
            sub_name = os.path.basename(sub_file)
            output_name = os.path.basename(output_file)

            # Créer un fichier de style ASS personnalisé
            # Cette approche est plus fiable que force_style
            ass_style_file = os.path.splitext(sub_name)[0] + "_style.ass"

            # Calculer l'alignment en fonction de la position
            # ASS Alignment: 1=bottom-left, 2=bottom-center, 3=bottom-right
            #                4=middle-left, 5=middle-center, 6=middle-right
            #                7=top-left, 8=top-center, 9=top-right
            if position <= 30:
                alignment = "8"  # Haut-centre
            elif position <= 45:
                alignment = "5"  # Milieu-centre
            elif position <= 60:
                alignment = "5"  # Milieu-centre
            elif position <= 75:
                alignment = "2"  # Bas-centre (plus haut)
            else:
                alignment = "2"  # Bas-centre (standard)

            # Créer le contenu ASS
            ass_content = f"""[Script Info]
Title: Custom Subtitle Style
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{color},{color},{outline_color},&H00000000,{bold},{italic},0,0,100,100,0,0,1,{outline},1,{alignment},10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

            # Lire le fichier SRT et convertir en ASS
            srt_content = self._read_text_file_with_fallback(sub_name)

            # Conversion simple SRT vers ASS
            import re
            ass_events = []

            # Parser les entrées SRT
            srt_pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?:\n\n|\Z)'
            matches = re.findall(srt_pattern, srt_content, re.DOTALL)

            for idx, (num, start, end, text) in enumerate(matches, 1):
                # Convertir le format de temps
                start_ass = start.replace(',', '.')
                end_ass = end.replace(',', '.')
                # Échapper les caractères spéciaux ASS
                text_clean = text.replace('\n', '\\N').replace('<i>', '{\\i1}').replace('</i>', '{\\i0}')
                text_clean = text_clean.replace('<b>', '{\\b1}').replace('</b>', '{\\b0}')

                ass_events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text_clean}")

            # Écrire le fichier ASS
            with open(ass_style_file, 'w', encoding='utf-8') as f:
                f.write(ass_content + '\n'.join(ass_events))

            task.logs.append(f"[INFO] Style sous-titres: taille={font_size}px, position={position}%, align={alignment}, contour={outline}px")

            # Commande FFmpeg avec le fichier ASS
            ffmpeg_path = self._get_binaries_path("ffmpeg.exe")

            cmd = [
                ffmpeg_path,
                "-i", video_name,
                "-vf", f"ass={ass_style_file}",
                "-c:a", "copy",
                "-preset", "fast",
                "-y",
                output_name
            ]

            task.logs.append("[INFO] Lancement de FFmpeg pour incrustation...")

            try:
                # Exécuter FFmpeg avec lecture de la sortie en temps réel
                startupinfo = None
                if sys.platform == 'win32':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    **self._get_text_decode_kwargs(),
                    bufsize=1,
                    universal_newlines=True,
                    startupinfo=startupinfo
                )

                # Lire la sortie en temps réel pour les logs et progression
                import re
                duration_pattern = re.compile(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})')
                time_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
                
                video_duration = None
                
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        task.logs.append(line)
                        
                        # Essayer d'extraire la durée totale
                        if not video_duration:
                            duration_match = duration_pattern.search(line)
                            if duration_match:
                                h, m, s, ms = map(int, duration_match.groups())
                                video_duration = h * 3600 + m * 60 + s + ms / 100
                        
                        # Essayer d'extraire le temps actuel
                        if video_duration:
                            time_match = time_pattern.search(line)
                            if time_match:
                                h, m, s, ms = map(int, time_match.groups())
                                current_time = h * 3600 + m * 60 + s + ms / 100
                                percent = (current_time / video_duration) * 100
                                task.progress = {
                                    "percent": min(50 + percent / 2, 99),  # De 50% à 99%
                                    "status": "Incrustation en cours"
                                }

                process.wait()

                # Revenir au répertoire original
                os.chdir(original_dir)

                if process.returncode == 0:
                    # Remplacer le fichier original par celui avec sous-titres incrustés
                    if os.path.exists(output_file):
                        os.remove(video_file)
                        os.rename(output_file, video_file)
                        task.output_file = video_file
                        self._register_download_file(task.output_file)
                        task.logs.append("[SUCCESS] Sous-titres incrustés avec succès!")
                    else:
                        task.logs.append("[ERROR] Fichier de sortie non créé")
                else:
                    error_msg = task.logs[-10] if task.logs else "Erreur inconnue"
                    task.logs.append(f"[ERROR] Échec incrustation FFmpeg")
                    if os.path.exists(output_file):
                        os.remove(output_file)
            except Exception as e:
                # Revenir au répertoire original en cas d'erreur
                os.chdir(original_dir)
                raise e

            task.status = "completed"
            task.progress = {"percent": 100, "status": "Terminé"}  # Set progress to 100% when completed

        except Exception as e:
            task.logs.append(f"[ERROR] Exception lors de l'incrustation: {str(e)}")
            import traceback
            task.logs.append(traceback.format_exc())
            task.status = "completed"
    
    def _parse_progress_line(self, task: DownloadTask, line: str):
        """Parse une ligne de progression yt-dlp."""
        # Pattern: [download] 45.3% of 202.47MiB at 5.20MiB/s ETA 00:30
        match = re.search(
            r'\[download\]\s+(\d+\.?\d*)%\s+of\s+(\S+)\s+at\s+(\S+)\s+ETA\s+(\S+)',
            line
        )
        
        if match:
            task.progress = {
                "percent": float(match.group(1)),
                "total_size": match.group(2),
                "speed": match.group(3),
                "eta": match.group(4)
            }
        elif "Destination:" in line:
            task.output_file = line.split("Destination:", 1)[1].strip()
        elif "Merging formats into" in line:
            task.output_file = line.split("\"", 2)[1] if "\"" in line else None
            task.status = "finalizing"
        elif "Extracting audio" in line:
            task.progress = task.progress or {}
            task.progress["status"] = "extracting_audio"
        elif "Converting video" in line or "Converting audio" in line:
            task.status = "finalizing"
        elif "[download] 100%" in line:
            task.progress = task.progress or {}
            task.progress["percent"] = 100
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retourne la progression d'une tâche."""
        with self.lock:
            task = self.active_downloads.get(task_id)
        
        if not task:
            return None
        
        return {
            "id": task.id,
            "status": task.status,
            "progress": task.progress,
            "logs": task.logs[-50:],  # Dernières 50 lignes
            "output_file": task.output_file,
            "error_message": task.error_message
        }
    
    def cancel_download(self, task_id: str) -> bool:
        """Annule un téléchargement en cours."""
        with self.lock:
            task = self.active_downloads.get(task_id)
        
        if not task:
            return False
        
        # Pour les playlists, il n'y a pas de process direct
        # On définit simplement le statut sur "cancelled"
        # La boucle dans _download_playlist_videos vérifiera ce statut
        if task.process:
            try:
                task.process.terminate()
            except:
                pass
        
        task.status = "cancelled"
        return True
    
    def pause_download(self, task_id: str) -> bool:
        """Met en pause un téléchargement en cours."""
        with self.lock:
            task = self.active_downloads.get(task_id)
        
        if not task:
            return False
        
        try:
            # Store the current progress for resume
            progress = getattr(task, 'progress', 0)
            task.paused_progress = progress
            
            # Set status to paused - the download loop will handle stopping
            task.status = "paused"
            task.logs.append(f"[INFO] Téléchargement mis en pause à {progress}%")
            return True
        except Exception as e:
            task.logs.append(f"[ERROR] Impossible de mettre en pause: {str(e)}")
            return False
    
    def resume_download(self, task_id: str) -> bool:
        """Reprend un téléchargement en pause."""
        with self.lock:
            task = self.active_downloads.get(task_id)
        
        if not task:
            return False
        
        try:
            # Set status back to downloading
            task.status = "downloading"
            paused_progress = getattr(task, 'paused_progress', 0)
            task.logs.append(f"[INFO] Reprise du téléchargement depuis {paused_progress}%")
            
            # For playlists, the loop will automatically continue
            # For single videos, we need to restart the download
            is_playlist = getattr(task, 'is_playlist', False)
            
            if not is_playlist and hasattr(task, 'url') and task.url:
                # Restart single video download with --continue flag
                import threading
                thread = threading.Thread(
                    target=self._restart_download,
                    args=(task,)
                )
                thread.daemon = True
                thread.start()
            
            return True
        except Exception as e:
            task.logs.append(f"[ERROR] Impossible de reprendre: {str(e)}")
            return False
    
    def _restart_download(self, task: DownloadTask):
        """Relance un téléchargement avec les mêmes paramètres."""
        try:
            # Reconstruct the download command with the same parameters
            cmd = [self.ytdlp_path, "--newline", "--progress", "--no-warnings"]
            
            # Optimisations réseau
            cmd.extend(["--force-ipv4"])
            cmd.extend(["--socket-timeout", "60"])
            cmd.extend(["--retries", "infinite", "--fragment-retries", "infinite"])
            cmd.extend(["--skip-unavailable-fragments"])
            cmd.extend(["--concurrent-fragments", "3"])
            cmd.extend(["--no-check-certificate"])
            cmd.extend(["--continue"])  # Important: resume from where it left off
            cmd.extend(["--ignore-errors"])
            cmd.extend(["--retry-sleep", "10"])
            
            # Use the same format and options that were stored
            if hasattr(task, 'video_format') and task.video_format:
                cmd.extend(["-f", task.video_format])
            elif hasattr(task, 'audio_format') and task.audio_format:
                cmd.extend(["-f", task.audio_format])
            else:
                cmd.extend(["-f", "best"])
            
            # Output directory
            output_dir = task.output_dir or self.downloads_dir
            cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])
            
            # URL
            cmd.append(task.url)
            
            # Execute the download
            subprocess_kwargs = self._get_subprocess_kwargs()
            task.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **self._get_text_decode_kwargs(),
                bufsize=1,
                universal_newlines=True,
                **subprocess_kwargs
            )
            
            # Read the output
            self._read_output(task)
            
            task.process.wait()
            
            if task.process.returncode == 0:
                task.status = "completed"
                task.logs.append("[SUCCESS] Téléchargement terminé avec succès")
                latest_file = self._find_latest_media_file_in_dir(output_dir, min_ctime=task.created_at)
                if latest_file:
                    self._register_download_file(latest_file)
            else:
                task.status = "error"
                task.error_message = "Le téléchargement a échoué"
                task.logs.append("[ERROR] Le téléchargement a échoué")
                
        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.logs.append(f"[ERROR] Erreur lors de la reprise: {str(e)}")
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Nettoie les anciennes tâches terminées."""
        # TODO: Implémenter le nettoyage des anciennes tâches
        pass
    
    def _parse_playlist_info(self, data: Dict) -> Dict[str, Any]:
        """Parse les données d'une playlist et retourne la première vidéo avec info playlist."""
        entries = data.get("entries", [])
        
        if not entries:
            raise Exception("Playlist vide ou inaccessible")
        
        # Prendre la première vidéo pour l'analyse détaillée
        first_video = None
        for entry in entries:
            if entry:
                first_video = entry
                break
        
        if not first_video:
            raise Exception("Aucune vidéo trouvée dans la playlist")
        
        # Parser la première vidéo normalement
        video_info = self._parse_video_info(first_video)
        
        # Ajouter les informations de playlist
        video_info["is_playlist"] = True
        video_info["playlist_title"] = data.get("title", "Playlist")
        video_info["playlist_uploader"] = data.get("uploader", "")
        video_info["playlist_count"] = len(entries)
        video_info["playlist_entries"] = [
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "duration": self._format_duration(e.get("duration")),
                "uploader": e.get("uploader"),
                "url": f"https://www.youtube.com/watch?v={e.get('id')}" if e.get('id') else None,
                "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg" if e.get('id') else None
            }
            for e in entries if e  # Toutes les entrées
        ]
        video_info["title"] = f"[PLAYLIST] {data.get('title', 'Playlist')} ({len(entries)} vidéos)"
        
        return video_info
    
    def _parse_playlist_info_flat(self, data: Dict) -> Dict[str, Any]:
        """Parse les données d'une playlist avec extract_flat (plus rapide)."""
        entries = [e for e in data.get("entries", []) if e is not None]
        
        if not entries:
            raise Exception("Playlist vide ou inaccessible")
        
        # Compter le nombre total de vidéos
        total_videos = len(entries)
        
        # Déterminer si c'est un résultat de recherche
        is_search = data.get('extractor_key', '').lower().startswith('youtube:search') or \
                   data.get('extractor', '').lower().startswith('youtube:search') or \
                   data.get('_type') == 'search'
        
        # Prendre la première vidéo pour obtenir des informations de base
        first_entry = entries[0]
        
        # Titre de la playlist ou de la recherche
        if is_search:
            title = f"Résultats de recherche : {data.get('title', 'Recherche')} ({total_videos} résultats)"
            uploader = "Recherche Multi-plateforme"
        else:
            title = f"[PLAYLIST] {data.get('title', 'Playlist')} ({total_videos} vidéos)"
            uploader = data.get("uploader", "Chaîne inconnue")
        
        # Créer des informations de base
        info = {
            "video_id": first_entry.get("id"),
            "title": title,
            "uploader": uploader,
            "duration": "--:--",
            "view_count": 0,
            "upload_date": "",
            "description": f"Contient {total_videos} éléments",
            "thumbnail": f"https://i.ytimg.com/vi/{first_entry.get('id')}/mqdefault.jpg" if first_entry.get('id') else None,
            "webpage_url": data.get("webpage_url", ""),
            "is_playlist": True,
            "is_search": is_search,
            "playlist_title": data.get("title", "Playlist"),
            "playlist_uploader": data.get("uploader", ""),
            "playlist_count": total_videos,
            "playlist_entries": [
                {
                    "id": e.get("id"),
                    "title": e.get("title", "Sans titre"),
                    "duration": self._format_duration(e.get("duration")),
                    "uploader": e.get("uploader", ""),
                    "url": e.get("url") or (f"https://www.youtube.com/watch?v={e.get('id')}" if e.get('id') else None),
                    "thumbnail": e.get("thumbnail") or (f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg" if e.get('id') else None)
                }
                for e in entries
            ],
            # Formats vides pour les playlists (seront déterminés au téléchargement)
            "video_formats": [],
            "audio_formats": [],
            "combined_formats": [],
            "subtitles": {},
            "automatic_captions": {}
        }
        
        return info
    
    def analyze_playlist_video(self, url: str, parent_task_id: str) -> str:
        """
        Analyse une vidéo individuelle d'une playlist.
        Retourne l'ID de la tâche créée.
        """
        task_id = str(uuid.uuid4())
        
        task = AnalysisTask(task_id, url)
        task.status = "pending"
        
        with self.lock:
            self.active_analyses[task_id] = task
        
        # Lancer l'analyse dans un thread séparé
        thread = threading.Thread(
            target=self._analyze_playlist_video_task,
            args=(task_id, url, parent_task_id)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _analyze_playlist_video_task(self, task_id: str, url: str, parent_task_id: str):
        """
        Tâche d'analyse d'une vidéo de playlist avec affichage des formats (comme yt-dlp -F).
        """
        task = self.active_analyses.get(task_id)
        if not task:
            return
        
        task.status = "analyzing"
        task.logs.append(f"[INFO] Analyse des formats pour: {url}")
        
        try:
            # S'assurer que l'environnement est configuré
            self._setup_environment()
            
            # Utiliser -F pour obtenir la liste des formats (comme en ligne de commande)
            cmd = [
                self.ytdlp_path,
                "-F",
                "--no-warnings",
                "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                url
            ]
            
            task.logs.append(f"[CMD] {' '.join(cmd)}")
            
            # Utiliser les paramètres pour cacher la fenêtre sous Windows
            subprocess_kwargs = self._get_subprocess_kwargs()
            
            task.logs.append("[INFO] Exécution de yt-dlp...")
            task.logs.append("")  # Ligne vide pour la lisibilité
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combiner stdout et stderr
                **self._get_text_decode_kwargs(),
                bufsize=1,
                universal_newlines=True,
                **subprocess_kwargs
            )
            
            # Lire la sortie en temps réel et l'ajouter aux logs
            output_lines = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    output_lines.append(line)
                    # Ajouter directement à la console avec le préfixe approprié
                    if '[info]' in line.lower() or 'available formats' in line.lower():
                        task.logs.append(f"[INFO] {line}")
                    elif 'error' in line.lower():
                        task.logs.append(f"[ERROR] {line}")
                    elif 'extracting' in line.lower() or 'downloading' in line.lower():
                        task.logs.append(f"[INFO] {line}")
                    elif 'solving js' in line.lower() or 'deno' in line.lower():
                        task.logs.append(f"[INFO] {line}")
                    else:
                        # Lignes de formats ou autres - les afficher telles quelles
                        task.logs.append(line)
            
            # Attendre la fin du processus
            process.wait()
            
            if process.returncode == 0:
                task.logs.append("")  # Ligne vide
                task.logs.append("[SUCCESS] Analyse des formats terminée")
                
                # Maintenant récupérer les données JSON pour le résultat
                task.logs.append("[INFO] Récupération des métadonnées...")
                
                cmd_json = [
                    self.ytdlp_path,
                    "-J",
                    "--no-warnings",
                    "--force-ipv4",  # Forcer IPv4 pour éviter les problèmes DNS
                    "--socket-timeout", "60",  # Timeout augmenté pour connexions lentes
                    url
                ]
                
                result_json = subprocess.run(
                    cmd_json,
                    capture_output=True,
                    **self._get_text_decode_kwargs(),
                    timeout=120,
                    **subprocess_kwargs
                )
                
                if result_json.returncode == 0:
                    data = json.loads(result_json.stdout)
                    result = self._parse_video_info(data)
                    task.result = result
                    task.status = "completed"
                else:
                    # Si échec JSON, on a quand même les formats affichés
                    task.result = {"video_formats": [], "audio_formats": [], "combined_formats": []}
                    task.status = "completed"
            else:
                raise Exception(f"yt-dlp a retourné le code d'erreur: {process.returncode}")
                
        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.logs.append(f"[ERROR] {type(e).__name__}: {str(e)}")

class HistoryManager:
    """Gestionnaire d'historique pour les recherches et analyses."""
    
    def __init__(self, history_file_path: str, max_items: int = 100):
        self.history_file_path = history_file_path
        self.max_items = max_items
        self.lock = Lock()
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Charge l'historique depuis le fichier JSON."""
        try:
            if not os.path.exists(self.history_file_path):
                return []
            with open(self.history_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    
    def _save_history(self) -> None:
        """Sauvegarde l'historique dans le fichier JSON."""
        try:
            directory = os.path.dirname(self.history_file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save history: {e}")
    
    def add_item(self, query: str, item_type: str = "url", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Ajoute un element a l'historique.
        
        Args:
            query: L'URL ou la requete de recherche
            item_type: "url" ou "search"
            metadata: Metadonnees supplementaires (titre, thumbnail, etc.)
        
        Returns:
            L'element ajoute a l'historique
        """
        with self.lock:
            # Supprimer l'element s'il existe deja
            self.history = [
                item for item in self.history 
                if item.get("query") != query or item.get("type") != item_type
            ]
            
            # Creer le nouvel element
            item = {
                "id": str(uuid.uuid4()),
                "query": query,
                "type": item_type,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            # Ajouter au debut (plus recent d'abord)
            self.history.insert(0, item)
            
            # Limiter le nombre d'elements
            if len(self.history) > self.max_items:
                self.history = self.history[:self.max_items]
            
            # Sauvegarder
            self._save_history()
            
            return item
    
    def get_history(self, item_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recupere l'historique.
        
        Args:
            item_type: Filtrer par type ("url" ou "search"), None pour tous
            limit: Nombre maximum d'elements a retourner
        
        Returns:
            Liste des elements de l'historique
        """
        with self.lock:
            filtered = self.history
            if item_type:
                filtered = [item for item in filtered if item.get("type") == item_type]
            if limit:
                filtered = filtered[:limit]
            return filtered
    
    def delete_item(self, item_id: str) -> bool:
        """
        Supprime un element de l'historique.
        
        Args:
            item_id: L'ID de l'element a supprimer
        
        Returns:
            True si l'element a ete supprime, False sinon
        """
        with self.lock:
            initial_length = len(self.history)
            self.history = [item for item in self.history if item.get("id") != item_id]
            if len(self.history) < initial_length:
                self._save_history()
                return True
            return False
    
    def clear_history(self) -> None:
        """Vide completement l'historique."""
        with self.lock:
            self.history = []
            self._save_history()
    
    def update_item_metadata(self, item_id: str, metadata: Dict) -> bool:
        """
        Met a jour les metadonnees d'un element de l'historique.
        
        Args:
            item_id: L'ID de l'element
            metadata: Les nouvelles metadonnees
        
        Returns:
            True si l'element a ete mis a jour, False sinon
        """
        with self.lock:
            for item in self.history:
                if item.get("id") == item_id:
                    item["metadata"] = {**item.get("metadata", {}), **metadata}
                    self._save_history()
                    return True
            return False

