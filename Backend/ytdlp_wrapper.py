# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
Wrapper pour yt-dlp qui configure correctement l'environnement Deno.
Ce script s'assure que Deno est trouvé et utilisé correctement.
"""
import os
import sys
import subprocess
import json

def setup_environment():
    """Configure l'environnement pour yt-dlp."""
    # Obtenir le dossier Binaries avec recherche dans installation principale
    binaries_dir = get_binaries_dir()

    # Ajouter au PATH
    current_path = os.environ.get('PATH', '')
    if binaries_dir not in current_path:
        os.environ['PATH'] = binaries_dir + os.pathsep + current_path

    # Définir DENO_PATH
    deno_path = os.path.join(binaries_dir, 'deno.exe')
    if os.path.exists(deno_path):
        os.environ['DENO_PATH'] = deno_path

    return binaries_dir

def get_binaries_dir():
    """
    Obtient le chemin du dossier Binaries.
    Cherche d'abord dans le dossier d'installation principal, puis dans _internal.
    """
    # D'abord, essayer le dossier d'installation principal (au-dessus de _internal)
    try:
        if hasattr(sys, '_MEIPASS'):
            install_dir = os.path.dirname(sys._MEIPASS)
            candidate_dir = os.path.join(install_dir, 'Binaries')
            if os.path.exists(candidate_dir):
                return candidate_dir
    except Exception:
        pass

    # Ensuite, essayer le chemin normal (développement)
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_dir, 'Binaries')

def run_ytdlp(args):
    """Exécute yt-dlp avec les arguments fournis."""
    binaries_dir = setup_environment()
    ytdlp_path = os.path.join(binaries_dir, 'yt-dlp.exe')
    
    # Créer STARTUPINFO pour cacher la fenêtre sous Windows
    startupinfo = None
    creationflags = 0
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        # Utiliser CREATE_NO_WINDOW pour cacher complètement la fenêtre console
        from subprocess import CREATE_NO_WINDOW
        creationflags = CREATE_NO_WINDOW
    
    cmd = [ytdlp_path] + args
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    
    return result

if __name__ == '__main__':
    # Passer tous les arguments à yt-dlp
    result = run_ytdlp(sys.argv[1:])
    print(result.stdout, end='')
    print(result.stderr, end='', file=sys.stderr)
    sys.exit(result.returncode)
