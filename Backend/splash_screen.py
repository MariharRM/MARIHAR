# Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
"""
splash_screen.py — Écran de démarrage professionnel pour MARIHAR.

Architecture :
- `build_splash_html(logo_b64)`  → génère le HTML complet du splash
- `SplashApi`                    → API Python exposée au JS du splash
                                   (ferme le splash et affiche la fenêtre principale)

Ce module est importé par `desktop_app.py`.
Le splash et la fenêtre principale partagent le MÊME appel `webview.start()` :
  1. La fenêtre principale est créée avec `hidden=True`
  2. Le splash est créé normalement (visible, frameless)
  3. `webview.start()` lance les deux fenêtres
  4. Quand le bouton est cliqué OU après 20 s, `SplashApi.start_app()` :
       - affiche la fenêtre principale
       - détruit le splash
"""

import threading
import time


# ---------------------------------------------------------------------------
# Classe API exposée au JavaScript du splash
# ---------------------------------------------------------------------------

class SplashApi:
    """
    Pont Python ↔ JS pour le splash screen.

    Paramètres
    ----------
    main_window  : webview.Window   fenêtre principale (hidden=True au départ)
    splash_ref   : list             liste [splash_window] — remplie après création
                                    (workaround : on ne peut pas passer la fenêtre
                                    splash au constructeur avant qu'elle existe)
    """

    def __init__(self, main_window, on_shown_callback=None):
        self._main        = main_window      # fenêtre principale (cachée)
        self._splash_ref  = []               # [splash_window] — assigné depuis desktop_app
        self._called      = False            # garde-fou : n'exécuter qu'une seule fois
        self._lock        = threading.Lock()
        self._on_shown    = on_shown_callback  # appelé après show() pour styliser la barre

    # ------------------------------------------------------------------
    # Appelé depuis JS :  window.pywebview.api.start_app()
    # ------------------------------------------------------------------
    def start_app(self):
        """
        Déclenché par le bouton OU par le timer JS (20 s).
        Montre la fenêtre principale et ferme le splash.
        Garanti de ne s'exécuter qu'une seule fois.
        """
        with self._lock:
            if self._called:
                return
            self._called = True

        def _transition():
            # Légère pause pour que l'animation de sortie CSS ait le temps de jouer
            time.sleep(0.35)

            # 1. Afficher la fenêtre principale
            try:
                self._main.show()
            except Exception as exc:
                print(f"[Splash] Impossible d'afficher la fenêtre principale : {exc}")

            # 2. Appliquer le style DWM (barre de titre sombre) juste après show()
            #    On attend un court instant que la fenêtre soit réellement visible
            time.sleep(0.15)
            try:
                if self._on_shown:
                    hwnd = int(self._main.native.Handle.ToInt64())
                    self._on_shown(hwnd)
            except Exception as exc:
                print(f"[Splash] Impossible d'appliquer le style DWM : {exc}")

            # 3. Fermer le splash
            time.sleep(0.05)
            try:
                if self._splash_ref:
                    self._splash_ref[0].destroy()
            except Exception as exc:
                print(f"[Splash] Impossible de fermer le splash : {exc}")

        threading.Thread(target=_transition, daemon=True).start()


# ---------------------------------------------------------------------------
# Générateur HTML du splash screen
# ---------------------------------------------------------------------------

def build_splash_html(logo_b64: str) -> str:
    """
    Construit et retourne le HTML complet du splash screen.

    Paramètre
    ---------
    logo_b64 : str   contenu du PNG encodé en base64 (sans le préfixe data:)

    Notes
    -----
    - Les accolades CSS/JS sont doublées {{ }} pour être compatibles avec f-string.
    - `window.pywebview.api.start_app()` est appelé par le bouton et par le timer.
    - La fenêtre est frameless → fond draggable via `-webkit-app-region: drag`.
    """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MARIHAR</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Cinzel+Decorative:wght@700;900&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400;1,500&family=Inter:wght@300;400;500;600;700&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  /* ── Reset & base ────────────────────────────────────────────── */
  *, *::before, *::after {{
    margin: 0; padding: 0; box-sizing: border-box;
  }}

  :root {{
    --red:    #e94560;
    --violet: #533483;
    --gold:   #B8945F;
    --gold-light: #e8c97e;
    --bg:     #0a0818;
    --deep:   #07060f;
    --card:   rgba(255,255,255,0.04);
  }}

  html, body {{
    width: 100%; height: 100%;
    overflow: hidden;
    background: linear-gradient(160deg, #07060f 0%, #0a0818 50%, #12102a 100%);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    color: #fff;
    /* Fenêtre frameless : draggable sur le fond */
    -webkit-app-region: drag;
    user-select: none;
  }}

  /* ── Effet scan-line futuriste ───────────────────────────────── */
  body::before {{
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(83, 52, 131, 0.04) 2px,
      rgba(83, 52, 131, 0.04) 4px
    );
    pointer-events: none;
    animation: scanMove 8s linear infinite;
  }}
  @keyframes scanMove {{
    from {{ background-position: 0 0; }}
    to   {{ background-position: 0 100px; }}
  }}

  /* ── Lueur ambiante centrale ─────────────────────────────────── */
  body::after {{
    content: '';
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 560px; height: 380px;
    background: radial-gradient(
      ellipse at center,
      rgba(83, 52, 131, 0.12) 0%,
      rgba(233, 69, 96, 0.07) 40%,
      transparent 72%
    );
    pointer-events: none;
    z-index: 1;
    animation: ambientPulse 4s ease-in-out infinite;
  }}
  @keyframes ambientPulse {{
    0%, 100% {{ opacity: 0.7; transform: translate(-50%, -50%) scale(1); }}
    50%       {{ opacity: 1;   transform: translate(-50%, -50%) scale(1.08); }}
  }}

  /* ── Particules canvas ───────────────────────────────────────── */
  #particles {{
    position: fixed; inset: 0; z-index: 0;
    pointer-events: none;
  }}

  /* ── Carte centrale ──────────────────────────────────────────── */
  .card {{
    position: relative; z-index: 10;
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 0;
    padding: 32px 48px 24px;
  }}

  /* ── Liseré shimmer en haut ──────────────────────────────────── */
  .shimmer-bar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: 3px; z-index: 100;
    background: linear-gradient(
      90deg,
      var(--violet) 0%,
      var(--red) 40%,
      var(--gold) 70%,
      var(--violet) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 2.5s ease-in-out infinite;
  }}
  @keyframes shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
  }}

  /* ── Logo ────────────────────────────────────────────────────── */
  .logo-wrap {{
    position: relative;
    margin-bottom: 16px;
    animation: logoIn 0.9s cubic-bezier(0.34,1.56,0.64,1) both;
  }}
  @keyframes logoIn {{
    from {{ opacity: 0; transform: scale(0.55); }}
    to   {{ opacity: 1; transform: scale(1); }}
  }}

  .logo-wrap img {{
    width: 108px; height: 108px;
    object-fit: contain;
    display: block;
    filter: drop-shadow(0 0 18px rgba(233,69,96,0.55))
            drop-shadow(0 0 36px rgba(184,148,95,0.28));
    -webkit-app-region: no-drag;
  }}

  /* Halo pulsant derrière le logo */
  .logo-halo {{
    position: absolute; inset: -18px;
    border-radius: 50%;
    background: radial-gradient(
      circle,
      rgba(233,69,96,0.18) 0%,
      rgba(184,148,95,0.10) 50%,
      transparent 70%
    );
    animation: haloPulse 2.8s ease-in-out infinite;
    pointer-events: none;
  }}
  @keyframes haloPulse {{
    0%, 100% {{ transform: scale(1);    opacity: 0.7; }}
    50%       {{ transform: scale(1.18); opacity: 1;   }}
  }}

  /* ── Séparateur décoratif ─────────────────────────────────────── */
  .divider {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    opacity: 0;
    animation: fadeUp 0.6s ease both;
    animation-delay: 0.42s;
  }}
  .divider-line {{
    width: 40px; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(184,148,95,0.5));
  }}
  .divider-line.right {{
    background: linear-gradient(270deg, transparent, rgba(184,148,95,0.5));
  }}
  .divider-diamond {{
    width: 6px; height: 6px;
    background: var(--gold);
    transform: rotate(45deg);
    box-shadow: 0 0 8px rgba(184,148,95,0.7);
  }}

  /* ── Texte principal (police display Cinzel) ─────────────────── */
  .main-title {{
    font-family: 'Cinzel', 'Trajan Pro', 'Times New Roman', serif;
    font-size: 1.6rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: transparent;
    background: linear-gradient(
      135deg,
      #f0ecff 0%,
      #c8b8e8 40%,
      #f0ecff 60%,
      #a090c0 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: none;
    filter: drop-shadow(0 2px 12px rgba(233,69,96,0.3));
    animation: fadeUp 0.8s ease both;
    animation-delay: 0.5s;
    opacity: 0;
    margin-bottom: 6px;
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  /* ── Sous-titre (police Rajdhani moderne) ────────────────────── */
  .sub-title {{
    font-family: 'Rajdhani', 'Segoe UI', sans-serif;
    font-size: 0.95rem;
    font-weight: 500;
    color: rgba(168,160,200,0.8);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    animation: fadeUp 0.8s ease both;
    animation-delay: 0.85s;
    opacity: 0;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .sub-title .dot {{
    width: 4px; height: 4px;
    border-radius: 50%;
    background: var(--gold);
    opacity: 0.7;
    flex-shrink: 0;
  }}
  .sub-title .highlight {{
    color: #e0d0b0;
    font-weight: 600;
    letter-spacing: 0.18em;
  }}

  /* ── Bloc glassmorphism MARIHAR ──────────────────────────────── */
  .brand-block {{
    background: linear-gradient(
      135deg,
      rgba(83,52,131,0.12) 0%,
      rgba(255,255,255,0.03) 50%,
      rgba(233,69,96,0.06) 100%
    );
    border: 1px solid rgba(184,148,95,0.22);
    border-top: 1px solid rgba(232,201,126,0.35);
    border-radius: 20px;
    padding: 12px 52px 14px;
    margin-bottom: 28px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow:
      0 12px 40px rgba(7,6,15,0.65),
      0 0 0 1px rgba(255,255,255,0.03),
      inset 0 1px 0 rgba(255,255,255,0.08),
      inset 0 -1px 0 rgba(0,0,0,0.2);
    animation: fadeUp 0.8s ease both;
    animation-delay: 1.15s;
    opacity: 0;
    -webkit-app-region: no-drag;
    position: relative;
    overflow: hidden;
  }}

  /* Reflet interne subtil */
  .brand-block::before {{
    content: '';
    position: absolute;
    top: 0; left: 15%; right: 15%; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(232,201,126,0.6), transparent);
  }}

  .brand-name {{
    font-family: 'Cinzel Decorative', 'Cinzel', 'Trajan Pro', serif;
    font-size: 4rem;
    font-weight: 900;
    letter-spacing: 0.22em;
    background: linear-gradient(
      90deg,
      var(--red)   0%,
      #b06ab3      28%,
      var(--gold-light) 55%,
      var(--gold)  72%,
      var(--red)   100%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientFlow 3.5s linear infinite;
    text-shadow: none;
    line-height: 1.1;
  }}
  @keyframes gradientFlow {{
    0%   {{ background-position: 0% center; }}
    100% {{ background-position: 200% center; }}
  }}

  /* ── Citation italienne sous MARIHAR ────────────────────────── */
  .brand-tag {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    margin-top: 10px;
    opacity: 0;
    animation: fadeUp 0.7s ease both;
    animation-delay: 1.35s;
    -webkit-app-region: no-drag;
    max-width: 480px;
  }}

  /* Séparateur fin au-dessus de la citation */
  .brand-tag::before {{
    content: '';
    display: block;
    width: 60px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(184,148,95,0.4), transparent);
    margin-bottom: 6px;
  }}

  /* Première partie : liberté */
  .bio-line-1 {{
    font-family: 'Cormorant Garamond', 'Garamond', 'Georgia', serif;
    font-style: italic;
    font-weight: 300;
    font-size: 0.82rem;
    line-height: 1.55;
    letter-spacing: 0.04em;
    color: rgba(220, 210, 240, 0.72);
    text-align: center;
  }}

  /* Virgule + espace entre les deux membres */
  .bio-comma {{
    display: none;
  }}

  /* Deuxième partie : progrès — mise en relief dorée */
  .bio-line-2 {{
    font-family: 'Cormorant Garamond', 'Garamond', 'Georgia', serif;
    font-style: italic;
    font-weight: 500;
    font-size: 0.82rem;
    line-height: 1.55;
    letter-spacing: 0.04em;
    color: rgba(232, 201,126, 0.82);
    text-align: center;
  }}

  /* Petit ornement guillemet ouvrant/fermant */
  .bio-quote-open,
  .bio-quote-close {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 300;
    line-height: 0;
    vertical-align: -0.18em;
    color: rgba(184,148,95,0.45);
    letter-spacing: 0;
    font-style: normal;
  }}
  .bio-quote-open {{ margin-right: 2px; }}
  .bio-quote-close {{ margin-left: 2px; }}

  /* ── Bouton ──────────────────────────────────────────────────── */
  .btn-enter {{
    -webkit-app-region: no-drag;
    cursor: pointer;
    padding: 0;
    border: none;
    background: none;
    outline: none;
    position: relative;
    overflow: hidden;
    border-radius: 50px;
    animation: fadeUp 0.8s ease both, btnPulse 2.5s ease-in-out 2s infinite;
    animation-delay: 1.45s, 2s;
    opacity: 0;
    margin-bottom: 20px;
  }}

  /* Fond dégradé du bouton */
  .btn-enter .btn-bg {{
    display: block;
    padding: 13px 48px;
    background: linear-gradient(
      135deg,
      var(--red)    0%,
      #7c3aed      50%,
      var(--violet) 100%
    );
    border-radius: 50px;
    position: relative;
    transition: filter 0.18s ease;
  }}
  .btn-enter:hover .btn-bg {{ filter: brightness(1.1); }}
  .btn-enter:active .btn-bg {{ filter: brightness(0.92); }}

  /* Bordure brillante autour du bouton */
  .btn-enter::before {{
    content: '';
    position: absolute; inset: -1px;
    border-radius: 50px;
    background: linear-gradient(135deg, var(--gold-light), var(--red), var(--violet), var(--gold-light));
    background-size: 300% 300%;
    animation: borderFlow 3s linear infinite;
    z-index: -1;
    opacity: 0.7;
  }}
  @keyframes borderFlow {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
  }}

  /* Reflet interne */
  .btn-enter .btn-bg::after {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, transparent 55%);
    border-radius: inherit;
    pointer-events: none;
  }}

  /* Icône + texte du bouton */
  .btn-inner {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .btn-icon {{
    display: flex; align-items: center; justify-content: center;
    width: 20px; height: 20px;
    flex-shrink: 0;
  }}
  .btn-icon svg {{ width: 16px; height: 16px; stroke: rgba(255,255,255,0.9); }}

  .btn-label {{
    font-family: 'Rajdhani', 'Segoe UI', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #fff;
  }}

  .btn-enter:hover {{
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 8px 32px rgba(233,69,96,0.55), 0 0 0 3px rgba(233,69,96,0.15);
  }}
  .btn-enter:active {{
    transform: translateY(0) scale(0.98);
  }}
  .btn-enter {{
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    box-shadow: 0 4px 22px rgba(233,69,96,0.4);
  }}
  @keyframes btnPulse {{
    0%, 100% {{ box-shadow: 0 4px 22px rgba(233,69,96,0.4), 0 0 0 0 rgba(233,69,96,0.35); }}
    50%       {{ box-shadow: 0 4px 22px rgba(233,69,96,0.4), 0 0 0 10px rgba(233,69,96,0); }}
  }}

  /* ── Barre de progression ────────────────────────────────────── */
  .progress-track {{
    position: fixed; bottom: 0; left: 0; right: 0;
    height: 3px;
    background: rgba(255,255,255,0.06);
    z-index: 100;
  }}
  .progress-fill {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, var(--violet), var(--red), var(--gold));
    background-size: 200% 100%;
    animation:
      fillBar 20s linear forwards,
      shimmer 2.5s ease-in-out infinite;
    border-radius: 0 2px 2px 0;
  }}
  @keyframes fillBar {{
    from {{ width: 0%; }}
    to   {{ width: 100%; }}
  }}

  /* ── Version ─────────────────────────────────────────────────── */
  .version {{
    position: fixed; bottom: 12px; right: 16px;
    font-family: 'Rajdhani', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    color: rgba(168,160,200,0.4);
    letter-spacing: 0.12em;
    z-index: 50;
    -webkit-app-region: no-drag;
  }}

  /* ── Animation de sortie (classe ajoutée par JS) ─────────────── */
  .fade-out {{
    animation: fadeOut 0.35s ease forwards !important;
  }}
  @keyframes fadeOut {{
    from {{ opacity: 1; transform: scale(1); }}
    to   {{ opacity: 0; transform: scale(0.97); }}
  }}
  .card.fade-out, body.fade-out {{
    animation: fadeOut 0.35s ease forwards;
  }}
</style>
</head>
<body>

<!-- Liseré shimmer -->
<div class="shimmer-bar"></div>

<!-- Canvas particules -->
<canvas id="particles"></canvas>

<!-- Carte principale -->
<div class="card" id="mainCard">

  <!-- Logo -->
  <div class="logo-wrap">
    <div class="logo-halo"></div>
    <img src="data:image/png;base64,{logo_b64}" alt="MARIHAR Logo" draggable="false">
  </div>

  <!-- Séparateur décoratif supérieur -->
  <div class="divider">
    <div class="divider-line"></div>
    <div class="divider-diamond"></div>
    <div class="divider-line right"></div>
  </div>

  <!-- Texte principal -->
  <div class="main-title">Tongasoa Tompoko</div>

  <!-- Sous-titre -->
  <div class="sub-title">
    <span class="dot"></span>
    <span>Misaotra anao nisafidy an'i&nbsp;<span class="highlight">MARIHAR</span></span>
    <span class="dot"></span>
  </div>

  <!-- Bloc glassmorphism MARIHAR -->
  <div class="brand-block">
    <div class="brand-name">MARIHAR</div>
    <div class="brand-tag">
      <span class="bio-line-1">
        <span class="bio-quote-open">&ldquo;</span>Libera te stesso dai vincoli sociali,
      </span>
      <span class="bio-line-2">
        ma tieni presente l'inarrestabile avanzare del progresso.<span class="bio-quote-close">&rdquo;</span>
      </span>
    </div>
  </div>

  <!-- Bouton d'accès -->
  <button class="btn-enter" id="enterBtn" onclick="launchApp()">
    <span class="btn-bg">
      <span class="btn-inner">
        <span class="btn-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
        </span>
        <span class="btn-label">Accéder à MARIHAR</span>
      </span>
    </span>
  </button>

</div>

<!-- Barre de progression (20 s) -->
<div class="progress-track">
  <div class="progress-fill" id="progressFill"></div>
</div>

<!-- Version -->
<div class="version">v1.0</div>

<script>
  // ── Particules flottantes ────────────────────────────────────────────
  (function() {{
    const canvas = document.getElementById('particles');
    const ctx    = canvas.getContext('2d');

    const COLORS = ['rgba(233,69,96,', 'rgba(83,52,131,', 'rgba(184,148,95,'];
    const COUNT  = 55;

    let W, H, particles;

    function resize() {{
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }}

    function rand(min, max) {{
      return Math.random() * (max - min) + min;
    }}

    function initParticles() {{
      particles = Array.from({{ length: COUNT }}, function() {{
        return {{
          x:    rand(0, W),
          y:    rand(0, H),
          r:    rand(1, 3.2),
          dx:   rand(-0.25, 0.25),
          dy:   rand(-0.4, -0.1),
          a:    rand(0.1, 0.55),
          da:   rand(-0.002, 0.002),
          col:  COLORS[Math.floor(rand(0, COLORS.length))]
        }};
      }});
    }}

    function draw() {{
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < particles.length; i++) {{
        var p = particles[i];
        p.x += p.dx;
        p.y += p.dy;
        p.a += p.da;
        if (p.a < 0.05) p.da =  Math.abs(p.da);
        if (p.a > 0.6)  p.da = -Math.abs(p.da);
        if (p.y < -4)   p.y  = H + 4;
        if (p.x < -4)   p.x  = W + 4;
        if (p.x > W+4)  p.x  = -4;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.col + p.a + ')';
        ctx.fill();
      }}
      requestAnimationFrame(draw);
    }}

    window.addEventListener('resize', function() {{
      resize();
      initParticles();
    }});

    resize();
    initParticles();
    draw();
  }})();

  // ── Lancement de l'application ───────────────────────────────────────
  var _launched = false;

  function launchApp() {{
    if (_launched) return;
    _launched = true;

    // Animation de sortie
    document.getElementById('mainCard').classList.add('fade-out');

    // Appel Python après un court délai (laisse l'animation jouer)
    setTimeout(function() {{
      try {{
        window.pywebview.api.start_app();
      }} catch(e) {{
        console.error('pywebview API non disponible :', e);
      }}
    }}, 300);
  }}

  // ── Timer 20 secondes → lancement automatique ───────────────────────
  var _autoTimer = setTimeout(function() {{
    launchApp();
  }}, 20000);

  // Si le bouton est cliqué avant la fin, annuler le timer auto
  document.getElementById('enterBtn').addEventListener('click', function() {{
    clearTimeout(_autoTimer);
  }});

  // Désactiver le menu contextuel (fenêtre propre)
  document.addEventListener('contextmenu', function(e) {{
    e.preventDefault();
  }});
</script>
</body>
</html>"""

    return html
