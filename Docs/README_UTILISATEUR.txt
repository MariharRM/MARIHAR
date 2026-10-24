════════════════════════════════════════════════════════════
  MARIHAR — Téléchargeur de vidéos (Windows)  |  v1.0.0
════════════════════════════════════════════════════════════

Libera te stesso dai vincoli sociali, ma tieni presente
l'inarrestabile avanzare del progresso.

────────────────────────────────────────────────────────────
📖  DESCRIPTION
────────────────────────────────────────────────────────────
MARIHAR est une application de bureau qui vous permet de
télécharger des vidéos et de l'audio depuis de nombreuses
plateformes compatibles avec yt-dlp, via une interface
web moderne intégrée (WebView).

────────────────────────────────────────────────────────────
✅  FONCTIONNALITÉS PRINCIPALES
────────────────────────────────────────────────────────────
  • Téléchargement vidéo (MP4, MKV, WebM…) jusqu'en 4K
  • Extraction audio (MP3, AAC, Opus, FLAC…)
  • Téléchargement de playlists complètes
  • Sous-titres : téléchargement et options de rendu
  • Sélection fine du format et de la qualité
  • Dossier de sortie personnalisable
  • Console d'analyse yt-dlp en temps réel
  • Historique local des fichiers téléchargés
  • Interface claire, thème sombre / clair

────────────────────────────────────────────────────────────
🚀  UTILISATION (RAPIDE)
────────────────────────────────────────────────────────────
  1) Ouvrez MARIHAR
  2) Saisissez une URL de vidéo/playlist OU un texte de recherche
  3) Cliquez sur « Analyser »
  4) Choisissez vos options (format, sous-titres, dossier…)
  5) Cliquez sur « Télécharger »

────────────────────────────────────────────────────────────
📁  OÙ SONT STOCKÉS MES TÉLÉCHARGEMENTS ?
────────────────────────────────────────────────────────────
Vous pouvez choisir un dossier de sortie dans l'interface.

Si aucun dossier n'est sélectionné, MARIHAR utilise par
défaut le dossier « Downloads » (ou « Téléchargements »
en français) de votre ordinateur, dans votre profil
utilisateur.

L'historique « Fichiers téléchargés » est conservé
localement et se met à jour après chaque téléchargement.


────────────────────────────────────────────────────────────
📄  PLATEFORMES SUPPORTÉES
────────────────────────────────────────────────────────────
La liste complète des plateformes/extracteurs supportés
est fournie dans :  Plateformes_supportées.txt

────────────────────────────────────────────────────────────
⚙️  CONFIGURATION REQUISE
────────────────────────────────────────────────────────────
  • Windows 10 ou Windows 11 (64 bits)
  • Connexion Internet (pour les téléchargements)
  • Espace disque disponible selon vos fichiers

────────────────────────────────────────────────────────────
🔒  CONFIDENTIALITÉ & SÉCURITÉ
────────────────────────────────────────────────────────────
  • Application 100 % locale : vos téléchargements restent
    sur votre appareil, aucune donnée n'est envoyée.
  • Aucune création de compte requise.
  • Aucune télémétrie ni collecte de données.

────────────────────────────────────────────────────────────
❓  FAQ
────────────────────────────────────────────────────────────
Q : Dois-je installer Python ?
R : Non. L'application distribuée inclut tout le nécessaire
    (Python embarqué, yt-dlp, FFmpeg…).

Q : Pourquoi certains sites ne fonctionnent pas ?
R : La compatibilité dépend de la plateforme et de ses
    éventuels changements. Consultez Plateformes_supportées.txt
    et réessayez plus tard si nécessaire.

Q : Puis-je choisir la qualité de la vidéo ?
R : Oui. Après l'analyse, MARIHAR affiche tous les formats
    disponibles (résolution, codec, taille estimée).

Q : L'audio est-il séparé de la vidéo ?
R : Oui. L'onglet « Audio » liste les flux audio disponibles
    pour une extraction directe en MP3, AAC, etc.

════════════════════════════════════════════════════════════
  CRÉDITS & LICENCES DES LOGICIELS TIERS
════════════════════════════════════════════════════════════

Ce logiciel intègre plusieurs composants open-source.
Chacun est soumis à sa propre licence, détaillée ci-dessous.

────────────────────────────────────────────────────────────
1.  yt-dlp
────────────────────────────────────────────────────────────
Rôle    : Moteur de téléchargement et d'extraction de médias
Licence : The Unlicense (domaine public)
          Lorsqu'il est distribué avec certaines dépendances,
          l'ensemble peut être soumis à la GPLv3.
Dépôt   : https://github.com/yt-dlp/yt-dlp
Texte   : licenses/yt-dlp-LICENSE.txt
          https://unlicense.org/

MARIHAR fournit une interface graphique indépendante et
ne modifie pas le code source original de yt-dlp.

────────────────────────────────────────────────────────────
2.  FFmpeg
────────────────────────────────────────────────────────────
Rôle    : Conversion, remuxage et traitement audio/vidéo
          (utilisé par yt-dlp pour fusionner les flux et
           convertir les formats)
Licence : GNU Lesser General Public License v2.1 ou ultérieure
          (LGPL v2.1+)
          Certains composants optionnels (libx264, libx265…)
          peuvent être soumis à la GPLv2+ si activés.
Site    : https://ffmpeg.org/
Texte   : https://www.gnu.org/licenses/lgpl-2.1.html

Les binaires ffmpeg.exe, ffprobe.exe et ffplay.exe inclus
dans ce package sont des builds statiques standard.

────────────────────────────────────────────────────────────
3.  Flask
────────────────────────────────────────────────────────────
Rôle    : Serveur web local qui alimente l'interface WebView
Licence : BSD 3-Clause License
Dépôt   : https://github.com/pallets/flask
Texte   : https://github.com/pallets/flask/blob/main/LICENSE.txt

Copyright (c) 2010 Pallets
Redistribution and use in source and binary forms, with or
without modification, are permitted provided that the
following conditions are met:
  1. Redistributions of source code must retain the above
     copyright notice, this list of conditions and the
     following disclaimer.
  2. Redistributions in binary form must reproduce the above
     copyright notice, this list of conditions and the
     following disclaimer in the documentation and/or other
     materials provided with the distribution.
  3. Neither the name of the copyright holder nor the names
     of its contributors may be used to endorse or promote
     products derived from this software without specific
     prior written permission.

────────────────────────────────────────────────────────────
4.  Python
────────────────────────────────────────────────────────────
Rôle    : Environnement d'exécution de l'application
Licence : Python Software Foundation License (PSF) v2
Site    : https://www.python.org/
Texte   : https://docs.python.org/3/license.html

────────────────────────────────────────────────────────────
5.  Werkzeug
────────────────────────────────────────────────────────────
Rôle    : Bibliothèque WSGI utilisée par Flask
Licence : BSD 3-Clause License
Dépôt   : https://github.com/pallets/werkzeug
Texte   : https://github.com/pallets/werkzeug/blob/main/LICENSE.txt

────────────────────────────────────────────────────────────
6.  Jinja2
────────────────────────────────────────────────────────────
Rôle    : Moteur de templates HTML utilisé par Flask
Licence : BSD 3-Clause License
Dépôt   : https://github.com/pallets/jinja
Texte   : https://github.com/pallets/jinja/blob/main/LICENSE.txt

────────────────────────────────────────────────────────────
Fichiers de licence inclus dans le dossier licenses/
────────────────────────────────────────────────────────────
  • GPL-3.0.txt          — GNU General Public License v3
  • yt-dlp-LICENSE.txt   — Licence Unlicense de yt-dlp

════════════════════════════════════════════════════════════
  CONDITIONS D'UTILISATION
════════════════════════════════════════════════════════════

Ce logiciel est fourni à des fins personnelles et éducatives.

L'utilisateur est seul responsable de l'usage qu'il fait de
ce logiciel, notamment en ce qui concerne le respect des
droits d'auteur et des conditions d'utilisation des
plateformes.

L'auteur du logiciel ne peut être tenu responsable d'une
utilisation illégale ou abusive.

════════════════════════════════════════════════════════════
  LIMITATION DE RESPONSABILITÉ
════════════════════════════════════════════════════════════

Ce logiciel est fourni « tel quel », sans garantie d'aucune
sorte. L'auteur ne garantit pas le bon fonctionnement sur
toutes les plateformes ni l'absence d'erreurs.

En aucun cas l'auteur ne pourra être tenu responsable de
dommages directs ou indirects résultant de l'utilisation
du logiciel.

════════════════════════════════════════════════════════════
  AVERTISSEMENT
════════════════════════════════════════════════════════════

Certaines plateformes peuvent interdire le téléchargement
de contenu via leurs conditions d'utilisation.

Veuillez vous assurer que votre utilisation respecte les
lois locales et les règles des plateformes concernées.

════════════════════════════════════════════════════════════
  NON-AFFILIATION
════════════════════════════════════════════════════════════

Ce logiciel n'est pas affilié, sponsorisé ou approuvé par
les plateformes de diffusion de contenu.

Toutes les marques citées appartiennent à leurs propriétaires
respectifs.

════════════════════════════════════════════════════════════
  ENGAGEMENT UTILISATEUR
════════════════════════════════════════════════════════════

L'utilisateur s'engage à utiliser ce logiciel conformément
aux lois en vigueur et aux conditions d'utilisation des
plateformes utilisées.

L'utilisation est strictement limitée aux contenus dont
l'utilisateur détient les droits ou pour lesquels il a une
autorisation explicite.

════════════════════════════════════════════════════════════
  CONTACT & SUPPORT
════════════════════════════════════════════════════════════

Pour toute question, support technique ou signalement :

  📧  Email      : rakotonjanaharymarino@gmail.com
  🌍  Localisation : Madagascar

N'hésitez pas à nous contacter pour :
  • Signaler un bug ou une incompatibilité
  • Demander de l'aide pour l'utilisation
  • Proposer des améliorations
  • Obtenir des informations techniques

════════════════════════════════════════════════════════════
  VERSION
════════════════════════════════════════════════════════════

  Version : 1.0.0
  © 2026 MARIHAR — Tous droits réservés sur l'interface
  et le code original. Les composants tiers restent soumis
  à leurs licences respectives (voir section ci-dessus).

════════════════════════════════════════════════════════════
