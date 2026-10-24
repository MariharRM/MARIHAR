# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
Application de bureau MARIHAR avec PyWebView.
Transforme l'application Flask en logiciel de bureau professionnel.
"""
import base64
import ctypes
import ctypes.wintypes
import os
import sys
import threading
import time
import webview
from app import app

_desktop_state = {"window": None, "allow_close": False}

# Cache des textes traduits — mis a jour par update_quit_texts() depuis JS
_quit_texts_cache = {
    "quit_title":   "Quitter MARIHAR",
    "quit_message": "Voulez-vous vraiment quitter MARIHAR ?",
    "btn_quit":     "Quitter",
    "btn_cancel":   "Annuler",
}


def get_resource_path(relative_path):
    """Chemin absolu vers une ressource (dev + PyInstaller)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def _is_frozen():
    return getattr(sys, "frozen", False)


def _log(msg):
    if not _is_frozen():
        print(msg)


# ---------------------------------------------------------------------------
# Personnalisation de la barre de titre via DWM (Windows 10/11)
# ---------------------------------------------------------------------------

def _apply_titlebar_style(hwnd: int) -> None:
    """
    Applique un style moderne a la barre de titre native :
    - Mode sombre (texte blanc, fond sombre systeme)
    - Couleur de fond personnalisee #0a0818 (Windows 11 uniquement)
    - Couleur du texte blanche (Windows 11 uniquement)
    - Coins arrondis (Windows 11 uniquement)
    Compatible Windows 10 et 11.
    """
    if not hwnd:
        return
    try:
        dwmapi = ctypes.windll.dwmapi
        build  = sys.getwindowsversion().build

        # ── 1. Mode sombre DWM (Win 10 build 17763+) ─────────────────────
        # Rend la barre de titre sombre avec texte blanc.
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val_dark = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(val_dark),
            ctypes.sizeof(val_dark),
        )

        # ── 2. Couleur de fond de la barre (Win 11 build 22000+) ──────────
        # #0a0818 en COLORREF = BGR : R=10, G=8, B=24 -> 0x18080A
        DWMWA_CAPTION_COLOR = 35
        if build >= 22000:
            color_bg = ctypes.c_int(0x18080A)  # #0a0818 en BGR
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(color_bg),
                ctypes.sizeof(color_bg),
            )

        # ── 3. Couleur du texte (Win 11 build 22000+) ─────────────────────
        # Blanc pur #ffffff en COLORREF BGR = 0xFFFFFF
        DWMWA_TEXT_COLOR = 36
        if build >= 22000:
            color_txt = ctypes.c_int(0xFFFFFF)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(color_txt),
                ctypes.sizeof(color_txt),
            )

        # ── 4. Coins arrondis (Win 11 uniquement) ─────────────────────────
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        if build >= 22000:
            corner = ctypes.c_int(DWMWCP_ROUND)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(corner),
                ctypes.sizeof(corner),
            )

        _log(f"[DWM] Barre de titre stylisee (build={build}, hwnd={hwnd})")

    except Exception as exc:
        _log(f"[DWM] Erreur : {exc}")


# ---------------------------------------------------------------------------
# Dialogue de confirmation — design MARIHAR
# ---------------------------------------------------------------------------

def _show_quit_dialog_native(owner_window) -> bool:
    """
    Affiche le dialogue de confirmation stylise MARIHAR via ShowDialog().

    IMPORTANT : on utilise ShowDialog(owner) exactement comme le modele
    original qui fonctionnait — le dialogue s'affiche dans le meme thread
    STA que la fenetre principale pywebview, ce qui evite tout deadlock.
    """
    try:
        import clr  # type: ignore
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        import System.Windows.Forms as WF    # type: ignore
        import System.Drawing as D           # type: ignore
        from System.Drawing import FontStyle # type: ignore
        _log("[DIALOG] WinForms disponible - utilisation du dialogue stylisé")
    except Exception as exc:
        # WinForms indisponible : fallback ctypes
        _log(f"[DIALOG] WinForms non disponible: {exc} - utilisation du fallback ctypes")
        return _ctypes_fallback()

    texts = _quit_texts_cache
    C = D.Color.FromArgb

    # ── Couleurs MARIHAR ──────────────────────────────────────────────────
    BG_DEEP       = C(10,  8, 24)
    BG_CARD       = C(22, 21, 42)
    BG_CARD2      = C(26, 26, 46)
    ACCENT_RED    = C(233, 69, 96)
    ACCENT_GLD    = C(184, 148, 95)
    TEXT_HEAD     = C(245, 240, 255)
    TEXT_BODY     = C(200, 195, 225)
    BTN_CANCEL_BG = C(30, 28, 55)
    BTN_CANCEL_FG = C(220, 215, 245)
    BORDER_SUBTLE = C(55, 50, 90)

    # ── Formulaire ────────────────────────────────────────────────────────
    form = WF.Form()
    form.Text            = "MARIHAR"
    form.FormBorderStyle = WF.FormBorderStyle.FixedDialog
    form.MaximizeBox     = False
    form.MinimizeBox     = False
    form.ShowInTaskbar   = False
    form.StartPosition   = WF.FormStartPosition.CenterParent
    form.ClientSize      = D.Size(440, 220)
    form.BackColor       = BG_DEEP
    form.ForeColor       = TEXT_HEAD
    try:
        form.Font = D.Font("Segoe UI", 9.5)
    except Exception:
        pass

    try:
        ico = get_resource_path("Assets/Logo_marino.ico")
        if os.path.exists(ico):
            form.Icon = D.Icon(ico)
    except Exception:
        pass

    # ── Bande rouge superieure ────────────────────────────────────────────
    strip = WF.Panel()
    strip.Dock      = WF.DockStyle.Top
    strip.Height    = 3
    strip.BackColor = ACCENT_RED
    form.Controls.Add(strip)

    # ── Corps ─────────────────────────────────────────────────────────────
    body = WF.Panel()
    body.BackColor = BG_CARD
    body.Size      = D.Size(440, 217)
    body.Location  = D.Point(0, 3)
    form.Controls.Add(body)

    # ── Logo PNG ──────────────────────────────────────────────────────────
    pic = WF.PictureBox()
    pic.Size      = D.Size(64, 64)
    pic.Location  = D.Point(24, 20)
    pic.SizeMode  = WF.PictureBoxSizeMode.Zoom
    pic.BackColor = D.Color.Transparent
    try:
        png = get_resource_path("Assets/Logo_marino.png")
        if os.path.exists(png):
            pic.Image = D.Image.FromFile(png)
        elif form.Icon is not None:
            pic.Image = form.Icon.ToBitmap()
    except Exception:
        pass
    body.Controls.Add(pic)

    # ── Titre ─────────────────────────────────────────────────────────────
    lbl_title = WF.Label()
    lbl_title.Text      = texts["quit_title"]
    lbl_title.AutoSize  = False
    lbl_title.Size      = D.Size(320, 28)
    lbl_title.Location  = D.Point(102, 22)
    lbl_title.ForeColor = TEXT_HEAD
    lbl_title.BackColor = D.Color.Transparent
    try:
        lbl_title.Font = D.Font("Segoe UI Semibold", 13, FontStyle.Bold)
    except Exception:
        lbl_title.Font = D.Font("Segoe UI", 13, FontStyle.Bold)
    body.Controls.Add(lbl_title)

    # ── Separateur dore ───────────────────────────────────────────────────
    sep = WF.Panel()
    sep.Size      = D.Size(40, 2)
    sep.Location  = D.Point(102, 56)
    sep.BackColor = ACCENT_GLD
    body.Controls.Add(sep)

    # ── Message ───────────────────────────────────────────────────────────
    lbl_msg = WF.Label()
    lbl_msg.Text      = texts["quit_message"]
    lbl_msg.AutoSize  = False
    lbl_msg.Size      = D.Size(320, 44)
    lbl_msg.Location  = D.Point(102, 65)
    lbl_msg.ForeColor = TEXT_BODY
    lbl_msg.BackColor = D.Color.Transparent
    try:
        lbl_msg.Font = D.Font("Segoe UI", 10)
    except Exception:
        pass
    body.Controls.Add(lbl_msg)

    # ── Ligne de separation ───────────────────────────────────────────────
    line = WF.Panel()
    line.Size      = D.Size(440, 1)
    line.Location  = D.Point(0, 140)
    line.BackColor = BORDER_SUBTLE
    body.Controls.Add(line)

    # ── Zone boutons ──────────────────────────────────────────────────────
    btn_zone = WF.Panel()
    btn_zone.Size      = D.Size(440, 76)
    btn_zone.Location  = D.Point(0, 141)
    btn_zone.BackColor = BG_CARD2
    body.Controls.Add(btn_zone)

    # ── Bouton Annuler ────────────────────────────────────────────────────
    btn_cancel = WF.Button()
    btn_cancel.Text         = texts["btn_cancel"]
    btn_cancel.Size         = D.Size(130, 38)
    btn_cancel.Location     = D.Point(164, 18)
    btn_cancel.FlatStyle    = WF.FlatStyle.Flat
    btn_cancel.FlatAppearance.BorderColor = ACCENT_GLD
    btn_cancel.FlatAppearance.BorderSize  = 1
    btn_cancel.BackColor    = BTN_CANCEL_BG
    btn_cancel.ForeColor    = BTN_CANCEL_FG
    btn_cancel.DialogResult = WF.DialogResult.Cancel
    btn_cancel.Cursor       = WF.Cursors.Hand
    try:
        btn_cancel.Font = D.Font("Segoe UI", 9.5)
    except Exception:
        pass
    btn_zone.Controls.Add(btn_cancel)

    # ── Bouton Quitter ────────────────────────────────────────────────────
    btn_quit = WF.Button()
    btn_quit.Text         = texts["btn_quit"]
    btn_quit.Size         = D.Size(130, 38)
    btn_quit.Location     = D.Point(302, 18)
    btn_quit.FlatStyle    = WF.FlatStyle.Flat
    btn_quit.FlatAppearance.BorderSize = 0
    btn_quit.BackColor    = ACCENT_RED
    btn_quit.ForeColor    = D.Color.White
    btn_quit.DialogResult = WF.DialogResult.OK
    btn_quit.Cursor       = WF.Cursors.Hand
    try:
        btn_quit.Font = D.Font("Segoe UI Semibold", 9.5, FontStyle.Bold)
    except Exception:
        btn_quit.Font = D.Font("Segoe UI", 9.5, FontStyle.Bold)
    btn_zone.Controls.Add(btn_quit)

    form.AcceptButton = btn_quit
    form.CancelButton = btn_cancel

    # ── Affichage via ShowDialog(owner) — identique au modele original ────
    try:
        owner = owner_window.native
        if owner is not None:
            result = form.ShowDialog(owner)
        else:
            result = form.ShowDialog()
    except Exception:
        result = form.ShowDialog()

    return result == WF.DialogResult.OK


def _ctypes_fallback() -> bool:
    """Secours si WinForms est indisponible."""
    try:
        import ctypes
        texts = _quit_texts_cache
        IDYES = 6
        flags = 0x04 | 0x20 | 0x40000 | 0x10000
        return ctypes.windll.user32.MessageBoxW(
            0,
            texts.get("quit_message", "Voulez-vous vraiment quitter MARIHAR ?"),
            texts.get("quit_title",   "Quitter MARIHAR"),
            flags,
        ) == IDYES
    except Exception:
        return True


# ---------------------------------------------------------------------------
# API exposee a l'interface JavaScript
# ---------------------------------------------------------------------------

class MariHarApi:
    """API exposee a l'interface (pont Python <-> JS)."""

    def update_quit_texts(self, quit_title, quit_message, btn_quit, btn_cancel):
        """Appele depuis JS a chaque changement de langue."""
        global _quit_texts_cache
        if quit_title:   _quit_texts_cache["quit_title"]   = quit_title
        if quit_message: _quit_texts_cache["quit_message"] = quit_message
        if btn_quit:     _quit_texts_cache["btn_quit"]     = btn_quit
        if btn_cancel:   _quit_texts_cache["btn_cancel"]   = btn_cancel
        _log(f"[i18n] Textes mis a jour : {_quit_texts_cache}")
        _log(f"[i18n] quit_title={quit_title}, quit_message={quit_message}, btn_quit={btn_quit}, btn_cancel={btn_cancel}")

    def confirm_quit(self):
        """Fermeture apres clic sur Quitter dans l'interface HTML."""
        _desktop_state["allow_close"] = True
        w = _desktop_state["window"]

        def _delayed_destroy():
            time.sleep(0.12)
            try:
                if w is not None:
                    w.destroy()
            except Exception:
                pass

        threading.Thread(target=_delayed_destroy, daemon=True).start()

    def request_quit_confirmation(self):
        """
        Appelé depuis JavaScript quand l'utilisateur tente de fermer la fenêtre (X).
        Affiche la boîte de dialogue stylisée et retourne True si l'utilisateur confirme.
        """
        w = _desktop_state["window"]
        if w is None:
            return True
        ok = _show_quit_dialog_native(w)
        if ok:
            _desktop_state["allow_close"] = True
        return ok

    def pick_ytdlp_exe(self):
        """
        Ouvre une boîte de dialogue pour sélectionner un exécutable yt-dlp.exe custom.
        Retourne le chemin absolu (string) ou None si annulé.

        IMPORTANT: pas de copie dans le dossier d'installation.
        Le JS enregistre ce chemin dans config.json.
        """
        print("[YTDLP PICK] Fonction pick_ytdlp_exe appelée")
        try:
            import clr  # type: ignore
            clr.AddReference("System.Windows.Forms")
            clr.AddReference("System.Drawing")
            import System.Windows.Forms as WF  # type: ignore

            # Filtre uniquement yt-dlp.exe (mais l'utilisateur peut quand même changer si besoin)
            ofd = WF.OpenFileDialog()
            ofd.Title = "Sélectionner yt-dlp.exe"
            ofd.Filter = "yt-dlp.exe (*.exe)|*.exe"
            ofd.CheckFileExists = True
            ofd.Multiselect = False

            # Optionnel: définir un répertoire de départ
            try:
                ofd.InitialDirectory = os.path.dirname(os.path.abspath(__file__))
            except Exception:
                pass

            # Appel modal
            w = _desktop_state.get("window")
            try:
                owner = w.native if w is not None else None
            except Exception:
                owner = None

            # ShowDialog(owner) si possible, sinon fallback
            try:
                result = ofd.ShowDialog(owner) if owner is not None else ofd.ShowDialog()
            except Exception:
                result = ofd.ShowDialog()

            if result == WF.DialogResult.OK and ofd.FileName:
                print(f"[YTDLP PICK] Fichier sélectionné: {ofd.FileName}")
                return str(ofd.FileName)
            print("[YTDLP PICK] Sélection annulée")
            return None
        except Exception as e:
            print(f"[YTDLP PICK] Erreur: {e}")
            _log(f"[YTDLP PICK] Erreur: {e}")
            return None


# ---------------------------------------------------------------------------
# Application Flask
# ---------------------------------------------------------------------------

def start_flask_app():
    """Demarre le serveur Flask en arriere-plan."""
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_logo_base64() -> str:
    """
    Charge le logo PNG et le retourne encodé en base64 (sans préfixe data:).
    Cherche d'abord dans static/, puis à la racine (build PyInstaller).
    Retourne une chaîne vide si le fichier est introuvable.
    """
    candidates = [
        get_resource_path("Assets/Logo_marino.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode("ascii")
            except Exception as exc:
                _log(f"[Logo] Erreur lecture logo : {exc}")
    _log("[Logo] Avertissement : logo non trouvé, splash sans image.")
    return ""


def _fatal_missing(file_label, file_path):
    msg = (
        f"Fichier requis manquant : {file_label}\n\n"
        f"Chemin : {file_path}\n\n"
        "Reinstallez ou recopiez les fichiers de l'application."
    )
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "MARIHAR - Erreur", 0x10)
        except Exception:
            pass
    else:
        _log(msg)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Creation de la fenetre PyWebView
# ---------------------------------------------------------------------------

def create_desktop_app():
    """
    Cree et configure l'application de bureau PyWebView.

    Architecture splash screen :
    ──────────────────────────────────────────────────────────────────
    webview.start() ne peut être appelé qu'UNE SEULE FOIS par processus.
    On crée donc les deux fenêtres AVANT d'appeler start() :
      1. Fenêtre principale  → hidden=True  (invisible au départ)
      2. Fenêtre splash      → visible, frameless, on_top
    Quand le bouton est cliqué (ou après 20 s), SplashApi.start_app() :
      - appelle main_window.show()      → affiche la fenêtre principale
      - appelle splash_window.destroy() → ferme le splash
    ──────────────────────────────────────────────────────────────────
    """
    import time
    # Ajouter un timestamp pour forcer le rechargement
    url = f"http://127.0.0.1:5000?t={int(time.time())}"
    api = MariHarApi()

    # ── 1. Fenêtre principale (cachée au départ) ──────────────────────
    window = webview.create_window(
        title="MARIHAR  —  Téléchargeur de vidéos",
        url=url,
        width=1200,
        height=800,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600),
        confirm_close=False,
        background_color="#0a0818",
        text_select=False,
        zoomable=True,
        draggable=False,
        js_api=api,
        hidden=True,   # invisible jusqu'à la fin du splash
    )
    _desktop_state["window"] = window

    # ── 2. Fenêtre splash (frameless, visible, on_top) ────────────────
    from splash_screen import build_splash_html, SplashApi

    logo_b64   = _get_logo_base64()
    splash_html = build_splash_html(logo_b64)
    splash_api  = SplashApi(main_window=window, on_shown_callback=_apply_titlebar_style)

    splash = webview.create_window(
        title="MARIHAR",
        html=splash_html,
        width=900,
        height=600,
        resizable=False,
        frameless=True,
        on_top=True,
        background_color="#07060f",
        js_api=splash_api,
    )
    # Référence partagée pour que SplashApi puisse détruire le splash
    splash_api._splash_ref.append(splash)

    # ── 3. Événements fenêtre principale ──────────────────────────
    def on_closing():
        # Fermeture déjà confirmée (via confirm_quit HTML ou validation précédente)
        if _desktop_state["allow_close"]:
            return True
        # Afficher notre boîte de dialogue stylisée WinForms
        w = _desktop_state["window"]
        ok = _show_quit_dialog_native(w)
        if ok:
            _desktop_state["allow_close"] = True
            return True
        return False

    window.events.closing += on_closing
    
    # ── 4. Initialisation des traductions après chargement JS ─────
    def on_loaded():
        """Appelé quand la page HTML est chargée."""
        _log("[INFO] Page HTML chargée, initialisation des traductions...")
        
        def sync_with_retry(attempt=0):
            """Tente de synchroniser les traductions avec retry."""
            try:
                result = window.evaluate_js("""
                    (function() {
                        if (typeof _syncQuitTextsToPython === 'function' && window.translations) {
                            _syncQuitTextsToPython(window.translations);
                            return 'sync_ok';
                        } else if (typeof _syncQuitTextsToPython === 'function') {
                            return 'sync_no_trans';
                        } else {
                            return 'sync_no_func';
                        }
                    })()
                """)
                _log(f"[i18n] Tentative {attempt}: result={result}")
                if result != 'sync_ok' and attempt < 5:
                    time.sleep(0.5)
                    sync_with_retry(attempt + 1)
            except Exception as exc:
                _log(f"[WARN] Erreur sync traductions (tentative {attempt}): {exc}")
                if attempt < 5:
                    time.sleep(0.5)
                    sync_with_retry(attempt + 1)
        
        # Lancer la synchronisation dans un thread séparé pour ne pas bloquer
        threading.Thread(target=sync_with_retry, daemon=True).start()
    
    window.events.loaded += on_loaded

    # ── 4. Lancement unique de la boucle UI ───────────────────────────
    _log("[INFO] Démarrage de la boucle UI (splash + fenêtre principale)...")
    webview.start(
        gui="edgechromium",
        debug=False,
        http_server=False,
        private_mode=False,
    )


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------

def main():
    if not _is_frozen():
        _log("=" * 60)
        _log("  MARIHAR - Application de Bureau")
        _log("=" * 60)

    required_files = [
        "Binaries/yt-dlp.exe",
        "Binaries/ffmpeg.exe",
        "Binaries/ffprobe.exe",
        "Frontend/templates/index.html",
        "Frontend/static/css/style.css",
        "Frontend/static/js/app.js",
    ]

    _log("[INFO] Verification des fichiers essentiels...")
    for file in required_files:
        file_path = get_resource_path(file)
        if os.path.exists(file_path):
            _log(f"  [OK] {file}")
        else:
            _fatal_missing(file, file_path)

    _log("[INFO] Demarrage du serveur Flask en arriere-plan...")
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()

    _log("[INFO] Attente du serveur Flask...")
    time.sleep(2)

    _log("[INFO] Démarrage du splash screen + interface MARIHAR...")
    create_desktop_app()


if __name__ == "__main__":
    main()
