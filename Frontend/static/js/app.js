// Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
/**
 * yt-dlp Web Interface - Frontend JavaScript
 */

// Global state
let currentVideoData = null;
let currentTaskId = null;
let progressInterval = null;
let selectedVideoFormat = null;
let selectedAudioFormat = null;
let selectedCombinedFormat = null;

/**
 * Modale MARIHAR (logo + style cohérent) — remplace alert() et la fermeture native.
 */
let mariharDialogOpen = false;
let mariharQuitPromptTimer = null;

/**
 * Appelé depuis Python après annulation de la fermeture (WebView2).
 * Un délai évite d'ouvrir la modale dans la même « frame » que FormClosing : sans cela,
 * les clics peuvent ne plus être traités (alors que mariharAlert depuis le JS normal fonctionne).
 */
window.mariharRequestQuitConfirm = function mariharRequestQuitConfirm() {
    if (mariharQuitPromptTimer !== null) {
        clearTimeout(mariharQuitPromptTimer);
        mariharQuitPromptTimer = null;
    }
    if (mariharDialogOpen) return;
    mariharQuitPromptTimer = setTimeout(function () {
        mariharQuitPromptTimer = null;
        if (mariharDialogOpen) return;
        if (typeof window.mariharShowQuitDialog === 'function') {
            window.mariharShowQuitDialog();
        }
    }, 320);
};

function closeMariharDialog() {
    const overlay = document.getElementById('mariharDialogOverlay');
    if (!overlay) return;
    
    // Nettoyage complet du modal
    mariharDialogOpen = false;
    overlay.removeAttribute('tabindex');
    overlay.classList.add('marihar-dialog-closed');
    overlay.setAttribute('aria-hidden', 'true');
}

function showMariharDialog(opts) {
    const overlay = document.getElementById('mariharDialogOverlay');
    const titleEl = document.getElementById('mariharDialogTitle');
    const messageEl = document.getElementById('mariharDialogMessage');
    const confirmBtn = document.getElementById('mariharDialogConfirm');
    const cancelBtn = document.getElementById('mariharDialogCancel');
    const dialogCard = overlay ? overlay.querySelector('.marihar-dialog') : null;
    const actions = overlay ? overlay.querySelector('.marihar-dialog-actions') : null;

    if (!overlay || !titleEl || !messageEl || !confirmBtn || !cancelBtn || !dialogCard || !actions) {
        const fallback = (opts && opts.message) || '';
        window.alert(fallback);
        return;
    }

    if (mariharDialogOpen) return;
    mariharDialogOpen = true;

    const {
        title = 'MARIHAR',
        message = '',
        variant = 'info',
        confirmText = 'OK',
        cancelText = 'Annuler',
        hideCancel = false,
        onConfirm = null,
        onCancel = null,
    } = opts;

    dialogCard.classList.remove('marihar-dialog--success', 'marihar-dialog--error', 'marihar-dialog--warning');
    if (variant === 'success') dialogCard.classList.add('marihar-dialog--success');
    else if (variant === 'error') dialogCard.classList.add('marihar-dialog--error');
    else if (variant === 'warning') dialogCard.classList.add('marihar-dialog--warning');

    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;

    if (hideCancel) {
        cancelBtn.style.display = 'none';
        actions.classList.add('marihar-dialog-actions--single');
    } else {
        cancelBtn.style.display = '';
        actions.classList.remove('marihar-dialog-actions--single');
    }

    function cleanup() {
        mariharDialogOpen = false;
        overlay.removeAttribute('tabindex');
        overlay.classList.add('marihar-dialog-closed');
        overlay.setAttribute('aria-hidden', 'true');
        confirmBtn.removeEventListener('click', onOk);
        cancelBtn.removeEventListener('click', onCancelClick);
        overlay.removeEventListener('click', onBackdrop);
        document.removeEventListener('keydown', onKey);
    }

    let confirmDone = false;
    let cancelDone = false;

    function onOk(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (confirmDone) return;
        confirmDone = true;
        cleanup();
        if (typeof onConfirm === 'function') {
            requestAnimationFrame(() => {
                try {
                    onConfirm();
                } catch (err) {
                    console.error('marihar onConfirm:', err);
                }
            });
        }
    }

    function onCancelClick(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (cancelDone) return;
        cancelDone = true;
        cleanup();
        if (typeof onCancel === 'function') {
            requestAnimationFrame(() => {
                try {
                    onCancel();
                } catch (err) {
                    console.error('marihar onCancel:', err);
                }
            });
        }
    }

    function onBackdrop(e) {
        // e.target reste l’élément d’origine : un clic sur un bouton ne doit pas fermer via l’overlay
        if (e.target !== overlay) return;
        e.preventDefault();
        if (hideCancel) onOk();
        else onCancelClick();
    }

    function onKey(e) {
        if (e.key === 'Escape' && !hideCancel) {
            e.preventDefault();
            onCancelClick();
        } else if (e.key === 'Enter' && hideCancel) {
            e.preventDefault();
            onOk();
        }
    }

    confirmBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancelClick);
    overlay.addEventListener('click', onBackdrop);
    document.addEventListener('keydown', onKey);

    overlay.classList.remove('marihar-dialog-closed');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.setAttribute('tabindex', '-1');

    requestAnimationFrame(function () {
        requestAnimationFrame(function () {
            try {
                overlay.focus({ preventScroll: true });
            } catch (err) {
                try {
                    overlay.focus();
                } catch (e2) {
                    /* ignore */
                }
            }
            try {
                confirmBtn.focus({ preventScroll: true });
            } catch (err) {
                confirmBtn.focus();
            }
        });
    });
}

function mariharAlert(message, variant = 'info', title = 'MARIHAR') {
    // Ensure translations are loaded before showing alert
    const translatedMessage = typeof message === 'string' && message.startsWith('alert_') ? t(message) : message;
    const translatedTitle = typeof title === 'string' && title.startsWith('alert_') ? t(title) : title;
    
    showMariharDialog({
        title: translatedTitle,
        message: translatedMessage,
        variant,
        hideCancel: true,
        confirmText: t('dialog_ok'),
    });
}

function mariharError(message, title = 'MARIHAR') {
    mariharAlert(message, 'error', title);
}

window.mariharShowQuitDialog = function mariharShowQuitDialog() {
    showMariharDialog({
        variant: 'warning',
        title: t('quit_title'),
        message: t('quit_message'),
        confirmText: t('btn_quit'),
        cancelText: t('btn_cancel_quit'),
        hideCancel: false,
        onConfirm: () => {
            if (
                window.pywebview &&
                window.pywebview.api &&
                typeof window.pywebview.api.confirm_quit === 'function'
            ) {
                const p = window.pywebview.api.confirm_quit();
                if (p && typeof p.catch === 'function') {
                    p.catch((err) => console.error('confirm_quit:', err));
                }
            }
        },
    });
};

// Fonction pour quitter directement sans confirmation HTML (appelée depuis l'interface)
window.mariharQuitDirect = function mariharQuitDirect() {
    if (
        window.pywebview &&
        window.pywebview.api &&
        typeof window.pywebview.api.confirm_quit === 'function'
    ) {
        const p = window.pywebview.api.confirm_quit();
        if (p && typeof p.catch === 'function') {
            p.catch((err) => console.error('confirm_quit:', err));
        }
    }
};

// DOM Elements - Will be initialized after DOM is loaded
let urlInput, analyzeBtn, loadingIndicator, videoInfo, formatsSection;
let advancedOptions, downloadSection, progressSection, consoleSection;
let pasteBtn, clearBtn;
let historyBtn, historyDropdown, historyList, historyEmpty, clearHistoryBtn, closeHistoryBtn;
let isHistoryDropdownOpen = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le système de langue (cela chargera les traductions de manière asynchrone)
    initLanguageSwitcher();
    // Ne pas appeler applyTranslations() ici car changeLanguage() le fait déjà après le chargement

    setupEventListeners();
    loadDownloadsList();
});

// ==================== LANGUAGE SWITCHER ====================

let isLangDropdownOpen = false;

function initLanguageSwitcher() {
    const langToggle = document.getElementById('langToggle');
    const langDropdown = document.getElementById('langDropdown');
    const langCurrentCode = document.getElementById('langCurrentCode');

    if (!langToggle || !langDropdown) return;

    // Mettre à jour le code affiché selon la langue sauvegardée
    function updateLangCode() {
        const codes = { fr: 'FR', en: 'EN', it: 'IT', mg: 'MG' };
        if (langCurrentCode) {
            langCurrentCode.textContent = codes[window.currentLang] || 'FR';
        }
    }
    updateLangCode();

    // Surcharger setLanguage pour mettre à jour le code
    const originalSetLanguage = window.setLanguage;
    window.setLanguage = function(lang) {
        originalSetLanguage(lang);
        updateLangCode();
    };

    langToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        // Animation du bouton
        langToggle.style.transform = 'scale(0.95)';
        setTimeout(() => { langToggle.style.transform = 'scale(1)'; }, 150);

        // Position du bouton
        const rect = langToggle.getBoundingClientRect();

        if (!isLangDropdownOpen) {
            // Afficher temporairement pour mesurer la largeur réelle
            langDropdown.style.display = 'block';
            langDropdown.style.visibility = 'hidden';
            langDropdown.style.opacity = '0';
            langDropdown.style.transform = 'translateY(-10px)';

            const dropdownWidth = langDropdown.offsetWidth;

            // Aligner le bord droit du dropdown avec le bord droit du bouton
            const leftPosition = rect.right - dropdownWidth;

            langDropdown.style.top = (rect.bottom + 5) + 'px';
            langDropdown.style.left = leftPosition + 'px';
            langDropdown.style.right = 'auto';
            langDropdown.style.visibility = 'visible';

            // Marquer l'option active
            document.querySelectorAll('.lang-option').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-lang') === window.currentLang);
            });

            setTimeout(() => {
                langDropdown.style.opacity = '1';
                langDropdown.style.transform = 'translateY(0)';
            }, 10);

            isLangDropdownOpen = true;
            window.isLangDropdownOpen = true;
        } else {
            langDropdown.style.opacity = '0';
            langDropdown.style.transform = 'translateY(-10px)';
            setTimeout(() => { langDropdown.style.display = 'none'; }, 300);
            isLangDropdownOpen = false;
            window.isLangDropdownOpen = false;
        }
    });

    // Fermer en cliquant ailleurs
    document.addEventListener('click', (e) => {
        // Lire depuis window pour rester synchronisé avec i18n.js
        const open = isLangDropdownOpen || window.isLangDropdownOpen;
        if (open &&
            !langToggle.contains(e.target) &&
            !langDropdown.contains(e.target)) {
            langDropdown.style.opacity = '0';
            langDropdown.style.transform = 'translateY(-10px)';
            setTimeout(() => { langDropdown.style.display = 'none'; }, 300);
            isLangDropdownOpen = false;
            window.isLangDropdownOpen = false;
        }
    });
}

function setupEventListeners() {
    // Setup navigation
    setupNavigation();
    
    // Initialize DOM elements
    urlInput = document.getElementById('urlInput');
    analyzeBtn = document.getElementById('analyzeBtn');
    loadingIndicator = document.getElementById('loadingIndicator');
    videoInfo = document.getElementById('videoInfo');
    formatsSection = document.getElementById('formatsSection');
    advancedOptions = document.getElementById('advancedOptions');
    downloadSection = document.getElementById('downloadSection');
    progressSection = document.getElementById('progressSection');
    consoleSection = document.getElementById('consoleSection');
    pasteBtn = document.getElementById('pasteBtn');
    clearBtn = document.getElementById('clearBtn');
    // History elements
    historyBtn = document.getElementById('historyBtn');
    historyDropdown = document.getElementById('historyDropdown');
    historyList = document.getElementById('historyList');
    historyEmpty = document.getElementById('historyEmpty');
    clearHistoryBtn = document.getElementById('clearHistoryBtn');
    closeHistoryBtn = document.getElementById('closeHistoryBtn');
    
    // Setup drag once (avoid duplicate listeners on each open)
    if (historyDropdown) setupDraggable(historyDropdown);
    
    console.log('[HISTORY] DOM Elements initialized:');
    console.log('[HISTORY] historyBtn:', historyBtn);
    console.log('[HISTORY] historyDropdown:', historyDropdown);
    console.log('[HISTORY] historyList:', historyList);
    console.log('[HISTORY] historyEmpty:', historyEmpty);
    console.log('[HISTORY] clearHistoryBtn:', clearHistoryBtn);
    console.log('[HISTORY] closeHistoryBtn:', closeHistoryBtn);
    
    // Setup ytdlp dropdown
    setupYtdlpDropdown();
    
    // Initialize analysis console
    initAnalysisConsole();
    
    // Analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeURL);
        console.log('Bouton analyser trouvé et événement attaché');
    } else {
        console.error('Bouton analyser non trouvé');
    }
    
    // Enter key on URL input
    if (urlInput) {
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                analyzeURL();
            }
        });
    }
    
    // Download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', startDownload);
        // Initially disable the download button
        downloadBtn.disabled = true;
    }

    // Function to check if download should be enabled
    window.updateDownloadButtonState = function() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (!downloadBtn) return;

        // Check if any format is selected for single video
        const hasFormat = selectedVideoFormat || selectedAudioFormat || selectedCombinedFormat;
        
        // Check if it's a playlist
        let hasPlaylist = false;
        let hasPlaylistFormat = false;
        if (currentVideoData && currentVideoData.is_playlist) {
            hasPlaylist = true;
            
            // Get selected videos
            const selectedVideos = [];
            document.querySelectorAll('.playlist-video-checkbox:checked').forEach(cb => {
                const item = cb.closest('.playlist-video-item');
                if (item) {
                    const videoId = item.dataset.videoId;
                    selectedVideos.push(videoId);
                }
            });
            
            // Check if any selected video has a format selected
            hasPlaylistFormat = selectedVideos.some(videoId => {
                const selection = playlistSelections[videoId];
                return selection && selection.formatId;
            });
        }
        
        // Check if subtitles are selected for separate download
        const writeAutoSubsChecked = document.getElementById('writeAutoSubs')?.checked || false;
        const selectedSubtitles = getSelectedSubtitles();
        const hasSubtitlesForDownload = writeAutoSubsChecked && selectedSubtitles && selectedSubtitles.length > 0;

        // Enable download button if:
        // - Single video: format is selected OR subtitles are selected
        // - Playlist: at least one video is selected (with or without format) OR subtitles are selected
        if (hasPlaylist) {
            // For playlists, enable if at least one video is selected OR subtitles are selected
            const hasSelectedVideos = document.querySelectorAll('.playlist-video-checkbox:checked').length > 0;
            downloadBtn.disabled = !(hasSelectedVideos || hasSubtitlesForDownload);
        } else {
            // For single videos, enable if format is selected OR subtitles are selected
            downloadBtn.disabled = !(hasFormat || hasSubtitlesForDownload);
        }
    }

    // Add event listeners to update download button state
    document.getElementById('writeAutoSubs')?.addEventListener('change', window.updateDownloadButtonState);
    document.getElementById('burnSubs')?.addEventListener('change', window.updateDownloadButtonState);
    
    // Add event listener for skip format selection checkbox
    document.getElementById('skipFormatSelection')?.addEventListener('change', function(e) {
        if (e.target.checked) {
            // Deselect all formats when skip is checked
            clearAllFormatSelections();
        }
        window.updateDownloadButtonState();
    });

    // Update button state when formats are selected (call this in selectVideoFormat, selectAudioFormat, selectCombinedFormat)
    
    // Cancel button
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelDownload);
    }
    
    // Pause button
    const pauseBtn = document.getElementById('pauseBtn');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', pauseDownload);
    }
    
    // Resume button
    const resumeBtn = document.getElementById('resumeBtn');
    if (resumeBtn) {
        resumeBtn.addEventListener('click', resumeDownload);
    }
    
    // Clear console
    const clearConsole = document.getElementById('clearConsole');
    if (clearConsole) {
        clearConsole.addEventListener('click', () => {
            const consoleOutput = document.getElementById('consoleOutput');
            if (consoleOutput) {
                consoleOutput.innerHTML = '';
            }
        });
    }

    // Copy console logs
    const copyConsole = document.getElementById('copyConsole');
    if (copyConsole) {
        copyConsole.addEventListener('click', () => {
            const consoleOutput = document.getElementById('consoleOutput');
            if (consoleOutput) {
                const text = Array.from(consoleOutput.querySelectorAll('.console-line'))
                    .map(line => line.textContent)
                    .join('\n');
                navigator.clipboard.writeText(text).then(() => {
                    mariharAlert(t('alert_copied'), 'success');
                }).catch(() => {
                    mariharAlert(t('alert_copy_error'), 'error');
                });
            }
        });
    }
    
    // Toggle subtitle style options
    const burnSubs = document.getElementById('burnSubs');
    if (burnSubs) {
        burnSubs.addEventListener('change', (e) => {
            const styleOptions = document.getElementById('subtitleStyleOptions');
            if (styleOptions) {
                if (e.target.checked) {
                    styleOptions.classList.remove('hidden');
                } else {
                    styleOptions.classList.add('hidden');
                }
            }
        });
    }

    // Dropdown À propos - Animation sans flèche
    const aboutDropdownToggle = document.getElementById('aboutDropdownToggle');
    const aboutDropdown = document.getElementById('aboutDropdown');
    let isAboutDropdownOpen = false;
    
    if (aboutDropdownToggle && aboutDropdown) {
        aboutDropdownToggle.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Animation de l'icône
            aboutDropdownToggle.style.transform = 'scale(0.95)';
            setTimeout(() => {
                aboutDropdownToggle.style.transform = 'scale(1)';
            }, 150);
            
            // Obtenir la position de l'icône pour positionner le dropdown
            const rect = aboutDropdownToggle.getBoundingClientRect();
            
            // Toggle dropdown avec animation
            if (!isAboutDropdownOpen) {
                // Afficher temporairement pour mesurer la largeur
                aboutDropdown.style.display = 'block';
                aboutDropdown.style.visibility = 'hidden';
                aboutDropdown.style.opacity = '0';
                aboutDropdown.style.transform = 'translateY(-10px)';
                
                // Mesurer la largeur réelle du dropdown
                const dropdownWidth = aboutDropdown.offsetWidth;
                
                // Calculer left pour aligner le coin droit du dropdown avec le coin droit de l'icône
                const leftPosition = rect.right - dropdownWidth;
                
                // Appliquer la position
                aboutDropdown.style.top = (rect.bottom + 5) + 'px';
                aboutDropdown.style.left = leftPosition + 'px';
                aboutDropdown.style.right = 'auto';
                aboutDropdown.style.visibility = 'visible';
                
                setTimeout(() => {
                    aboutDropdown.style.opacity = '1';
                    aboutDropdown.style.transform = 'translateY(0)';
                }, 10);
                
                isAboutDropdownOpen = true;
            } else {
                aboutDropdown.style.opacity = '0';
                aboutDropdown.style.transform = 'translateY(-10px)';
                
                setTimeout(() => {
                    aboutDropdown.style.display = 'none';
                }, 300);
                
                isAboutDropdownOpen = false;
            }
        });
        
        // Fermer le dropdown en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (isAboutDropdownOpen && 
                !aboutDropdownToggle.contains(e.target) && 
                !aboutDropdown.contains(e.target)) {
                aboutDropdown.style.opacity = '0';
                aboutDropdown.style.transform = 'translateY(-10px)';
                
                setTimeout(() => {
                    aboutDropdown.style.display = 'none';
                }, 300);
                
                isAboutDropdownOpen = false;
            }
        });
    }

    // Sélection du dossier de sortie (desktop)
    const outputDirBrowseBtn = document.getElementById('outputDirBrowseBtn');
    if (outputDirBrowseBtn) {
        outputDirBrowseBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/select-folder');
                const result = await response.json();
                if (result.success && result.path) {
                    document.getElementById('outputDirInput').value = result.path;
                }
            } catch (error) {
                console.error('Folder selection error:', error);
                mariharError(t('alert_folder_error'));
            }
        });
    }
    
    // URL Input - Paste and Clear buttons setup
    console.log('Setting up URL input buttons, elements:', { 
        urlInput: !!urlInput, 
        pasteBtn: !!pasteBtn, 
        clearBtn: !!clearBtn 
    });
    
    // Fonction pour mettre à jour les boutons
    function updateInputButtons() {
        if (!urlInput || !pasteBtn || !clearBtn) return;
        
        const hasValue = urlInput.value.trim().length > 0;
        
        if (hasValue) {
            // Il y a du texte : cacher Coller, montrer Supprimer
            pasteBtn.classList.add('hidden');
            clearBtn.classList.remove('hidden');
        } else {
            // Pas de texte : montrer Coller, cacher Supprimer
            pasteBtn.classList.remove('hidden');
            clearBtn.classList.add('hidden');
        }
    }
    
    // Initialiser l'état des boutons au chargement
    updateInputButtons();
    
    // Paste button
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            urlInput.value = text;
            updateInputButtons();
            urlInput.focus();
        } catch (err) {
            console.error('Failed to read clipboard:', err);
            mariharError(t('alert_clipboard_error'));
        }
    });
    
    // Clear button
    clearBtn.addEventListener('click', () => {
        urlInput.value = '';
        updateInputButtons();
        urlInput.focus();
    });
    
    // Écouter tous les événements possibles sur l'input
    urlInput.addEventListener('input', updateInputButtons);
    urlInput.addEventListener('keyup', updateInputButtons);
    urlInput.addEventListener('keydown', updateInputButtons);
    urlInput.addEventListener('change', updateInputButtons);
    urlInput.addEventListener('focus', updateInputButtons);
    urlInput.addEventListener('blur', updateInputButtons);
    
    // Écouter l'événement paste
    urlInput.addEventListener('paste', (e) => {
        // Attendre que le paste soit effectué
        setTimeout(() => {
            updateInputButtons();
        }, 50);
    });
    
    // Vérifier périodiquement (pour les cas où le navigateur auto-remplit)
    setInterval(updateInputButtons, 500);
    
    // ========== SEARCH MODE CUSTOM LIMIT ==========
    const searchModeSelect = document.getElementById('searchMode');
    const customSearchLimitInput = document.getElementById('customSearchLimit');
    
    if (searchModeSelect && customSearchLimitInput) {
        searchModeSelect.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                customSearchLimitInput.classList.remove('hidden');
                customSearchLimitInput.focus();
            } else {
                customSearchLimitInput.classList.add('hidden');
            }
        });
    }
    
    // ========== HISTORY FUNCTIONALITY ==========

    // History button toggle
    if (historyBtn) {
        console.log('[HISTORY] History button found, adding event listener');
        historyBtn.addEventListener('click', async (e) => {
            console.log('[HISTORY] History button clicked');
            e.preventDefault();
            e.stopPropagation();
            
            if (!isHistoryDropdownOpen) {
                console.log('[HISTORY] Opening dropdown');
                await loadHistory();
                openHistoryDropdown();
            } else {
                console.log('[HISTORY] Closing dropdown');
                closeHistoryDropdown();
            }
        });
    } else {
        console.error('[HISTORY] History button NOT found!');
    }
    
    // Clear history button
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (confirm('Voulez-vous vraiment vider l\'historique ?')) {
                await clearHistory();
            }
        });
    }
    
    // Close history button
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeHistoryDropdown();
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!isHistoryDropdownOpen) return;
        // Use composedPath() to correctly handle SVG child elements
        const path = e.composedPath();
        const insideDropdown = path.some(el => el === historyDropdown);
        const insideBtn = path.some(el => el === historyBtn);
        if (!insideDropdown && !insideBtn) {
            closeHistoryDropdown();
        }
    });
    
    // Load history on page load
    window.addEventListener('load', () => {
        // Preload history in background
        loadHistory();
    });
    
    // Column collapse/expand functionality
    setupColumnCollapse();
    
    // Preview subtitle style
    document.getElementById('previewSubtitleBtn').addEventListener('click', async () => {
        const previewDiv = document.getElementById('subtitlePreview');
        const previewImg = previewDiv.querySelector('img');
        
        const subStyle = {
            color: document.getElementById('subColor').value,
            outline_color: document.getElementById('subOutlineColor').value,
            font_size: parseInt(document.getElementById('subFontSize').value),
            position: parseInt(document.getElementById('subPosition').value),
            outline: parseInt(document.getElementById('subOutline').value),
            font_style: parseInt(document.getElementById('subFontStyle').value)
        };
        
        try {
            const response = await fetch('/api/preview_subtitle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sub_style: subStyle })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                previewImg.src = url;
                previewDiv.classList.remove('hidden');
            } else {
                mariharError(t('alert_preview_error'));
            }
        } catch (error) {
            console.error('Preview error:', error);
            mariharError(t('alert_preview_error'));
        }
    });

    // Table sorting
    setupTableSorting();
}

// ==================== YTDLP UPDATE / CUSTOM ====================
function setupYtdlpDropdown() {
    const ytdlpDropdownToggle = document.getElementById('ytdlpDropdownToggle');
    const ytdlpDropdown = document.getElementById('ytdlpDropdown');
    const ytdlpAutoUpdateBtn = document.getElementById('ytdlpAutoUpdateBtn');
    const ytdlpPickCustomBtn = document.getElementById('ytdlpPickCustomBtn');
    const ytdlpResetToDefaultBtn = document.getElementById('ytdlpResetToDefaultBtn');

    console.log('[YTDLP Dropdown] Elements found:', {
        toggle: !!ytdlpDropdownToggle,
        dropdown: !!ytdlpDropdown,
        autoUpdateBtn: !!ytdlpAutoUpdateBtn,
        pickCustomBtn: !!ytdlpPickCustomBtn,
        resetToDefaultBtn: !!ytdlpResetToDefaultBtn
    });

    // Log pour vérifier si la fonction est appelée
    console.log('[YTDLP Dropdown] setupYtdlpDropdown called');

    let isYtdlpDropdownOpen = false;

    function closeYtdlpDropdown() {
        if (!ytdlpDropdown) return;
        ytdlpDropdown.style.opacity = '0';
        ytdlpDropdown.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            ytdlpDropdown.style.display = 'none';
        }, 200);
        isYtdlpDropdownOpen = false;
    }

    function openYtdlpDropdown() {
        if (!ytdlpDropdownToggle || !ytdlpDropdown) return;

        const rect = ytdlpDropdownToggle.getBoundingClientRect();

        // afficher temporairement pour mesurer
        ytdlpDropdown.style.display = 'block';
        ytdlpDropdown.style.visibility = 'hidden';
        ytdlpDropdown.style.opacity = '0';
        ytdlpDropdown.style.transform = 'translateY(-10px)';
        ytdlpDropdown.style.border = 'none';
        ytdlpDropdown.style.boxShadow = 'none';
        ytdlpDropdown.style.background = '#1a1a2e';
        ytdlpDropdown.style.borderRadius = '12px';
        ytdlpDropdown.style.padding = '8px';

        const dropdownWidth = ytdlpDropdown.offsetWidth;
        const leftPosition = rect.right - dropdownWidth;

        ytdlpDropdown.style.top = (rect.bottom + 5) + 'px';
        ytdlpDropdown.style.left = leftPosition + 'px';
        ytdlpDropdown.style.right = 'auto';
        ytdlpDropdown.style.visibility = 'visible';

        setTimeout(() => {
            ytdlpDropdown.style.opacity = '1';
            ytdlpDropdown.style.transform = 'translateY(0)';
            ytdlpDropdown.style.border = 'none';
            ytdlpDropdown.style.boxShadow = 'none';
            ytdlpDropdown.style.background = '#1a1a2e';
            ytdlpDropdown.style.borderRadius = '12px';
            ytdlpDropdown.style.padding = '8px';
        }, 10);

        isYtdlpDropdownOpen = true;
    }

    if (ytdlpDropdownToggle && ytdlpDropdown) {
        ytdlpDropdownToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            ytdlpDropdownToggle.style.transform = 'scale(0.95)';
            setTimeout(() => { ytdlpDropdownToggle.style.transform = 'scale(1)'; }, 150);

            // Vérifier si on est sur la page yt-dlp
            const ytdlpPage = document.getElementById('ytdlpPage');
            const isOnYtdlpPage = ytdlpPage && ytdlpPage.classList.contains('active');

            if (!isOnYtdlpPage) {
                // Premier clic : naviguer vers la page yt-dlp et ouvrir le dropdown
                navigateToPage('ytdlp');
                setTimeout(() => {
                    openYtdlpDropdown();
                }, 100);
            } else {
                // Deuxième clic : ouvrir/fermer le dropdown
                if (!isYtdlpDropdownOpen) openYtdlpDropdown();
                else closeYtdlpDropdown();
            }
        });

        // Fermer le dropdown quand on clique en dehors
        document.addEventListener('click', (e) => {
            if (!isYtdlpDropdownOpen) return;
            // Vérifier si le clic est sur le dropdown ou le toggle
            const clickedInsideDropdown = ytdlpDropdown.contains(e.target);
            const clickedOnToggle = ytdlpDropdownToggle.contains(e.target);
            const clickedOnButtons = e.target.closest('#ytdlpAutoUpdateBtn') || e.target.closest('#ytdlpPickCustomBtn');

            console.log('[YTDLP Dropdown] Click detected:', {
                insideDropdown: clickedInsideDropdown,
                onToggle: clickedOnToggle,
                onButtons: clickedOnButtons,
                target: e.target.tagName,
                targetId: e.target.id
            });

            if (!clickedInsideDropdown && !clickedOnToggle && !clickedOnButtons) {
                console.log('[YTDLP Dropdown] Closing dropdown');
                closeYtdlpDropdown();
            }
        });
    }

    async function callPickCustomYtdlp() {
        if (!window.pywebview || !window.pywebview.api) {
            throw new Error("API desktop non disponible (window.pywebview.api manquant).");
        }

        // Essayer plusieurs noms possibles selon l'implémentation PyWebView
        const api = window.pywebview.api;

        if (typeof api.pick_ytdlp_exe === 'function') {
            return api.pick_ytdlp_exe();
        }
        if (typeof api.select_ytdlp_exe === 'function') {
            return api.select_ytdlp_exe();
        }
        if (typeof api.select_yt_dlp_exe === 'function') {
            return api.select_yt_dlp_exe();
        }

        throw new Error("Fonction de sélection manquante côté Python. Attendu: pick_ytdlp_exe (ou équivalent).");
    }

    if (ytdlpAutoUpdateBtn) {
        console.log('[YTDLP Dropdown] Attaching listener to auto update button');
        ytdlpAutoUpdateBtn.addEventListener('click', async (e) => {
            console.log('[YTDLP Dropdown] Auto update button clicked');
            e.preventDefault();
            e.stopPropagation();

            closeYtdlpDropdown();

            // Afficher un modal de progression bloquant
            showMariharDialog({
                title: t('ytdlp_update_title'),
                message: t('ytdlp_update_message'),
                variant: 'info',
                hideCancel: true,
                confirmText: t('dialog_ok'),
                showProgress: true,
                onConfirm: () => {
                    // Fermer le modal
                }
            });

            try {
                const response = await fetch('/api/ytdlp/update-auto', { method: 'POST' });
                const result = await response.json();

                // Mettre à jour le modal avec le résultat
                const dialogOverlay = document.getElementById('mariharDialogOverlay');
                const dialogMessage = document.getElementById('mariharDialogMessage');
                const dialogTitle = document.getElementById('mariharDialogTitle');
                const dialogConfirmBtn = document.getElementById('mariharDialogConfirm');

                console.log('[YTDLP Update] Modal elements:', {
                    overlay: !!dialogOverlay,
                    message: !!dialogMessage,
                    title: !!dialogTitle,
                    confirm: !!dialogConfirmBtn
                });

                if (dialogOverlay && dialogMessage && dialogTitle) {
                    // Mettre à jour le titre
                    dialogTitle.textContent = t('ytdlp_update_result_title');

                    // Formater la sortie comme une console
                    const consoleOutput = `[YTDLP API] Requête reçue: /api/ytdlp/update-auto
[YTDLP API] Chemin yt-dlp: ${result.path || 'N/A'}
[YTDLP API] Lancement mise à jour
[YTDLP API] Sortie de yt-dlp -U:
${result.output || 'Aucune sortie'}

[YTDLP API] Statut: ${result.status}
[YTDLP API] Message: ${result.message}`;

                    dialogMessage.textContent = consoleOutput;
                    dialogMessage.style.fontFamily = 'Consolas, Monaco, monospace';
                    dialogMessage.style.fontSize = '12px';
                    dialogMessage.style.whiteSpace = 'pre-wrap';
                    dialogMessage.style.textAlign = 'left';

                    // Changer la couleur selon le statut
                    if (result.status === 'already_up_to_date') {
                        dialogMessage.style.color = '#4a90e2'; // Bleu
                    } else if (result.status === 'updated') {
                        dialogMessage.style.color = '#4caf50'; // Vert
                    } else if (result.status === 'error') {
                        dialogMessage.style.color = '#f44336'; // Rouge
                    } else {
                        dialogMessage.style.color = '#ffffff'; // Blanc
                    }

                    // Cacher la progression
                    const progressBar = dialogOverlay.querySelector('.dialog-progress');
                    if (progressBar) {
                        progressBar.style.display = 'none';
                    }

                    // Mettre à jour le bouton
                    if (dialogConfirmBtn) {
                        dialogConfirmBtn.textContent = t('dialog_ok');
                        dialogConfirmBtn.onclick = () => {
                            closeMariharDialog();
                        };
                    }
                } else {
                    // Fallback si le modal n'existe pas
                    closeMariharDialog();
                    if (!result.success) {
                        mariharError(result.message || 'Échec mise à jour', 'MARIHAR');
                        return;
                    }
                    mariharAlert(result.message, 'info', 'MARIHAR');
                }

                // Afficher la sortie complète dans la console pour débogage
                console.log('[YTDLP Update] Output:', result.output);
            } catch (error) {
                const dialogOverlay = document.getElementById('mariharDialogOverlay');
                const dialogMessage = document.getElementById('mariharDialogMessage');
                const dialogTitle = document.getElementById('mariharDialogTitle');
                if (dialogOverlay && dialogMessage && dialogTitle) {
                    dialogTitle.textContent = 'Erreur';
                    dialogMessage.textContent = 'Erreur réseau: ' + error.message;
                    dialogMessage.style.color = '#f44336';
                } else {
                    document.getElementById('mariharDialogOverlay').style.display = 'none';
                    mariharError('Erreur réseau: ' + error.message, 'MARIHAR');
                }
            }
        });
    } else {
        console.error('[YTDLP Dropdown] Auto update button not found!');
    }

    if (ytdlpPickCustomBtn) {
        console.log('[YTDLP Dropdown] Attaching listener to pick custom button');
        ytdlpPickCustomBtn.addEventListener('click', async (e) => {
            console.log('[YTDLP Dropdown] Pick custom button clicked');
            e.preventDefault();
            e.stopPropagation();

            closeYtdlpDropdown();

            // Afficher un modal de progression bloquant
            showMariharDialog({
                title: t('ytdlp_pick_title'),
                message: t('ytdlp_pick_message'),
                variant: 'info',
                hideCancel: true,
                confirmText: t('dialog_ok'),
                showProgress: true,
                onConfirm: () => {
                    // Fermer le modal
                }
            });

            try {
                // Mettre à jour le message pour indiquer que la boîte de dialogue va s'ouvrir
                const dialogOverlay = document.getElementById('mariharDialogOverlay');
                const dialogMessage = document.getElementById('mariharDialogMessage');
                if (dialogOverlay && dialogMessage) {
                    dialogMessage.textContent = t('ytdlp_pick_opening');
                }

                const pickedPath = await callPickCustomYtdlp();

                if (!pickedPath || typeof pickedPath !== 'string') {
                    // Mettre à jour le modal avec l'erreur
                    if (dialogOverlay && dialogMessage) {
                        const dialogTitle = document.getElementById('mariharDialogTitle');
                        const dialogConfirmBtn = document.getElementById('mariharDialogConfirm');

                        if (dialogTitle) {
                            dialogTitle.textContent = t('ytdlp_pick_error_title');
                        }
                        dialogMessage.textContent = t('ytdlp_pick_error_path');
                        dialogMessage.style.color = '#f44336';

                        const progressBar = dialogOverlay.querySelector('.dialog-progress');
                        if (progressBar) {
                            progressBar.style.display = 'none';
                        }

                        if (dialogConfirmBtn) {
                            dialogConfirmBtn.textContent = t('dialog_ok');
                            dialogConfirmBtn.onclick = () => {
                                closeMariharDialog();
                            };
                        }
                    } else {
                        closeMariharDialog();
                        mariharError(t('ytdlp_pick_error_short'), 'MARIHAR');
                    }
                    return;
                }

                // Mettre à jour le message pour indiquer l'envoi au serveur
                if (dialogOverlay && dialogMessage) {
                    dialogMessage.textContent = 'Enregistrement du chemin...\n\nVeuillez patienter.';
                }

                // Envoyer le chemin au serveur
                const response = await fetch('/api/ytdlp/custom-ytdlp-path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: pickedPath })
                });

                const result = await response.json();

                // Mettre à jour le modal avec le résultat
                const dialogTitle = document.getElementById('mariharDialogTitle');
                const dialogConfirmBtn = document.getElementById('mariharDialogConfirm');

                if (dialogOverlay && dialogMessage && dialogTitle) {
                    // Mettre à jour le titre
                    dialogTitle.textContent = t('ytdlp_pick_result_title');

                    // Formater la sortie comme une console
                    const consoleOutput = `[YTDLP PICK] Fonction pick_ytdlp_exe appelée
[YTDLP PICK] Fichier sélectionné: ${pickedPath}
[YTDLP API] Requête reçue: /api/ytdlp/custom-ytdlp-path
[YTDLP API] Données reçues: {'path': '${pickedPath}'}
[YTDLP API] Chemin custom: ${pickedPath}
[YTDLP API] Chemin config: ${result.config_path || 'N/A'}
[YTDLP API] Config sauvegardée: ${pickedPath}
[YTDLP API] Service mis à jour avec succès
[YTDLP API] Succès: ${result.message}`;

                    dialogMessage.textContent = consoleOutput;
                    dialogMessage.style.fontFamily = 'Consolas, Monaco, monospace';
                    dialogMessage.style.fontSize = '12px';
                    dialogMessage.style.whiteSpace = 'pre-wrap';
                    dialogMessage.style.textAlign = 'left';
                    dialogMessage.style.color = '#4caf50'; // Vert pour succès

                    // Cacher la progression
                    const progressBar = dialogOverlay.querySelector('.dialog-progress');
                    if (progressBar) {
                        progressBar.style.display = 'none';
                    }

                    // Mettre à jour le bouton
                    if (dialogConfirmBtn) {
                        dialogConfirmBtn.textContent = t('dialog_ok');
                        dialogConfirmBtn.onclick = () => {
                            closeMariharDialog();
                        };
                    }
                } else {
                    closeMariharDialog();
                    if (!result.success) {
                        mariharError(result.error || 'Échec enregistrement', 'MARIHAR');
                        return;
                    }
                    mariharAlert(result.message, 'success', 'MARIHAR');
                }
            } catch (error) {
                const dialogOverlay = document.getElementById('mariharDialogOverlay');
                const dialogMessage = document.getElementById('mariharDialogMessage');
                const dialogTitle = document.getElementById('mariharDialogTitle');
                if (dialogOverlay && dialogMessage && dialogTitle) {
                    dialogTitle.textContent = 'Erreur';
                    dialogMessage.textContent = 'Erreur: ' + error.message;
                    dialogMessage.style.color = '#f44336';

                    const progressBar = dialogOverlay.querySelector('.dialog-progress');
                    if (progressBar) {
                        progressBar.style.display = 'none';
                    }

                    const dialogConfirmBtn = document.getElementById('mariharDialogConfirm');
                    if (dialogConfirmBtn) {
                        dialogConfirmBtn.textContent = t('dialog_ok');
                        dialogConfirmBtn.onclick = () => {
                            closeMariharDialog();
                        };
                    }
                } else {
                    closeMariharDialog();
                    mariharError(String(error.message || error), 'MARIHAR');
                }
            }
        });
    } else {
        console.error('[YTDLP Dropdown] Pick custom button not found!');
    }

    if (ytdlpResetToDefaultBtn) {
        console.log('[YTDLP Dropdown] Attaching listener to reset to default button');
        ytdlpResetToDefaultBtn.addEventListener('click', async (e) => {
            console.log('[YTDLP Dropdown] Reset to default button clicked');
            e.preventDefault();
            e.stopPropagation();

            closeYtdlpDropdown();

            try {
                const response = await fetch('/api/ytdlp/reset-to-default', { method: 'POST' });
                const result = await response.json();

                if (!result.success) {
                    mariharError(result.error || 'Échec réinitialisation', 'MARIHAR');
                    return;
                }

                mariharAlert(t('ytdlp_reset_success'), 'success', 'MARIHAR');
            } catch (error) {
                mariharError(t('ytdlp_network_error') + error.message, 'MARIHAR');
            }
        });
    } else {
        console.error('[YTDLP Dropdown] Reset to default button not found!');
    }
}

// ==================== ANALYZE URL ====================

// ==================== ANALYSIS CONSOLE ====================

let currentAnalysisTaskId = null;
let analysisProgressInterval = null;
let analysisIsRunning = false;
let elapsedTimerInterval = null;
let analysisStartTime = null;

function initAnalysisConsole() {
    const cancelBtn = document.getElementById('cancelAnalysisBtn');

    // Cancel analysis button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            if (analysisIsRunning) {
                showCancelAnalysisConfirmation();
            }
        });
    }
}

function showAnalysisConsole() {
    const section = document.getElementById('analysisConsoleSection');
    const logs = document.getElementById('analysisConsoleLogs');
    section.classList.remove('hidden');
    logs.innerHTML = '';
}

function hideAnalysisConsole() {
    const section = document.getElementById('analysisConsoleSection');
    section.classList.add('hidden');
}

function addAnalysisLog(message, type = 'info') {
    const logs = document.getElementById('analysisConsoleLogs');
    const line = document.createElement('div');
    line.className = `analysis-log-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logs.appendChild(line);
    logs.scrollTop = logs.scrollHeight;
}

function showCancelAnalysisConfirmation() {
    const confirmText = window.currentLang === 'en' ? 'Cancel Analysis' :
                        window.currentLang === 'it' ? 'Annulla Analisi' :
                        window.currentLang === 'mg' ? 'Ajanony ny fanadihadiana' :
                        'Annuler l\'analyse';
    const cancelText = window.currentLang === 'en' ? 'Continue' :
                       window.currentLang === 'it' ? 'Continua' :
                       window.currentLang === 'mg' ? 'Hanohy' :
                       'Continuer';
    const message = window.currentLang === 'en' ? 'Are you sure you want to cancel the current analysis?' :
                    window.currentLang === 'it' ? 'Sei sicuro di voler annullare l\'analisi in corso?' :
                    window.currentLang === 'mg' ? 'Azonao antoka fa te hijanona ny fanadihadiana?' :
                    'Voulez-vous vraiment annuler l\'analyse en cours ?';
    
    showMariharDialog({
        variant: 'warning',
        title: confirmText,
        message: message,
        confirmText: confirmText,
        cancelText: cancelText,
        onConfirm: () => {
            cancelCurrentAnalysis();
        }
    });
}

async function cancelCurrentAnalysis() {
    if (!currentAnalysisTaskId) return;
    
    try {
        const response = await fetch(`/api/analyze/cancel/${currentAnalysisTaskId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            addAnalysisLog('Analyse annulée par l\'utilisateur', 'warning');
            analysisIsRunning = false;
            
            // Hide cancel button but keep elapsed time visible
            const cancelBtn = document.getElementById('cancelAnalysisBtn');
            if (cancelBtn) cancelBtn.classList.add('hidden');
            
            // Stop timers
            if (analysisProgressInterval) {
                clearInterval(analysisProgressInterval);
                analysisProgressInterval = null;
            }
            if (elapsedTimerInterval) {
                clearInterval(elapsedTimerInterval);
                elapsedTimerInterval = null;
            }
            
            // Re-enable analyze button
            loadingIndicator.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    } catch (error) {
        addAnalysisLog('Erreur lors de l\'annulation: ' + error.message, 'error');
    }
}

function updateElapsedTime() {
    if (!analysisStartTime) return;
    
    const elapsed = Math.floor((Date.now() - analysisStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    const elapsedText = document.getElementById('elapsedTimeText');
    if (elapsedText) {
        elapsedText.textContent = timeStr;
    }
}

// ==================== HISTORY FUNCTIONS ====================

let currentHistory = [];

async function loadHistory() {
    console.log('[HISTORY] loadHistory() called');
    try {
        const response = await fetch('/api/history');
        const result = await response.json();
        console.log('[HISTORY] loadHistory() response:', result);
        if (result.success) {
            currentHistory = result.history;
            console.log('[HISTORY] Loaded', currentHistory.length, 'history items');
            return result.history;
        }
        return [];
    } catch (error) {
        console.error('[HISTORY] Failed to load history:', error);
        return [];
    }
}

function openHistoryDropdown() {
    console.log('[HISTORY] openHistoryDropdown() called');
    console.log('[HISTORY] historyDropdown element:', historyDropdown);
    if (!historyDropdown) {
        console.error('[HISTORY] historyDropdown element is NULL!');
        return;
    }
    
    // Calculate position under the history button
    const rect = historyBtn.getBoundingClientRect();
    const dropdownWidth = 400; // Same as CSS width
    
    // Position dropdown below the button
    historyDropdown.style.top = (rect.bottom + 8) + 'px';
    
    // Align right edge with button right edge
    historyDropdown.style.right = (window.innerWidth - rect.right) + 'px';
    historyDropdown.style.left = 'auto';
    
    // Ensure dropdown doesn't go off-screen on the right
    const rightEdge = rect.right;
    if (rightEdge + dropdownWidth > window.innerWidth) {
        historyDropdown.style.right = '20px';
        historyDropdown.style.left = 'auto';
    }
    
    // Ensure dropdown doesn't go off-screen on the left
    if (rect.right - dropdownWidth < 20) {
        historyDropdown.style.left = '20px';
        historyDropdown.style.right = 'auto';
    }
    
    historyDropdown.classList.remove('hidden');
    historyDropdown.classList.add('draggable');
    console.log('[HISTORY] Removed hidden class, classes:', historyDropdown.className);
    
    // Force reflow to allow transition
    historyDropdown.offsetHeight;
    historyDropdown.style.opacity = '1';
    historyDropdown.style.transform = 'translateY(0)';
    
    isHistoryDropdownOpen = true;
    console.log('[HISTORY] Dropdown opened, isHistoryDropdownOpen = true');
    renderHistoryItems();
}

function closeHistoryDropdown() {
    if (!historyDropdown) return;
    historyDropdown.style.opacity = '0';
    historyDropdown.style.transform = 'translateY(-10px)';
    historyDropdown.classList.remove('draggable');
    setTimeout(() => { historyDropdown.classList.add('hidden'); }, 200);
    isHistoryDropdownOpen = false;
}

function setupDraggable(element) {
    console.log('[HISTORY] setupDraggable() called');
    const header = element.querySelector('.history-dropdown-header');
    if (!header) {
        console.error('[HISTORY] Header not found for drag functionality');
        return;
    }
    
    let isDragging = false;
    let startX, startY, initialX, initialY;
    
    header.addEventListener('mousedown', (e) => {
        // Don't drag if clicking on action buttons
        if (e.target.closest('#clearHistoryBtn') || e.target.closest('#closeHistoryBtn')) return;
        
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        
        // Get current position
        const rect = element.getBoundingClientRect();
        initialX = rect.left;
        initialY = rect.top;
        
        // Remove transitions during drag
        element.style.transition = 'none';
        element.style.cursor = 'grabbing';
        header.style.cursor = 'grabbing';
        
        console.log('[HISTORY] Drag started at:', startX, startY);
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        e.preventDefault();
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        const newX = initialX + deltaX;
        const newY = initialY + deltaY;
        
        // Keep dropdown within viewport bounds
        const maxX = window.innerWidth - element.offsetWidth;
        const maxY = window.innerHeight - element.offsetHeight;
        
        const constrainedX = Math.max(0, Math.min(newX, maxX));
        const constrainedY = Math.max(0, Math.min(newY, maxY));
        
        element.style.left = constrainedX + 'px';
        element.style.top = constrainedY + 'px';
        element.style.right = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            element.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
            element.style.cursor = 'move';
            header.style.cursor = 'move';
            console.log('[HISTORY] Drag ended');
        }
    });
}

function renderHistoryItems() {
    console.log('[HISTORY] renderHistoryItems() called');
    const historyList = document.getElementById('historyList');
    const historyEmpty = document.getElementById('historyEmpty');
    
    console.log('[HISTORY] historyList element:', historyList);
    console.log('[HISTORY] historyEmpty element:', historyEmpty);
    console.log('[HISTORY] currentHistory:', currentHistory);
    
    if (!currentHistory || currentHistory.length === 0) {
        console.log('[HISTORY] No history items, showing empty state');
        historyList.innerHTML = '';
        historyEmpty.classList.remove('hidden');
        return;
    }
    
    console.log('[HISTORY] Rendering', currentHistory.length, 'history items');
    historyEmpty.classList.add('hidden');
    
    historyList.innerHTML = '';
    
    currentHistory.forEach((item, index) => {
        console.log('[HISTORY] Rendering item', index, ':', item);
        const itemDiv = document.createElement('div');
        itemDiv.className = 'history-item';
        itemDiv.dataset.id = item.id;
        itemDiv.dataset.query = item.query;
        itemDiv.dataset.type = item.type;
        
        const iconSvg = item.type === 'url' 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>`
            : `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
        
        const dateStr = new Date(item.timestamp * 1000).toLocaleString();
        
        itemDiv.innerHTML = `
            <div class="history-item-icon">${iconSvg}</div>
            <div class="history-item-content">
                <div class="history-item-query">${escapeHtml(item.query)}</div>
                <div class="history-item-date">${dateStr}</div>
            </div>
            <button class="history-item-delete" title="Supprimer">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;
        
        // Handle click on item (except delete button)
        itemDiv.addEventListener('click', (e) => {
            if (!e.target.closest('.history-item-delete')) {
                handleHistoryItemClick(item.query);
            }
        });
        
        // Handle delete button click
        const deleteBtn = itemDiv.querySelector('.history-item-delete');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteHistoryItem(item.id, itemDiv);
        });
        
        historyList.appendChild(itemDiv);
    });
    
    console.log('[HISTORY] Finished rendering, historyList children:', historyList.children.length);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleHistoryItemClick(query) {
    urlInput.value = query;
    closeHistoryDropdown();
    updateInputButtons();
    analyzeURL();
}

async function deleteHistoryItem(itemId, element) {
    try {
        const response = await fetch(`/api/history/${itemId}`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            // Remove from DOM and reload history
            currentHistory = currentHistory.filter(item => item.id !== itemId);
            renderHistoryItems();
        }
    } catch (error) {
        console.error('Failed to delete history item:', error);
    }
}

async function clearHistory() {
    try {
        const response = await fetch('/api/history', { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            currentHistory = [];
            renderHistoryItems();
        }
    } catch (error) {
        console.error('Failed to clear history:', error);
    }
}

async function analyzeURL() {
    const url = urlInput.value.trim();
    
    if (!url) {
        mariharAlert(t('alert_enter_url'), 'warning');
        return;
    }
    
    // Show loading and console
    loadingIndicator.classList.remove('hidden');
    analyzeBtn.disabled = true;
    showAnalysisConsole();
    addAnalysisLog('Démarrage de l\'analyse...', 'info');
    
    // Show cancel button and elapsed time
    const cancelBtn = document.getElementById('cancelAnalysisBtn');
    const elapsedBadge = document.getElementById('analysisElapsedTime');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    if (elapsedBadge) elapsedBadge.classList.remove('hidden');
    
    analysisIsRunning = true;
    analysisStartTime = Date.now();
    
    // Obtenir le mode de recherche sélectionné
    const searchModeSelect = document.getElementById('searchMode');
    const customSearchLimitInput = document.getElementById('customSearchLimit');
    let searchMode = searchModeSelect ? searchModeSelect.value : 'ytsearch20';
    
    // Si mode personnalisé, utiliser la valeur personnalisée
    if (searchMode === 'custom') {
        const customLimit = customSearchLimitInput ? parseInt(customSearchLimitInput.value) : 20;
        if (customLimit && customLimit > 0) {
            searchMode = `ytsearch${customLimit}`;
        } else {
            searchMode = 'ytsearch20'; // Fallback si valeur invalide
        }
    }
    
    // Start elapsed time timer
    if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
    elapsedTimerInterval = setInterval(updateElapsedTime, 1000);
    
    try {
        // Démarrer l'analyse
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, search_mode: searchMode })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            addAnalysisLog('Erreur: ' + result.error, 'error');
            mariharError(t('alert_error_prefix') + ': ' + result.error);
            analysisIsRunning = false;
            if (cancelBtn) cancelBtn.classList.add('hidden');
            // Keep elapsed time visible after error
            if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
            loadingIndicator.classList.add('hidden');
            analyzeBtn.disabled = false;
            return;
        }
        
        currentAnalysisTaskId = result.task_id;
        addAnalysisLog(`Tâche démarrée: ${result.task_id}`, 'info');
        
        // Démarrer le polling de progression
        startAnalysisProgressPolling();
        
    } catch (error) {
        addAnalysisLog('Erreur de connexion: ' + error.message, 'error');
        mariharError(t('alert_connection_error') + ': ' + error.message);
        analysisIsRunning = false;
        if (cancelBtn) cancelBtn.classList.add('hidden');
        if (elapsedBadge) elapsedBadge.classList.add('hidden');
        if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
        loadingIndicator.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}

function startAnalysisProgressPolling() {
    if (analysisProgressInterval) {
        clearInterval(analysisProgressInterval);
    }
    
    analysisProgressInterval = setInterval(async () => {
        if (!currentAnalysisTaskId) {
            clearInterval(analysisProgressInterval);
            return;
        }
        
        try {
            const response = await fetch(`/api/analyze/progress/${currentAnalysisTaskId}`);
            const data = await response.json();
            
            if (!data.success) {
                addAnalysisLog('Erreur: ' + data.error, 'error');
                clearInterval(analysisProgressInterval);
                loadingIndicator.classList.add('hidden');
                analyzeBtn.disabled = false;
                analysisIsRunning = false;
                const cancelBtn = document.getElementById('cancelAnalysisBtn');
                if (cancelBtn) cancelBtn.classList.add('hidden');
                // Keep elapsed time visible after error
                if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
                return;
            }
            
            // Afficher les nouveaux logs
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    let type = 'info';
                    if (log.includes('[ERROR]') || log.includes('error')) type = 'error';
                    else if (log.includes('[SUCCESS]') || log.includes('success')) type = 'success';
                    else if (log.includes('[WARNING]') || log.includes('warning')) type = 'warning';
                    addAnalysisLog(log, type);
                });
            }
            
            // Vérifier si l'analyse est terminée
            if (data.status === 'completed') {
                clearInterval(analysisProgressInterval);
                if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
                addAnalysisLog('Analyse terminée!', 'success');

                if (data.result) {
                    currentVideoData = data.result;
                    displayVideoInfo(data.result);
                    displayFormats(data.result);
                    showSections();
                }

                loadingIndicator.classList.add('hidden');
                analyzeBtn.disabled = false;
                analysisIsRunning = false;
                const cancelBtn = document.getElementById('cancelAnalysisBtn');
                if (cancelBtn) cancelBtn.classList.add('hidden');
                // Keep elapsed time visible after analysis completes

            } else if (data.status === 'error') {
                clearInterval(analysisProgressInterval);
                if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
                addAnalysisLog('Erreur: ' + (data.error_message || 'Erreur inconnue'), 'error');
                mariharError(t('alert_error_prefix') + ': ' + (data.error_message || 'Erreur inconnue'));
                loadingIndicator.classList.add('hidden');
                analyzeBtn.disabled = false;
                analysisIsRunning = false;
                const cancelBtn = document.getElementById('cancelAnalysisBtn');
                if (cancelBtn) cancelBtn.classList.add('hidden');
                // Keep elapsed time visible after error

            } else if (data.status === 'cancelled') {
                clearInterval(analysisProgressInterval);
                if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
                addAnalysisLog('Analyse annulée', 'warning');
                loadingIndicator.classList.add('hidden');
                analyzeBtn.disabled = false;
                analysisIsRunning = false;
                const cancelBtn = document.getElementById('cancelAnalysisBtn');
                if (cancelBtn) cancelBtn.classList.add('hidden');
                // Keep elapsed time visible after cancellation
            }
            
        } catch (error) {
            addAnalysisLog('Erreur de polling: ' + error.message, 'error');
        }
    }, 1000); // Polling toutes les secondes
}

function showSections() {
    videoInfo.classList.remove('hidden');
    formatsSection.classList.remove('hidden');
    advancedOptions.classList.remove('hidden');
    downloadSection.classList.remove('hidden');
}

// ==================== DISPLAY VIDEO INFO ====================

function displayVideoInfo(data) {
    document.getElementById('thumbnail').src = data.thumbnail || '';
    document.getElementById('videoTitle').textContent = data.title || 'Titre inconnu';
    document.getElementById('videoUploader').textContent = data.uploader || 'Chaîne inconnue';
    document.getElementById('videoDuration').textContent = data.duration || '00:00';
    document.getElementById('videoViews').textContent = `${formatNumber(data.view_count)} vues`;
    document.getElementById('videoDate').textContent = formatDate(data.upload_date);
    
    // Afficher la durée dans le badge
    const durationBadge = document.getElementById('durationBadge');
    if (durationBadge && data.duration) {
        durationBadge.textContent = data.duration;
    }
    
    // Afficher les informations de playlist si c'est une playlist
    const playlistInfo = document.getElementById('playlistInfo');
    if (data.is_playlist) {
        if (!playlistInfo) {
            // Créer la section playlist si elle n'existe pas
            const infoCard = document.querySelector('.info-card-modern');
            const playlistDiv = document.createElement('div');
            playlistDiv.id = 'playlistInfo';
            playlistDiv.className = 'playlist-info';
            playlistDiv.innerHTML = `
                <div class="playlist-badge">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                        <line x1="8" y1="21" x2="16" y2="21"></line>
                        <line x1="12" y1="17" x2="12" y2="21"></line>
                    </svg>
                    <span>Playlist détectée</span>
                </div>
                <div class="playlist-count">${data.playlist_count} vidéos</div>
                <div class="playlist-note">Sélectionnez les vidéos à télécharger ci-dessous</div>
            `;
            infoCard.appendChild(playlistDiv);
        } else {
            playlistInfo.style.display = 'block';
            playlistInfo.querySelector('.playlist-count').textContent = `${data.playlist_count} vidéos`;
            playlistInfo.querySelector('.playlist-note').textContent = 'Sélectionnez les vidéos à télécharger ci-dessous';
        }
        
        // Afficher la liste des vidéos de la playlist
        displayPlaylistVideos(data.playlist_entries);
        
        // Stocker les données pour les formats
        currentPlaylistData = data;
    } else if (playlistInfo) {
        playlistInfo.style.display = 'none';
        document.getElementById('playlistVideosSection').classList.add('hidden');
    }
}

// ==================== PLAYLIST VIDEOS ====================

function displayPlaylistVideos(videos) {
    const section = document.getElementById('playlistVideosSection');
    const list = document.getElementById('playlistVideosList');
    const count = document.getElementById('playlistVideosCount');
    
    if (!videos || videos.length === 0) {
        section.classList.add('hidden');
        return;
    }
    
    // Afficher la section
    section.classList.remove('hidden');
    count.textContent = `${videos.length} vidéos`;
    
    // Vider la liste
    list.innerHTML = '';
    
    // Ajouter chaque vidéo
    videos.forEach((video, index) => {
        const item = document.createElement('div');
        item.className = 'playlist-video-item';
        item.dataset.index = index;
        item.dataset.videoId = video.id;
        item.dataset.url = video.url;
        
        // Vérifier si un format est déjà sélectionné
        const selection = playlistSelections[video.id];
        const hasFormatSelected = selection && selection.formatId;
        
        item.innerHTML = `
            <input type="checkbox" class="playlist-video-checkbox" checked data-index="${index}">
            <img src="${video.thumbnail || ''}" alt="${video.title}" class="playlist-video-thumbnail" onerror="this.src='/static/Logo_marino.png'">
            <div class="playlist-video-info">
                <div class="playlist-video-title">${video.title || 'Sans titre'}</div>
                <div class="playlist-video-meta">
                    <span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        ${video.duration || '--:--'}
                    </span>
                    <span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        ${video.uploader || 'Chaîne inconnue'}
                    </span>
                </div>
            </div>
            <div class="playlist-video-actions">
                <button class="analyze-video-btn" onclick="event.stopPropagation(); showPlaylistVideoFormats('${video.id}', '${video.title.replace(/'/g, "\\'")}', '${video.thumbnail || ''}')" title="Choisir le format">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="9" y1="9" x2="15" y2="9"></line>
                        <line x1="9" y1="15" x2="15" y2="15"></line>
                    </svg>
                    ${hasFormatSelected ? 'Modifier' : 'Choisir le format'}
                </button>
                ${hasFormatSelected ? `<span class="format-selected-badge">Format: ${selection.formatId}</span>` : ''}
            </div>
        `;
        
        // Gestion du clic sur l'item
        item.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                const checkbox = item.querySelector('.playlist-video-checkbox');
                checkbox.checked = !checkbox.checked;
                updatePlaylistVideoSelection(item, checkbox.checked);
            }
        });
        
        // Gestion du changement de checkbox
        const checkbox = item.querySelector('.playlist-video-checkbox');
        checkbox.addEventListener('change', () => {
            updatePlaylistVideoSelection(item, checkbox.checked);
        });
        
        list.appendChild(item);
    });
    
    // Configurer les boutons
    document.getElementById('selectAllBtn').addEventListener('click', () => {
        document.querySelectorAll('.playlist-video-checkbox').forEach(cb => {
            cb.checked = true;
            updatePlaylistVideoSelection(cb.closest('.playlist-video-item'), true);
        });
    });
    
    document.getElementById('deselectAllBtn').addEventListener('click', () => {
        document.querySelectorAll('.playlist-video-checkbox').forEach(cb => {
            cb.checked = false;
            updatePlaylistVideoSelection(cb.closest('.playlist-video-item'), false);
        });
    });
    
    // Mettre à jour l'état du bouton de téléchargement après l'affichage des vidéos
    window.updateDownloadButtonState();
}

function updatePlaylistVideoSelection(item, isSelected) {
    if (isSelected) {
        item.classList.add('selected');
    } else {
        item.classList.remove('selected');
    }
    
    // Mettre à jour l'état du bouton de téléchargement
    window.updateDownloadButtonState();
}

function getSelectedPlaylistVideos() {
    const selected = [];
    document.querySelectorAll('.playlist-video-item').forEach(item => {
        const checkbox = item.querySelector('.playlist-video-checkbox');
        if (checkbox.checked) {
            selected.push({
                index: parseInt(item.dataset.index),
                videoId: item.dataset.videoId
            });
        }
    });
    return selected;
}

function formatNumber(num) {
    if (num === null || num === undefined || num === '') return '0';
    const n = parseInt(num);
    if (isNaN(n)) return '0';
    return n.toLocaleString('fr-FR');
}

function formatDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return 'Date inconnue';
    if (dateStr.length !== 8) return 'Date inconnue';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${day}/${month}/${year}`;
}

// ==================== DISPLAY FORMATS ====================

function displayFormats(data) {
    // Pour les playlists, afficher un message spécial
    if (data.is_playlist) {
        displayPlaylistFormats();
    } else {
        displayVideoFormats(data.video_formats);
        displayAudioFormats(data.audio_formats);
        displayCombinedFormats(data.combined_formats);
        displaySubtitles(data.subtitles, data.automatic_captions);
    }
}

function displayPlaylistFormats() {
    // Afficher un message dans les colonnes pour les playlists
    const videoTbody = document.getElementById('videoTableBody');
    const audioTbody = document.getElementById('audioTableBody');
    const combinedTbody = document.getElementById('combinedTableBody');
    
    const playlistMessage = `
        <tr>
            <td colspan="6" class="playlist-formats-message">
                <div class="playlist-formats-info">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                        <line x1="8" y1="21" x2="16" y2="21"></line>
                        <line x1="12" y1="17" x2="12" y2="21"></line>
                    </svg>
                    <span>Les formats seront détectés automatiquement pour chaque vidéo de la playlist lors du téléchargement.</span>
                </div>
            </td>
        </tr>
    `;
    
    videoTbody.innerHTML = playlistMessage;
    audioTbody.innerHTML = playlistMessage.replace('colspan="6"', 'colspan="5"');
    combinedTbody.innerHTML = playlistMessage.replace('colspan="6"', 'colspan="6"');
    
    document.getElementById('videoCount').textContent = '∞';
    document.getElementById('audioCount').textContent = '∞';
    
    // Afficher un message pour les sous-titres
    document.getElementById('originalSubs').innerHTML = `
        <div class="playlist-subs-message">
            Les sous-titres seront disponibles lors du téléchargement
        </div>
    `;
    document.getElementById('autoSubs').innerHTML = '';
}

function displayVideoFormats(formats) {
    const tbody = document.getElementById('videoTableBody');
    tbody.innerHTML = '';
    
    // Vérifier que formats est un tableau
    if (!Array.isArray(formats)) {
        document.getElementById('videoCount').textContent = '0';
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;">Aucun format vidéo disponible</td></tr>';
        return;
    }
    
    document.getElementById('videoCount').textContent = formats.length;
    
    formats.forEach(format => {
        const row = document.createElement('tr');
        row.dataset.formatId = format.format_id;
        row.innerHTML = `
            <td><input type="radio" name="videoFormat" value="${format.format_id}"></td>
            <td>${format.resolution || 'N/A'}</td>
            <td>${format.fps || 'N/A'}</td>
            <td>${format.vcodec || 'N/A'}</td>
            <td>${format.vbr ? format.vbr + 'k' : 'N/A'}</td>
            <td>${format.filesize || 'N/A'}</td>
        `;
        
        row.addEventListener('click', (e) => {
            if (e.target.type !== 'radio') {
                row.querySelector('input[type="radio"]').checked = true;
            }
            selectVideoFormat(format.format_id, row);
        });
        
        row.querySelector('input[type="radio"]').addEventListener('change', () => {
            selectVideoFormat(format.format_id, row);
        });
        
        tbody.appendChild(row);
    });
}

function displayAudioFormats(formats) {
    const tbody = document.getElementById('audioTableBody');
    tbody.innerHTML = '';
    
    // Vérifier que formats est un tableau
    if (!Array.isArray(formats)) {
        document.getElementById('audioCount').textContent = '0';
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;">Aucun format audio disponible</td></tr>';
        return;
    }
    
    document.getElementById('audioCount').textContent = formats.length;
    
    formats.forEach(format => {
        const row = document.createElement('tr');
        row.dataset.formatId = format.format_id;
        
        const langClass = format.default ? 'default' : (format.original ? 'original' : '');
        const langText = format.language ? format.language.toUpperCase() : '?';
        
        row.innerHTML = `
            <td><input type="radio" name="audioFormat" value="${format.format_id}"></td>
            <td><span class="lang-badge ${langClass}">${langText}</span></td>
            <td>${format.abr ? format.abr + 'k' : 'N/A'}</td>
            <td>${format.acodec || 'N/A'}</td>
            <td>${format.default ? 'Défaut' : (format.original ? 'Original' : '')}</td>
        `;
        
        row.addEventListener('click', (e) => {
            if (e.target.type !== 'radio') {
                row.querySelector('input[type="radio"]').checked = true;
            }
            selectAudioFormat(format.format_id, row);
        });
        
        row.querySelector('input[type="radio"]').addEventListener('change', () => {
            selectAudioFormat(format.format_id, row);
        });
        
        tbody.appendChild(row);
    });
}

function displayCombinedFormats(formats) {
    const tbody = document.getElementById('combinedTableBody');
    tbody.innerHTML = '';
    
    // Vérifier que formats est un tableau
    if (!Array.isArray(formats)) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align: center; color: var(--text-secondary);">Aucun format combiné disponible</td>';
        tbody.appendChild(row);
        return;
    }
    
    if (formats.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align: center; color: var(--text-secondary);">Aucun format combiné disponible</td>';
        tbody.appendChild(row);
        return;
    }
    
    formats.forEach(format => {
        const row = document.createElement('tr');
        row.dataset.formatId = format.format_id;
        
        const langText = format.language ? format.language.toUpperCase() : 'Default';
        const type = format.protocol === 'm3u8' ? 'HLS Stream' : 'Direct';
        
        row.innerHTML = `
            <td><input type="radio" name="combinedFormat" value="${format.format_id}"></td>
            <td>${format.format_id}</td>
            <td>${format.resolution || 'N/A'}</td>
            <td>${format.fps || 'N/A'}</td>
            <td>${langText}</td>
            <td>${type}</td>
        `;
        
        row.addEventListener('click', (e) => {
            if (e.target.type !== 'radio') {
                row.querySelector('input[type="radio"]').checked = true;
            }
            selectCombinedFormat(format.format_id, row);
        });
        
        row.querySelector('input[type="radio"]').addEventListener('change', () => {
            selectCombinedFormat(format.format_id, row);
        });
        
        tbody.appendChild(row);
    });
}

window.lastSubtitles = null;
window.lastAutoCaptions = null;

function displaySubtitles(subtitles, autoCaptions) {
    window.lastSubtitles = subtitles;
    window.lastAutoCaptions = autoCaptions;
    
    const originalContainer = document.getElementById('originalSubs');
    const autoContainer = document.getElementById('autoSubs');
    
    originalContainer.innerHTML = '';
    autoContainer.innerHTML = '';
    
    // Original subtitles
    if (subtitles && subtitles.length > 0) {
        subtitles.forEach(sub => {
            const item = createSubtitleItem(sub, 'original');
            originalContainer.appendChild(item);
        });
    } else {
        originalContainer.innerHTML = '<p class="empty">' + t('subs_no_original') + '</p>';
    }
    
    // Auto-generated captions
    if (autoCaptions && autoCaptions.length > 0) {
        autoCaptions.forEach(sub => {
            const item = createSubtitleItem(sub, 'auto');
            autoContainer.appendChild(item);
        });
    } else {
        autoContainer.innerHTML = '<p class="empty">' + t('subs_no_auto') + '</p>';
    }
}

window.displaySubtitles = displaySubtitles;

function createSubtitleItem(sub, type) {
    const div = document.createElement('div');
    div.className = 'subtitle-item-modern';
    div.dataset.lang = sub.language;
    div.dataset.type = type;
    
    const formatsStr = sub.formats ? sub.formats.join(', ') : '';
    const typeLabel = type === 'auto' ? '🤖' : '✓';
    
    div.innerHTML = `
        <input type="checkbox" value="${sub.language}" title="Sélectionner ${sub.language.toUpperCase()}">
        <span class="subtitle-lang">${sub.language.toUpperCase()}</span>
        <span class="subtitle-formats-list">${formatsStr}</span>
        <span class="subtitle-type" title="${type === 'auto' ? 'Auto-généré' : 'Original'}">${typeLabel}</span>
    `;
    
    div.addEventListener('click', (e) => {
        if (e.target.type !== 'checkbox') {
            const checkbox = div.querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;
        }
    });
    
    return div;
}

// ==================== SELECTION HANDLERS ====================

function selectVideoFormat(formatId, row) {
    selectedVideoFormat = formatId;
    selectedCombinedFormat = null;

    // Clear combined selection
    document.querySelectorAll('#combinedTableBody tr').forEach(r => r.classList.remove('selected'));
    document.querySelectorAll('input[name="combinedFormat"]').forEach(r => r.checked = false);

    // Update video table
    document.querySelectorAll('#videoTableBody tr').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');

    // Uncheck skip format selection when a format is selected
    const skipFormatCheckbox = document.getElementById('skipFormatSelection');
    if (skipFormatCheckbox) skipFormatCheckbox.checked = false;

    // Update download button state
    window.updateDownloadButtonState();
}

function selectAudioFormat(formatId, row) {
    selectedAudioFormat = formatId;
    selectedCombinedFormat = null;

    // Clear combined selection
    document.querySelectorAll('#combinedTableBody tr').forEach(r => r.classList.remove('selected'));
    document.querySelectorAll('input[name="combinedFormat"]').forEach(r => r.checked = false);

    // Update audio table
    document.querySelectorAll('#audioTableBody tr').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');

    // Uncheck skip format selection when a format is selected
    const skipFormatCheckbox = document.getElementById('skipFormatSelection');
    if (skipFormatCheckbox) skipFormatCheckbox.checked = false;

    // Update download button state
    window.updateDownloadButtonState();
}

function selectCombinedFormat(formatId, row) {
    selectedCombinedFormat = formatId;
    selectedVideoFormat = null;
    selectedAudioFormat = null;

    // Clear video/audio selections
    document.querySelectorAll('#videoTableBody tr, #audioTableBody tr').forEach(r => r.classList.remove('selected'));
    document.querySelectorAll('input[name="videoFormat"], input[name="audioFormat"]').forEach(r => r.checked = false);

    // Update combined table
    document.querySelectorAll('#combinedTableBody tr').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');

    // Uncheck skip format selection when a format is selected
    const skipFormatCheckbox = document.getElementById('skipFormatSelection');
    if (skipFormatCheckbox) skipFormatCheckbox.checked = false;

    // Update download button state
    window.updateDownloadButtonState();
}

// ==================== FORMAT SELECTION CLEARING ====================

function clearAllFormatSelections() {
    // Clear all format selections
    selectedVideoFormat = null;
    selectedAudioFormat = null;
    selectedCombinedFormat = null;

    // Clear visual selections
    document.querySelectorAll('#videoTableBody tr').forEach(r => r.classList.remove('selected'));
    document.querySelectorAll('#audioTableBody tr').forEach(r => r.classList.remove('selected'));
    document.querySelectorAll('#combinedTableBody tr').forEach(r => r.classList.remove('selected'));

    // Clear checkbox selections
    document.querySelectorAll('input[name="videoFormat"]').forEach(r => r.checked = false);
    document.querySelectorAll('input[name="audioFormat"]').forEach(r => r.checked = false);
    document.querySelectorAll('input[name="combinedFormat"]').forEach(r => r.checked = false);
}

// ==================== TABLE SORTING ====================

function setupTableSorting() {
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const sortKey = th.dataset.sort;
            const isAsc = !th.classList.contains('asc');
            
            // Remove sort classes from all headers
            table.querySelectorAll('th').forEach(header => {
                header.classList.remove('asc', 'desc');
            });
            
            th.classList.add(isAsc ? 'asc' : 'desc');
            
            // Sort rows
            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.sort((a, b) => {
                let aVal = getCellValue(a, th.cellIndex);
                let bVal = getCellValue(b, th.cellIndex);
                
                // Try numeric comparison
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAsc ? aNum - bNum : bNum - aNum;
                }
                
                // String comparison
                return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });
            
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

function getCellValue(row, index) {
    const cell = row.cells[index];
    if (!cell) return '';
    return cell.textContent.trim();
}

// ==================== DOWNLOAD ====================

async function startDownload() {
    if (!currentVideoData) {
        mariharAlert(t('alert_analyze_first'), 'warning');
        return;
    }

    // Vérifier si c'est une playlist
    if (currentVideoData.is_playlist) {
        await startPlaylistDownload();
        return;
    }

    // Validation pour l'incrustation des sous-titres
    const burnSubs = document.getElementById('burnSubs').checked;
    const writeAutoSubs = document.getElementById('writeAutoSubs').checked;
    const selectedSubtitles = getSelectedSubtitles();

    // Si incrustation demandée, vérifier qu'un seul sous-titre est sélectionné
    if (burnSubs && selectedSubtitles && selectedSubtitles.length > 1) {
        // Si plusieurs sous-titres sont sélectionnés pour l'incrustation
        // et que l'utilisateur veut aussi télécharger séparément, on peut permettre
        // mais on doit demander quel sous-titre utiliser pour l'incrustation
        if (writeAutoSubs) {
            // Mode mixte: télécharger plusieurs, mais en incruster un seul
            // Afficher une boîte de dialogue pour sélectionner le sous-titre à incruster
            showSubtitleSelectionDialog(selectedSubtitles, (selectedBurnSubtitle) => {
                // Utiliser le sous-titre sélectionné pour l'incrustation
                proceedWithDownload(selectedVideoFormat, selectedAudioFormat, selectedCombinedFormat, {
                    video_format: selectedVideoFormat,
                    audio_format: selectedAudioFormat,
                    write_auto_subs: true,
                    sub_langs: selectedSubtitles,  // Télécharger tous les sous-titres sélectionnés
                    burn_subs: true,
                    burn_subtitle_lang: selectedBurnSubtitle,  // Mais n'en incruster qu'un seul
                    output_dir: getOutputDirectory(),
                    embed_thumbnail: document.getElementById('embedThumbnail').checked,
                    extract_audio: document.getElementById('extractAudio').checked,
                    download_sections: getSectionTime(),
                    sub_style: document.getElementById('burnSubs').checked ? {
                        color: document.getElementById('subColor').value,
                        outline_color: document.getElementById('subOutlineColor').value,
                        font_size: parseInt(document.getElementById('subFontSize').value),
                        position: parseInt(document.getElementById('subPosition').value),
                        outline: parseInt(document.getElementById('subOutline').value),
                        font_style: parseInt(document.getElementById('subFontStyle').value)
                    } : null
                });
            });
            return;
        } else {
            mariharAlert('Pour l\'incrustation des sous-titres, vous devez sélectionner un seul sous-titre.', 'error');
            return;
        }
    }

    // Si incrustation demandée mais aucun sous-titre sélectionné
    if (burnSubs && (!selectedSubtitles || selectedSubtitles.length === 0)) {
        mariharAlert('Pour l\'incrustation des sous-titres, vous devez sélectionner au moins un sous-titre.', 'error');
        return;
    }

    // Cas normal: un seul sous-titre sélectionné ou pas d'incrustation
    // Continuer avec le téléchargement normal
    buildAndProceedDownload(selectedVideoFormat, selectedAudioFormat, selectedCombinedFormat, burnSubs, selectedSubtitles);
}

function buildAndProceedDownload(videoFormat, audioFormat, combinedFormat, burnSubs, selectedSubtitles) {
    // Check if format selection should be skipped
    const skipFormatSelection = document.getElementById('skipFormatSelection')?.checked || false;
    
    // If skip format selection is checked, clear all formats
    if (skipFormatSelection) {
        videoFormat = null;
        audioFormat = null;
        combinedFormat = null;
    }
    
    // Build options
    const writeAutoSubsChecked = document.getElementById('writeAutoSubs').checked;
    
    // Si incrustation demandée, forcer le téléchargement des sous-titres auto
    // même si l'utilisateur n'a pas coché "Télécharger les sous-titres séparément"
    const effectiveWriteAutoSubs = burnSubs ? true : writeAutoSubsChecked;
    
    const options = {
        video_format: videoFormat,
        audio_format: audioFormat,

        write_auto_subs: effectiveWriteAutoSubs,
        sub_langs: selectedSubtitles,
        burn_subs: burnSubs,
        output_dir: getOutputDirectory(),
        embed_thumbnail: document.getElementById('embedThumbnail').checked,
        extract_audio: document.getElementById('extractAudio').checked,
        download_sections: getSectionTime(),
        // Style des sous-titres
        sub_style: document.getElementById('burnSubs').checked ? {
            color: document.getElementById('subColor').value,
            outline_color: document.getElementById('subOutlineColor').value,
            font_size: parseInt(document.getElementById('subFontSize').value),
            position: parseInt(document.getElementById('subPosition').value),
            outline: parseInt(document.getElementById('subOutline').value),
            font_style: parseInt(document.getElementById('subFontStyle').value)
        } : null
    };
    
    // If combined format selected, use it instead
    if (combinedFormat) {
        options.video_format = combinedFormat;
        options.audio_format = null;
    }
    
    // Si incrustation demandée avec un seul sous-titre, définir burn_subtitle_lang
    if (burnSubs && selectedSubtitles && selectedSubtitles.length === 1) {
        options.burn_subtitle_lang = selectedSubtitles[0];
    }
    
    proceedWithDownload(videoFormat, audioFormat, combinedFormat, options);
}

function showSubtitleSelectionDialog(subtitles, callback) {
    // Create a custom dialog for subtitle selection
    const dialogOverlay = document.createElement('div');
    dialogOverlay.className = 'marihar-dialog-overlay';
    dialogOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:99999;';
    
    const dialogCard = document.createElement('div');
    dialogCard.className = 'marihar-dialog';
    dialogCard.style.cssText = 'background:#1a1a2e;border-radius:12px;padding:24px;max-width:500px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.3);';
    
    dialogCard.innerHTML = `
        <h3 style="color:#fff;margin:0 0 16px 0;font-size:20px;">${t('select_subtitle_to_embed')}</h3>
        <p style="color:#aaa;margin:0 0 20px 0;font-size:14px;">${t('multiple_subtitles_selected')}</p>
        <div id="subtitleSelectionList" style="margin-bottom:20px;"></div>
        <div style="display:flex;gap:12px;justify-content:flex-end;">
            <button id="cancelSubtitleSelection" style="background:#333;color:#fff;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;font-size:14px;">${t('cancel')}</button>
        </div>
    `;
    
    dialogOverlay.appendChild(dialogCard);
    document.body.appendChild(dialogOverlay);
    
    const listContainer = dialogCard.querySelector('#subtitleSelectionList');
    
    subtitles.forEach((sub, index) => {
        const item = document.createElement('div');
        item.style.cssText = 'background:#252540;padding:12px;margin-bottom:8px;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:all 0.2s;';
        item.innerHTML = `
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:24px;height:24px;border:2px solid #b8944f;border-radius:4px;display:flex;align-items:center;justify-content:center;">
                    <div class="radio-dot" style="width:12px;height:12px;background:#b8944f;border-radius:50%;display:none;"></div>
                </div>
                <span style="color:#fff;font-size:15px;font-weight:500;">${sub.toUpperCase()}</span>
            </div>
        `;
        
        item.addEventListener('click', () => {
            // Reset all items
            listContainer.querySelectorAll('div > div > div.radio-dot').forEach(dot => dot.style.display = 'none');
            listContainer.querySelectorAll('div').forEach(div => div.style.borderColor = 'transparent');
            
            // Select this item
            item.querySelector('.radio-dot').style.display = 'block';
            item.style.borderColor = '#b8944f';
            
            // Call callback with selected subtitle
            callback(sub);
            
            // Remove dialog
            document.body.removeChild(dialogOverlay);
        });
        
        listContainer.appendChild(item);
    });
    
    dialogCard.querySelector('#cancelSubtitleSelection').addEventListener('click', () => {
        document.body.removeChild(dialogOverlay);
    });
    
    // Close on backdrop click
    dialogOverlay.addEventListener('click', (e) => {
        if (e.target === dialogOverlay) {
            document.body.removeChild(dialogOverlay);
        }
    });
}

async function proceedWithDownload(videoFormat, audioFormat, combinedFormat, options) {
    // Show progress section
    progressSection.classList.remove('hidden');
    consoleSection.classList.remove('hidden');
    document.getElementById('downloadBtn').disabled = true;
    
    // Check if this is a search/title download (not a direct URL)
    const url = currentVideoData.webpage_url || urlInput.value;
    const isSearchDownload = !url.startsWith('http://') && !url.startsWith('https://');
    
    // Only show pause button for direct URL downloads (not playlists or searches)
    if (!isSearchDownload && !currentVideoData.is_playlist) {
        showPauseButton();
    } else {
        hidePauseResumeButtons();
    }
    
    // If combined format selected, use it instead
    if (combinedFormat) {
        options.video_format = combinedFormat;
        options.audio_format = null;
    }
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: currentVideoData.webpage_url || urlInput.value,
                options: options
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentTaskId = result.task_id;
            startProgressPolling();
        } else {
            mariharError(t('alert_error_prefix') + ': ' + result.error);
            document.getElementById('downloadBtn').disabled = false;
        }
    } catch (error) {
        mariharError(t('alert_connection_error') + ': ' + error.message);
        document.getElementById('downloadBtn').disabled = false;
    }
}

// Téléchargement d'une playlist avec les formats sélectionnés
async function startPlaylistDownload() {
    // Récupérer les vidéos sélectionnées
    const selectedVideos = [];
    document.querySelectorAll('.playlist-video-checkbox:checked').forEach(cb => {
        const item = cb.closest('.playlist-video-item');
        const videoId = item.dataset.videoId;
        const videoUrl = item.dataset.url;
        
        // Vérifier si un format est sélectionné
        const selection = playlistSelections[videoId];
        
        selectedVideos.push({
            id: videoId,
            url: videoUrl,
            format_id: selection ? selection.formatId : null,
            format_type: selection ? selection.formatType : null
        });
    });
    
    if (selectedVideos.length === 0) {
        mariharAlert(t('alert_select_video'), 'warning');
        return;
    }
    
    // Show progress section
    progressSection.classList.remove('hidden');
    consoleSection.classList.remove('hidden');
    document.getElementById('downloadBtn').disabled = true;
    // Don't show pause button for playlists (pause functionality breaks playlist downloads)
    hidePauseResumeButtons();
    
    try {
        const response = await fetch('/api/download/playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                playlist_title: currentVideoData.playlist_title,
                videos: selectedVideos,
                options: {
                    write_auto_subs: document.getElementById('writeAutoSubs').checked,
                    sub_langs: getSelectedSubtitles(),
                    output_dir: getOutputDirectory(),
                    embed_thumbnail: document.getElementById('embedThumbnail').checked,
                    extract_audio: document.getElementById('extractAudio').checked,
                    download_sections: getSectionTime()
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentTaskId = result.task_id;
            startProgressPolling();
        } else {
            mariharError(t('alert_error_prefix') + ': ' + result.error);
            document.getElementById('downloadBtn').disabled = false;
        }
    } catch (error) {
        mariharError(t('alert_connection_error') + ': ' + error.message);
        document.getElementById('downloadBtn').disabled = false;
    }
}

function getSelectedSubtitles() {
    const selected = [];
    document.querySelectorAll('.subtitle-item-modern input[type="checkbox"]:checked, .subtitle-item input[type="checkbox"]:checked').forEach(cb => {
        selected.push(cb.value);
    });
    return selected.length > 0 ? selected : null;
}

function getOutputDirectory() {
    const input = document.getElementById('outputDirInput');
    if (!input) return null;
    const value = input.value.trim();
    return value.length > 0 ? value : null;
}

function getSectionTime() {
    const start = document.getElementById('sectionStart').value;
    const end = document.getElementById('sectionEnd').value;
    
    if (start && end) {
        return `*${start}-${end}`;
    }
    return null;
}

// ==================== PROGRESS POLLING ====================

function startProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(pollProgress, 1000);
}

async function pollProgress() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/progress/${currentTaskId}`);
        const result = await response.json();
        
        if (result.success) {
            updateProgress(result.data);
            
            // Handle pause/resume button visibility
            // Don't show pause button for playlists or search downloads
            const isPlaylistDownload = currentVideoData && currentVideoData.is_playlist;
            const isSearchDownload = currentVideoData && (!currentVideoData.webpage_url || !currentVideoData.webpage_url.startsWith('http'));
            
            if (result.data.status === 'paused') {
                showResumeButton();
            } else if (result.data.status === 'downloading' && !isPlaylistDownload && !isSearchDownload) {
                showPauseButton();
            }
            
            // Stop polling if completed or error
            if (result.data.status === 'completed' || result.data.status === 'error' || result.data.status === 'cancelled') {
                clearInterval(progressInterval);
                document.getElementById('downloadBtn').disabled = false;
                hidePauseResumeButtons();
                
                if (result.data.status === 'completed') {
                    loadDownloadsList();
                    mariharAlert('alert_download_complete', 'success', 'alert_download_complete_title');
                }
            }
            
            // Afficher le statut d'incrustation
            if (result.data.status === 'burning_subs') {
                document.getElementById('progressPercent').textContent = 'Incrustation...';
            }
            
            // Afficher le statut de pause
            if (result.data.status === 'paused') {
                document.getElementById('progressPercent').textContent = 'En pause';
            }
        }
    } catch (error) {
        console.error('Error polling progress:', error);
    }
}

function parseLogLine(line) {
    const div = document.createElement('div');
    div.className = 'console-line';

    // Détecter le type de ligne
    if (line.includes('[ERROR]') || line.includes('ERROR') || line.includes('error') || line.includes('Traceback')) {
        div.classList.add('error');
        div.innerHTML = `<span class="log-prefix log-prefix-error">[ERROR]</span> ${escapeHtml(line.replace(/\[ERROR\]\s*/i, ''))}`;
    } else if (line.includes('[SUCCESS]') || line.includes('Completed') || line.includes('Finished') || line.includes('Téléchargée')) {
        div.classList.add('success');
        div.innerHTML = `<span class="log-prefix log-prefix-success">[OK]</span> ${escapeHtml(line.replace(/\[SUCCESS\]\s*/i, ''))}`;
    } else if (line.includes('[WARNING]') || line.includes('WARNING') || line.includes('warning') || line.includes('attention', 'i')) {
        div.classList.add('warning');
        div.innerHTML = `<span class="log-prefix log-prefix-warning">[WARN]</span> ${escapeHtml(line.replace(/\[WARNING\]\s*/i, ''))}`;
    } else if (line.includes('[INFO]') || line.includes('Dossier de sortie') || line.includes('Destination:')) {
        div.classList.add('info');
        div.innerHTML = `<span class="log-prefix log-prefix-info">[INFO]</span> ${escapeHtml(line.replace(/\[INFO\]\s*/i, ''))}`;
    } else if (line.includes('[download]') || line.match(/\d+\.?\d*%/)) {
        div.classList.add('download');
        // Extraire le pourcentage pour barre visuelle
        const percentMatch = line.match(/(\d+\.?\d*)%/);
        if (percentMatch) {
            const pct = parseFloat(percentMatch[1]);
            div.innerHTML = `<span class="log-prefix log-prefix-download">[DL]</span> ${escapeHtml(line)} <span class="yt-progress-bar"><span class="yt-progress-fill" style="width:${pct}%"></span></span>`;
        } else {
            div.innerHTML = `<span class="log-prefix log-prefix-download">[DL]</span> ${escapeHtml(line)}`;
        }
    } else if (line.includes('ETA') || line.includes('speed') || line.includes('MiB/s')) {
        div.classList.add('progress');
        div.textContent = line;
    } else {
        div.classList.add('tech');
        div.textContent = line;
    }

    return div;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateConsoleStatus(status) {
    const badge = document.getElementById('consoleStatusBadge');
    const dot = document.getElementById('consoleStatusDot');
    const text = document.getElementById('consoleStatusText');

    if (!badge || !text) return;

    badge.classList.remove('active', 'error');

    if (status === 'pending') {
        badge.classList.add('active');
        text.textContent = 'En attente...';
    } else if (status === 'analyzing') {
        badge.classList.add('active');
        text.textContent = 'Analyse...';
    } else if (status === 'downloading') {
        badge.classList.add('active');
        text.textContent = 'Téléchargement...';
    } else if (status === 'downloading_subs') {
        badge.classList.add('active');
        text.textContent = 'Téléchargement sous-titres...';
    } else if (status === 'burning_subs') {
        badge.classList.add('active');
        text.textContent = 'Incrustation...';
    } else if (status === 'finalizing' || status === 'merging') {
        badge.classList.add('active');
        text.textContent = 'Finalisation...';
    } else if (status === 'completed') {
        badge.classList.remove('active');
        text.textContent = 'Terminé';
    } else if (status === 'error') {
        badge.classList.add('error');
        text.textContent = 'Erreur';
    } else if (status === 'cancelled') {
        badge.classList.remove('active');
        text.textContent = 'Annulé';
    } else {
        text.textContent = 'Inactif';
    }
}

function updateProgress(data) {
    const progress = data.progress || {};
    const percent = progress.percent || 0;

    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressSize = document.getElementById('progressSize');
    const progressSpeed = document.getElementById('progressSpeed');
    const progressEta = document.getElementById('progressEta');

    if (progressBar) progressBar.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent.toFixed(1) + '%';

    // Update info
    if (progressSize) progressSize.textContent = progress.total_size ? `Taille: ${progress.total_size}` : '';
    if (progressSpeed) progressSpeed.textContent = progress.speed ? `Vitesse: ${progress.speed}` : '';
    if (progressEta) progressEta.textContent = progress.eta ? `ETA: ${progress.eta}` : '';

    // Update status indicator
    updateConsoleStatus(data.status);

    // Update console with colored lines
    if (data.logs && data.logs.length > 0) {
        const consoleOutput = document.getElementById('consoleOutput');
        if (consoleOutput) {
            consoleOutput.innerHTML = '';
            data.logs.forEach(line => {
                consoleOutput.appendChild(parseLogLine(line));
            });
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    }
}

async function cancelDownload() {
    if (!currentTaskId) return;
    
    // Show confirmation dialog before canceling
    const confirmed = confirm(t('confirm_cancel_message') + '\n\n' + t('confirm_cancel_yes') + ' / ' + t('confirm_cancel_no'));
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/cancel/${currentTaskId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            clearInterval(progressInterval);
            document.getElementById('downloadBtn').disabled = false;
            hidePauseResumeButtons();
            mariharAlert('alert_download_cancelled', 'info');
        }
    } catch (error) {
        mariharError(t('alert_cancel_error') + ': ' + error.message);
    }
}

async function pauseDownload() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/pause/${currentTaskId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResumeButton();
            mariharAlert('Download paused', 'info');
        }
    } catch (error) {
        mariharError('Error pausing download: ' + error.message);
    }
}

async function resumeDownload() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/resume/${currentTaskId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showPauseButton();
            mariharAlert('Download resumed', 'info');
        }
    } catch (error) {
        mariharError('Error resuming download: ' + error.message);
    }
}

function showPauseButton() {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    if (pauseBtn) pauseBtn.classList.remove('hidden');
    if (resumeBtn) resumeBtn.classList.add('hidden');
}

function showResumeButton() {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    if (pauseBtn) pauseBtn.classList.add('hidden');
    if (resumeBtn) resumeBtn.classList.remove('hidden');
}

function hidePauseResumeButtons() {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    if (pauseBtn) pauseBtn.classList.add('hidden');
    if (resumeBtn) resumeBtn.classList.add('hidden');
}

// ==================== DOWNLOADS LIST ====================

async function loadDownloadsList() {
    try {
        const response = await fetch('/api/downloads');
        const result = await response.json();

        if (result.success) {
            displayDownloadsList(result.files);
        }
    } catch (error) {
        console.error('Error loading downloads:', error);
    }
}

// Exporter la fonction loadDownloadsList globalement pour qu'elle puisse être appelée depuis localization.js
window.loadDownloadsList = loadDownloadsList;

function displayDownloadsList(files) {
    const container = document.getElementById('downloadsList');
    const countElement = document.getElementById('downloadsCount');
    
    // Mettre à jour le compteur
    if (countElement) {
        const countNumber = countElement.querySelector('.count-number');
        if (countNumber) {
            countNumber.textContent = files.length;
        }
    }
    
    if (files.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <p class="empty-text">${t('empty_text')}</p>
                <p class="empty-hint">${t('empty_hint')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    files.forEach(file => {
        const div = document.createElement('div');
        div.className = 'download-item-modern';
        
        const sizeFormatted = formatFileSize(file.size);
        const dateFormatted = new Date(file.created * 1000).toLocaleDateString('fr-FR');
        const timeFormatted = new Date(file.created * 1000).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
        const locationLabel = file.directory ? escapeHtml(file.directory) : 'Dossier par défaut';
        const downloadUrl = file.download_url || `/downloads/${encodeURIComponent(file.name)}`;
        
        // Détecter le type de fichier
        const isVideo = file.name.match(/\.(mp4|mkv|avi|mov|webm)$/i);
        const isAudio = file.name.match(/\.(mp3|m4a|wav|ogg|flac)$/i);
        const isSubtitle = file.name.match(/\.(srt|vtt|ass)$/i);
        const isJson = file.name.match(/\.json$/i);
        const fileType = isVideo ? 'Vidéo' : isAudio ? 'Audio' : isSubtitle ? 'Sous-titre' : isJson ? 'JSON' : 'Fichier';
        
        div.innerHTML = `
            <div class="download-file-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${isVideo ? '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>' : 
                      isAudio ? '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>' : 
                      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline>'}
                </svg>
            </div>
            <div class="download-info-modern">
                <div class="download-name-modern" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                <div class="download-meta-modern">
                    <span class="download-meta-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        ${sizeFormatted}
                    </span>
                    <span class="download-meta-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        ${dateFormatted} à ${timeFormatted}
                    </span>
                    <span class="download-meta-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        </svg>
                        ${fileType}
                    </span>
                    <span class="download-meta-item" title="${locationLabel}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10a2 2 0 0 0-2-2h-7l-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2z"></path>
                        </svg>
                        ${locationLabel}
                    </span>
                </div>
            </div>
            <div class="download-actions-modern">
                <a href="${downloadUrl}" class="btn-download-file-modern" download>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Télécharger
                </a>
            </div>
        `;
        
        container.appendChild(div);
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== NAVIGATION ====================

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page-content');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.dataset.page;
            
            // Mettre à jour les liens actifs
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Afficher la page cible
            pages.forEach(page => {
                page.classList.remove('active');
                if (page.id === targetPage + 'Page') {
                    page.classList.add('active');
                }
            });
            
            // Sauvegarder la page active
            localStorage.setItem('activePage', targetPage);
            
            // Scroll en haut de page
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });
    
    // Restaurer la page active au chargement
    const savedPage = localStorage.getItem('activePage') || 'home';
    const savedLink = document.querySelector(`.nav-link[data-page="${savedPage}"]`);
    if (savedLink && savedPage !== 'home') {
        savedLink.click();
    }
}

// ==================== COLUMN COLLAPSE/EXPAND ====================

function setupColumnCollapse() {
    // Gérer les clics sur les boutons de réduction des colonnes
    document.querySelectorAll('.collapse-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const column = btn.closest('.column-modern');
            toggleColumn(column);
        });
    });
    
    // Gérer les clics sur l'en-tête des colonnes (sauf sur les contrôles)
    document.querySelectorAll('.column-header-modern').forEach(header => {
        header.addEventListener('click', (e) => {
            // Ne pas réagir si on clique sur un bouton ou contrôle
            if (e.target.closest('.collapse-btn') || e.target.closest('.column-controls')) {
                return;
            }
            const column = header.closest('.column-modern');
            toggleColumn(column);
        });
    });
    
    // Gérer les clics sur les boutons de réduction des sections
    document.querySelectorAll('.collapse-btn-section').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const section = btn.closest('.collapsible-section');
            toggleSection(section);
        });
    });
    
    // Gérer les clics sur les en-têtes de sections (sauf sur les contrôles)
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', (e) => {
            // Ne pas réagir si on clique sur un bouton
            if (e.target.closest('.collapse-btn-section')) {
                return;
            }
            const section = header.closest('.collapsible-section');
            toggleSection(section);
        });
    });
}

function toggleColumn(column) {
    if (!column) return;
    
    column.classList.toggle('collapsed');
    
    // Sauvegarder l'état dans localStorage
    const columnId = column.id;
    const isCollapsed = column.classList.contains('collapsed');
    localStorage.setItem(`column_${columnId}_collapsed`, isCollapsed);
}

function toggleSection(section) {
    if (!section) return;
    
    section.classList.toggle('collapsed');
    
    // Sauvegarder l'état dans localStorage
    const sectionId = section.id || section.dataset.section;
    const isCollapsed = section.classList.contains('collapsed');
    localStorage.setItem(`section_${sectionId}_collapsed`, isCollapsed);
}

// Restaurer l'état des colonnes et sections au chargement
function restoreColumnStates() {
    // Restaurer les colonnes
    ['videoColumn', 'audioColumn', 'subtitleColumn'].forEach(columnId => {
        const column = document.getElementById(columnId);
        if (column) {
            const isCollapsed = localStorage.getItem(`column_${columnId}_collapsed`) === 'true';
            if (isCollapsed) {
                column.classList.add('collapsed');
            }
        }
    });
    
    // Restaurer les sections
    ['separatedSection', 'combinedSection', 'advanced', 'analysisConsole'].forEach(sectionId => {
        const section = document.getElementById(sectionId) ||
                        document.querySelector(`[data-section="${sectionId}"]`);
        if (section) {
            const isCollapsed = localStorage.getItem(`section_${sectionId}_collapsed`) === 'true';
            if (isCollapsed) {
                section.classList.add('collapsed');
            }
        }
    });
}

// Appeler la restauration après le chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(restoreColumnStates, 100);
    initAnalysisConsole();
});

// ==================== PLAYLIST VIDEO ANALYSIS ====================

// Variable globale pour stocker les sélections de format des vidéos de playlist
let playlistSelections = {};
let currentPlaylistVideoId = null;
let currentPlaylistVideoUrl = null;
let currentPlaylistVideoTaskId = null;
let currentPlaylistData = null;

// Analyse une vidéo individuelle de la playlist
async function analyzePlaylistVideo(videoId, videoUrl, videoTitle, videoThumbnail) {
    currentPlaylistVideoId = videoId;
    currentPlaylistVideoUrl = videoUrl;
    
    // Ouvrir la modale
    const modal = document.getElementById('playlistVideoModal');
    const loader = document.getElementById('playlistVideoModalLoader');
    const content = document.getElementById('playlistVideoModalContent');
    
    // Mettre à jour les informations de la vidéo
    document.getElementById('playlistVideoModalVideoTitle').textContent = videoTitle;
    document.getElementById('playlistVideoModalThumbnail').src = videoThumbnail || '/static/Logo_marino.png';
    
    // Afficher la modale
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    
    // Réinitialiser les onglets
    switchPlaylistFormatTab('combined');
    
    try {
        // Démarrer l'analyse
        const response = await fetch('/api/analyze/playlist-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: videoUrl,
                playlist_task_id: currentAnalysisTaskId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentPlaylistVideoTaskId = data.task_id;
            // Polling de la progression
            pollPlaylistVideoAnalysisProgress(data.task_id);
        } else {
            showNotification('Erreur lors du démarrage de l\'analyse', 'error');
            loader.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Erreur de connexion', 'error');
        loader.classList.add('hidden');
    }
}

// Polling de la progression de l'analyse
async function pollPlaylistVideoAnalysisProgress(taskId) {
    const loader = document.getElementById('playlistVideoModalLoader');
    const content = document.getElementById('playlistVideoModalContent');
    const consoleOutput = document.getElementById('playlistAnalysisConsoleOutput');
    
    // Réinitialiser la console
    if (consoleOutput) {
        consoleOutput.innerHTML = '';
    }
    
    const checkProgress = async () => {
        try {
            const response = await fetch(`/api/analyze/progress/${taskId}`);
            const data = await response.json();
            
            console.log('[DEBUG] Progress data:', data); // Debug
            
            // Afficher les logs dans la console
            if (data.logs && data.logs.length > 0 && consoleOutput) {
                console.log('[DEBUG] Logs received:', data.logs.length); // Debug
                data.logs.forEach(log => {
                    addLogToPlaylistConsole(log);
                });
                // Scroll vers le bas
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            } else {
                console.log('[DEBUG] No logs or console output not ready'); // Debug
            }
            
            if (data.status === 'completed') {
                // Afficher les formats
                displayPlaylistVideoFormats(data.result);
                loader.classList.add('hidden');
                content.classList.remove('hidden');
            } else if (data.status === 'error') {
                showNotification('Erreur lors de l\'analyse: ' + data.error_message, 'error');
                loader.classList.add('hidden');
            } else {
                // Continuer le polling
                setTimeout(checkProgress, 1000);
            }
        } catch (error) {
            console.error('Error:', error);
            setTimeout(checkProgress, 2000);
        }
    };
    
    checkProgress();
}

// Ajoute une ligne de log dans la console de la modale
function addLogToPlaylistConsole(log) {
    const consoleOutput = document.getElementById('playlistAnalysisConsoleOutput');
    if (!consoleOutput) return;
    
    const line = document.createElement('div');
    line.className = 'console-line';
    
    // Déterminer le type de log
    if (log.includes('[ERROR]')) {
        line.classList.add('error');
    } else if (log.includes('[SUCCESS]')) {
        line.classList.add('success');
    } else if (log.includes('[INFO]')) {
        line.classList.add('info');
    } else if (log.includes('[WARN]')) {
        line.classList.add('warn');
    } else if (log.includes('[TECH]')) {
        line.classList.add('tech');
    }
    
    // Ajouter un timestamp
    const now = new Date();
    const timestamp = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
    
    line.innerHTML = `<span class="console-timestamp">${timestamp}</span>${escapeHtml(log)}`;
    consoleOutput.appendChild(line);
    
    // Limiter le nombre de lignes (garder les 100 dernières)
    while (consoleOutput.children.length > 100) {
        consoleOutput.removeChild(consoleOutput.firstChild);
    }
}

// Échapper les caractères HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Affiche les formats d'une vidéo de playlist (déjà analysés)
function showPlaylistVideoFormats(videoId, title, thumbnail) {
    currentPlaylistVideoId = videoId;
    currentPlaylistVideoUrl = `https://www.youtube.com/watch?v=${videoId}`;
    
    console.log('[DEBUG] currentPlaylistData:', currentPlaylistData);
    console.log('[DEBUG] videoId recherché:', videoId);
    
    // Trouver les données de la vidéo dans les résultats de l'analyse
    const video = currentPlaylistData?.playlist_entries?.find(v => v.id === videoId);
    
    console.log('[DEBUG] Vidéo trouvée:', video);
    
    if (!video) {
        showNotification('Vidéo non trouvée dans la playlist', 'error');
        return;
    }
    
    console.log('[DEBUG] available_formats:', video.available_formats);
    
    // Ouvrir la modale
    const modal = document.getElementById('playlistVideoModal');
    const loader = document.getElementById('playlistVideoModalLoader');
    const content = document.getElementById('playlistVideoModalContent');
    const consoleOutput = document.getElementById('playlistAnalysisConsoleOutput');
    
    modal.classList.remove('hidden');
    loader.classList.add('hidden');
    content.classList.remove('hidden');
    
    // Mettre à jour les informations
    document.getElementById('playlistVideoModalTitle').textContent = title || 'Sans titre';
    document.getElementById('playlistVideoModalThumbnail').src = thumbnail || '/static/Logo_marino.png';
    
    // Afficher les formats disponibles dans la console
    if (consoleOutput) {
        consoleOutput.innerHTML = '';
        
        if (video.available_formats && video.available_formats.length > 0) {
            addLogToPlaylistConsole('[INFO] Formats disponibles pour cette vidéo:');
            addLogToPlaylistConsole('');
            addLogToPlaylistConsole('ID  EXT   RESOLUTION FPS CH │   FILESIZE  TBR PROTO │ VCODEC      VBR ACODEC      ABR ASR MORE INFO');
            addLogToPlaylistConsole('───────────────────────────────────────────────────────────────────────────────────────────────────────────');
            
            video.available_formats.forEach(formatLine => {
                addLogToPlaylistConsole(formatLine);
            });
            
            addLogToPlaylistConsole('');
            addLogToPlaylistConsole(`[INFO] ${video.available_formats.length} formats disponibles`);
        } else {
            addLogToPlaylistConsole('[WARN] Aucun format pré-analysé disponible');
            addLogToPlaylistConsole('[INFO] Veuillez d\'abord analyser la playlist complète');
        }
    }
    
    // Parser les formats pour les afficher dans les tableaux
    const parsedFormats = parseAvailableFormats(video.available_formats || []);
    displayPlaylistVideoFormats(parsedFormats);
}

// Parse les lignes de formats yt-dlp -F
function parseAvailableFormats(formatLines) {
    const videoFormats = [];
    const audioFormats = [];
    const combinedFormats = [];
    
    formatLines.forEach(line => {
        // Parser une ligne de format
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 2) {
            const formatId = parts[0];
            const ext = parts[1];
            
            // Détecter le type de format
            const isAudioOnly = line.includes('audio only');
            const isVideoOnly = line.includes('video only');
            
            const format = {
                format_id: formatId,
                ext: ext,
                resolution: isAudioOnly ? 'audio only' : (parts[2] || 'N/A'),
                filesize: extractFilesize(line),
                vcodec: extractCodec(line, 'vcodec'),
                acodec: extractCodec(line, 'acodec'),
                protocol: extractProtocol(line)
            };
            
            if (isAudioOnly) {
                audioFormats.push(format);
            } else if (isVideoOnly) {
                videoFormats.push(format);
            } else {
                combinedFormats.push(format);
            }
        }
    });
    
    const result = {
        video_formats: videoFormats,
        audio_formats: audioFormats,
        combined_formats: combinedFormats
    };
    
    return result;
}

// Extrait la taille du fichier d'une ligne de format
function extractFilesize(line) {
    const match = line.match(/(\d+\.?\d*\s*(KiB|MiB|GiB|k|M|G))/i);
    return match ? match[1] : 'N/A';
}

// Extrait le codec d'une ligne de format
function extractCodec(line, type) {
    if (type === 'vcodec') {
        const match = line.match(/(avc1\.\w+|vp9|av01\.\w+|h265|hevc)/i);
        return match ? match[1] : 'none';
    } else {
        const match = line.match(/(mp4a\.\w+|opus|aac|vorbis)/i);
        return match ? match[1] : 'none';
    }
}

// Extrait le protocole d'une ligne de format
function extractProtocol(line) {
    if (line.includes('m3u8')) return 'm3u8';
    if (line.includes('https')) return 'https';
    if (line.includes('http')) return 'http';
    return 'N/A';
}

// Affiche les formats dans la modale
function displayPlaylistVideoFormats(data) {
    // Mettre à jour les compteurs
    const combinedCount = document.getElementById('playlistCombinedCount');
    const videoCount = document.getElementById('playlistVideoCount');
    const audioCount = document.getElementById('playlistAudioCount');
    
    if (combinedCount) combinedCount.textContent = data.combined_formats?.length || 0;
    if (videoCount) videoCount.textContent = data.video_formats?.length || 0;
    if (audioCount) audioCount.textContent = data.audio_formats?.length || 0;
    
    // Remplir les tableaux
    fillPlaylistFormatTable('playlistCombinedTableBody', data.combined_formats || [], 'combined');
    fillPlaylistFormatTable('playlistVideoTableBody', data.video_formats || [], 'video');
    fillPlaylistFormatTable('playlistAudioTableBody', data.audio_formats || [], 'audio');
    
    // Pré-sélectionner les formats si déjà sélectionnés
    const selection = playlistSelections[currentPlaylistVideoId];
    if (selection) {
        if (selection.selectedIds && selection.selectedIds.length > 0) {
            selection.selectedIds.forEach(id => {
                const input = document.querySelector(`input[name="playlistFormat"][value="${id}"]`);
                if (input) {
                    input.checked = true;
                }
            });
        } else if (selection.formatId) {
            const input = document.querySelector(`input[name="playlistFormat"][value="${selection.formatId}"]`);
            if (input) {
                input.checked = true;
            }
        }
    }
}

// Remplit un tableau de formats
function fillPlaylistFormatTable(tbodyId, formats, type) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';
    
    if (formats.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="5" style="text-align: center; color: var(--text-secondary);">Aucun format disponible</td>`;
        tbody.appendChild(row);
        return;
    }
    
    formats.forEach(format => {
        const row = document.createElement('tr');
        
        let details = '';
        if (type === 'combined') {
            details = `
                <td>${format.resolution || 'N/A'}</td>
                <td>${format.vcodec || 'N/A'}</td>
                <td>${format.filesize || 'N/A'}</td>
            `;
        } else if (type === 'video') {
            details = `
                <td>${format.resolution || 'N/A'}</td>
                <td>${format.vcodec || 'N/A'}</td>
                <td>${format.vbr ? format.vbr + 'k' : 'N/A'}</td>
            `;
        } else if (type === 'audio') {
            details = `
                <td>${format.acodec || 'N/A'}</td>
                <td>${format.abr ? format.abr + 'k' : 'N/A'}</td>
                <td>${format.language || 'Default'}</td>
            `;
        }
        
        row.innerHTML = `
            <td><input type="${type === 'combined' ? 'radio' : 'checkbox'}" name="playlistFormat" value="${format.format_id}" data-type="${type}"></td>
            <td>${format.format_id}</td>
            ${details}
        `;
        
        // Gérer l'exclusivité entre Combiné et Vidéo/Audio
        row.querySelector('input').addEventListener('change', (e) => {
            if (e.target.checked) {
                if (type === 'combined') {
                    // Si on sélectionne un combiné, on décoche tout le reste
                    document.querySelectorAll('input[name="playlistFormat"]').forEach(input => {
                        if (input !== e.target) input.checked = false;
                    });
                } else {
                    // Si on sélectionne Vidéo ou Audio, on décoche les combinés
                    document.querySelectorAll('input[name="playlistFormat"][data-type="combined"]').forEach(input => {
                        input.checked = false;
                    });
                }
            }
        });
        
        // Rendre la ligne cliquable
        row.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                const input = row.querySelector('input');
                if (input.type === 'radio') {
                    input.checked = true;
                } else {
                    input.checked = !input.checked;
                }
                // Déclencher manuellement l'événement change
                input.dispatchEvent(new Event('change'));
            }
        });
        
        tbody.appendChild(row);
    });
}

// Change d'onglet dans la modale
function switchPlaylistFormatTab(tab) {
    // Mettre à jour les boutons
    document.querySelectorAll('.format-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });
    
    // Mettre à jour le contenu
    document.querySelectorAll('.format-tab-content').forEach(content => {
        content.classList.add('hidden');
        content.classList.remove('active');
    });
    
    const activeContent = document.getElementById(`playlist${tab.charAt(0).toUpperCase() + tab.slice(1)}Formats`);
    if (activeContent) {
        activeContent.classList.remove('hidden');
        activeContent.classList.add('active');
    }
}

// Ferme la modale
function closePlaylistVideoModal() {
    document.getElementById('playlistVideoModal').classList.add('hidden');
    currentPlaylistVideoId = null;
    currentPlaylistVideoUrl = null;
    currentPlaylistVideoTaskId = null;
}

// Confirme la sélection du format
function confirmPlaylistVideoFormat() {
    const selectedInputs = document.querySelectorAll('input[name="playlistFormat"]:checked');
    
    if (selectedInputs.length === 0) {
        showNotification('Veuillez sélectionner au moins un format', 'warning');
        return;
    }
    
    let formatId = '';
    let formatType = '';
    
    if (selectedInputs.length === 1) {
        formatId = selectedInputs[0].value;
        formatType = selectedInputs[0].dataset.type;
    } else {
        // Combiner plusieurs formats (ex: vidéo + audio)
        const ids = Array.from(selectedInputs).map(input => input.value);
        formatId = ids.join('+');
        formatType = 'custom';
    }
    
    // Stocker la sélection
    playlistSelections[currentPlaylistVideoId] = {
        selected: true,
        formatId: formatId,
        formatType: formatType,
        videoUrl: currentPlaylistVideoUrl,
        selectedIds: Array.from(selectedInputs).map(input => input.value) // Garder les IDs individuels pour la ré-affichage
    };
    
    // Mettre à jour l'UI de la liste
    updatePlaylistVideoItemUI(currentPlaylistVideoId, formatId);
    
    showNotification('Format sélectionné avec succès', 'success');
    closePlaylistVideoModal();
}

// Met à jour l'UI d'un item de la playlist
function updatePlaylistVideoItemUI(videoId, formatId) {
    const item = document.querySelector(`.playlist-video-item[data-video-id="${videoId}"]`);
    if (item) {
        const btn = item.querySelector('.analyze-video-btn');
        const existingBadge = item.querySelector('.format-selected-badge');
        
        if (btn) {
            btn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                Modifier
            `;
        }
        
        if (existingBadge) {
            existingBadge.textContent = `Format: ${formatId}`;
        } else {
            const badge = document.createElement('span');
            badge.className = 'format-selected-badge';
            badge.textContent = `Format: ${formatId}`;
            const actions = item.querySelector('.playlist-video-actions');
            if (actions) {
                actions.appendChild(badge);
            }
        }
    }
}

// ==================== NAVBAR PREMIUM ====================

// Effet de scroll sur la navbar
function setupNavbarScroll() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Ajouter la classe 'scrolled' après 50px
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

// Menu mobile
function setupMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (!mobileMenuBtn || !mobileMenu) return;
    
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenuBtn.classList.toggle('active');
        mobileMenu.classList.toggle('active');
    });
    
    // Fermer le menu quand on clique sur un lien
    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            // Si c'est le dropdown toggle, ne pas fermer
            if (link.classList.contains('mobile-dropdown-toggle')) {
                return;
            }
            
            e.preventDefault();
            const page = link.dataset.page;
            
            // Navigation vers la page
            if (page) {
                navigateToPage(page);
            }
            
            mobileMenuBtn.classList.remove('active');
            mobileMenu.classList.remove('active');
        });
    });
    
    // Fermer le menu quand on clique en dehors
    document.addEventListener('click', (e) => {
        if (!mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
            mobileMenuBtn.classList.remove('active');
            mobileMenu.classList.remove('active');
        }
    });
}

// Navigation entre les pages
function navigateToPage(pageName) {
    // Masquer toutes les pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    // Afficher la page demandée
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Mettre à jour les liens actifs (desktop)
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });
    
    // Mettre à jour les liens actifs (mobile)
    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });
}

// Activer les fonctionnalités de la navbar
document.addEventListener('DOMContentLoaded', () => {
    setupNavbarScroll();
    setupMobileMenu();
    setupDropdownMenus();
    setupYtdlpDropdown();
    
    // Navigation desktop
    document.querySelectorAll('.nav-link[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            // Si le lien a un dropdown, ne pas naviguer
            if (link.querySelector('.nav-dropdown')) {
                return;
            }

            e.preventDefault();
            const page = link.dataset.page;
            if (page) {
                navigateToPage(page);
            }
        });
    });
});

// Gestion des menus déroulants
function setupDropdownMenus() {
    const aboutWrapper = document.querySelector('.nav-dropdown-wrapper');
    const aboutLink = document.querySelector('.nav-dropdown-wrapper .nav-link');
    
    // Gérer les clics sur les items du dropdown
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const modal = item.dataset.modal;
            if (modal === 'privacy') {
                showPrivacyModal();
            } else if (modal === 'contact') {
                showContactModal();
            }
            
            // Fermer le dropdown après le clic
            const aboutDropdown = document.getElementById('aboutDropdown');
            if (aboutDropdown) {
                aboutDropdown.classList.remove('show');
            }
        });
    });
    
    // Gérer le clic sur le lien "À propos" principal
    const aboutDropdown = document.getElementById('aboutDropdown');
    if (aboutLink && aboutWrapper && aboutDropdown) {
        aboutLink.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Vérifier si on est sur la page À propos
            const aboutPage = document.getElementById('aboutPage');
            const isOnAboutPage = aboutPage && aboutPage.classList.contains('active');
            
            if (!isOnAboutPage) {
                // Premier clic : naviguer vers la page À propos
                aboutDropdown.classList.remove('show');
                navigateToPage('about');
            } else {
                // Deuxième clic : ouvrir/fermer le dropdown
                // Positionner le dropdown aligné à droite avec l'icône
                const rect = aboutLink.getBoundingClientRect();
                
                // Mesurer la largeur réelle du dropdown
                aboutDropdown.style.display = 'block';
                const dropdownWidth = aboutDropdown.offsetWidth;
                
                // Aligner le coin droit du dropdown avec le coin droit de l'icône
                aboutDropdown.style.left = (rect.right - dropdownWidth) + 'px';
                aboutDropdown.style.top = (rect.bottom + 10) + 'px';
                aboutDropdown.classList.toggle('show');
            }
        });
    }
    
    // Fermer le dropdown quand on clique ailleurs
    document.addEventListener('click', (e) => {
        const aboutDropdown = document.getElementById('aboutDropdown');
        if (aboutDropdown && !aboutDropdown.contains(e.target) && !aboutWrapper.contains(e.target)) {
            aboutDropdown.classList.remove('show');
        }
    });
}

// Modale Confidentialité
function showPrivacyModal() {
    // Supprimer l'ancienne modale aboutModal si elle existe encore
    const oldModal = document.getElementById('aboutModal');
    if (oldModal) {
        oldModal.remove();
    }
    
    let modal = document.getElementById('privacyModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'privacyModal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content privacy-modal">
                <button class="modal-close" onclick="closeModal('privacyModal')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="modal-header">
                    <h2 data-i18n="modal_privacy_title">${t('modal_privacy_title')}</h2>
                </div>
                <div class="modal-body">
                    <div class="privacy-content">
                        <div class="privacy-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                <path d="m9 12 2 2 4-4"></path>
                            </svg>
                        </div>
                        
                        <div class="privacy-section">
                            <h4 data-i18n="modal_privacy_data_protection">${t('modal_privacy_data_protection')}</h4>
                            <p data-i18n="modal_privacy_data_desc">${t('modal_privacy_data_desc')}</p>
                        </div>
                        
                        <div class="privacy-section">
                            <h4 data-i18n="modal_privacy_local_data">${t('modal_privacy_local_data')}</h4>
                            <ul>
                                <li data-i18n="modal_privacy_local_1">${t('modal_privacy_local_1')}</li>
                                <li data-i18n="modal_privacy_local_2">${t('modal_privacy_local_2')}</li>
                                <li data-i18n="modal_privacy_local_3">${t('modal_privacy_local_3')}</li>
                                <li data-i18n="modal_privacy_local_4">${t('modal_privacy_local_4')}</li>
                            </ul>
                        </div>
                        
                        <div class="privacy-section">
                            <h4 data-i18n="modal_privacy_security">${t('modal_privacy_security')}</h4>
                            <div class="security-features">
                                <div class="security-item">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                    </svg>
                                    <span data-i18n="modal_privacy_security_1">${t('modal_privacy_security_1')}</span>
                                </div>
                                <div class="security-item">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                                    </svg>
                                    <span data-i18n="modal_privacy_security_2">${t('modal_privacy_security_2')}</span>
                                </div>
                                <div class="security-item">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path>
                                    </svg>
                                    <span data-i18n="modal_privacy_security_3">${t('modal_privacy_security_3')}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="privacy-section">
                            <h4 data-i18n="modal_privacy_cookies">${t('modal_privacy_cookies')}</h4>
                            <p data-i18n="modal_privacy_cookies_desc">${t('modal_privacy_cookies_desc')}</p>
                        </div>
                        
                        <div class="privacy-warning">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                            <p><strong data-i18n="modal_privacy_warning">${t('modal_privacy_warning')}</strong> <span data-i18n="modal_privacy_warning_desc">${t('modal_privacy_warning_desc')}</span></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        applyTranslations();
    }
    
    modal.classList.add('active');
}

// Modale À propos
function showAboutModal() {
    // TOUJOURS supprimer l'ancienne modale pour forcer la recréation
    const existingModal = document.getElementById('aboutModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Créer une nouvelle modale
    const modal = document.createElement('div');
    modal.id = 'aboutModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
            <div class="modal-content about-modal">
                <button class="modal-close" onclick="closeModal('aboutModal')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="modal-header">
                    <h2>Qu'est-ce que MARIHAR ?</h2>
                    <p class="modal-subtitle">Votre outil de téléchargement vidéo moderne et puissant</p>
                </div>
                <div class="modal-body">
                    <div class="about-content">
                        <h3>MARIHAR - Téléchargeur Vidéo Premium</h3>
                        <p class="about-version">Version 1.0.0</p>
                        
                        <div class="about-section">
                            <h4>Description</h4>
                            <p>MARIHAR est une interface web moderne et puissante pour yt-dlp, conçue pour simplifier le téléchargement de vidéos depuis de nombreuses plateformes avec des fonctionnalités avancées.</p>
                        </div>
                        
                        <div class="about-section">
                            <h4>Fonctionnalités</h4>
                            <ul>
                                <li>✓ Téléchargement vidéo jusqu'en 4K</li>
                                <li>✓ Pistes audio multilingues</li>
                                <li>✓ Sous-titres dans toutes les langues</li>
                                <li>✓ Support des playlists</li>
                                <li>✓ Interface moderne et intuitive</li>
                            </ul>
                        </div>
                        
                        <div class="about-section">
                            <h4>Technologies</h4>
                            <div class="tech-stack">
                                <span class="tech-badge">Python</span>
                                <span class="tech-badge">Flask</span>
                                <span class="tech-badge">yt-dlp</span>
                                <span class="tech-badge">FFmpeg</span>
                                <span class="tech-badge">JavaScript</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    document.body.appendChild(modal);
    
    modal.classList.add('active');
}

// Modale Contact
function showContactModal() {
    let modal = document.getElementById('contactModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'contactModal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content contact-modal">
                <button class="modal-close" onclick="closeModal('contactModal')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="modal-header">
                    <h2 data-i18n="modal_contact_title">${t('modal_contact_title')}</h2>
                </div>
                <div class="modal-body">
                    <div class="contact-content">
                        <div class="contact-developer">
                            <div class="developer-avatar">
                                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="12" cy="7" r="4"></circle>
                                </svg>
                            </div>
                            <h3 data-i18n="modal_contact_dev">${t('modal_contact_dev')}</h3>
                            <p class="developer-role" data-i18n="modal_contact_role">${t('modal_contact_role')}</p>
                        </div>
                        
                        <div class="contact-info">
                            <div class="contact-item">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                                    <polyline points="22,6 12,13 2,6"></polyline>
                                </svg>
                                <div>
                                    <span class="contact-label" data-i18n="modal_contact_email">${t('modal_contact_email')}</span>
                                    <a href="mailto:rakotonjanaharymarino@gmail.com" class="contact-value">rakotonjanaharymarino@gmail.com</a>
                                </div>
                            </div>
                            
                            <div class="contact-item">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                    <circle cx="12" cy="10" r="3"></circle>
                                </svg>
                                <div>
                                    <span class="contact-label" data-i18n="modal_contact_location">${t('modal_contact_location')}</span>
                                    <span class="contact-value">Madagascar</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="contact-message">
                            <p data-i18n="modal_contact_message">${t('modal_contact_message')}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        applyTranslations();
    }
    
    modal.classList.add('active');
}

// Fermer une modale
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Fermer la modale en cliquant à l'extérieur
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// ==================== GUIDE STEPPER ====================

let currentGuideStep = 0;
const totalGuideSteps = 5;

function initGuideStepper() {
    const prevBtn = document.getElementById('stepperPrevBtn');
    const nextBtn = document.getElementById('stepperNextBtn');
    const counter = document.getElementById('stepperCounter');
    const dots = document.querySelectorAll('.stepper-dot');
    
    if (!prevBtn || !nextBtn) return;
    
    // Bouton Précédent
    prevBtn.addEventListener('click', () => {
        if (currentGuideStep > 0) {
            currentGuideStep--;
            updateGuideStepper();
        }
    });
    
    // Bouton Suivant
    nextBtn.addEventListener('click', () => {
        if (currentGuideStep < totalGuideSteps - 1) {
            currentGuideStep++;
            updateGuideStepper();
        }
    });
    
    // Clic sur les dots
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            currentGuideStep = index;
            updateGuideStepper();
        });
    });
    
    // Navigation clavier
    document.addEventListener('keydown', (e) => {
        const guidePage = document.getElementById('guidePage');
        if (guidePage && guidePage.classList.contains('active')) {
            if (e.key === 'ArrowLeft' && currentGuideStep > 0) {
                currentGuideStep--;
                updateGuideStepper();
            } else if (e.key === 'ArrowRight' && currentGuideStep < totalGuideSteps - 1) {
                currentGuideStep++;
                updateGuideStepper();
            }
        }
    });
}

function updateGuideStepper() {
    const slider = document.getElementById('guideStepsSlider');
    const prevBtn = document.getElementById('stepperPrevBtn');
    const nextBtn = document.getElementById('stepperNextBtn');
    const counter = document.getElementById('stepperCounter');
    const progressBar = document.getElementById('stepperProgressBar');
    const dots = document.querySelectorAll('.stepper-dot');
    const steps = document.querySelectorAll('.guide-step');
    
    if (!slider) return;
    
    // Animation de transition
    slider.style.transform = `translateX(-${currentGuideStep * 100}%)`;
    
    // Mise à jour des classes actives
    steps.forEach((step, index) => {
        step.classList.toggle('active', index === currentGuideStep);
    });
    
    // Mise à jour des dots
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentGuideStep);
    });
    
    // Mise à jour de la barre de progression
    const progress = ((currentGuideStep + 1) / totalGuideSteps) * 100;
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    // Mise à jour du compteur
    if (counter) {
        counter.textContent = t('step_counter', {n: currentGuideStep + 1, total: totalGuideSteps});
    }
    
    // Activation/désactivation des boutons
    if (prevBtn) {
        prevBtn.disabled = currentGuideStep === 0;
    }
    
    if (nextBtn) {
        if (currentGuideStep === totalGuideSteps - 1) {
            nextBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>${t('btn_finish')}</span>
            `;
            nextBtn.classList.add('stepper-btn-finish');
        } else {
            nextBtn.innerHTML = `
                <span>${t('btn_next')}</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            `;
            nextBtn.classList.remove('stepper-btn-finish');
        }
    }
}

// Exporter la fonction updateGuideStepper globalement pour qu'elle puisse être appelée depuis localization.js
window.updateGuideStepper = updateGuideStepper;

// Initialiser le stepper au chargement
document.addEventListener('DOMContentLoaded', () => {
    initGuideStepper();
    
    // Gestion du dropdown mobile
    const mobileDropdownToggle = document.querySelector('.mobile-dropdown-toggle');
    const mobileDropdownContent = document.querySelector('.mobile-dropdown-content');
    const mobileDropdownArrow = document.querySelector('.mobile-dropdown-arrow');
    
    if (mobileDropdownToggle && mobileDropdownContent) {
        mobileDropdownToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Vérifier si on est sur la page À propos
            const aboutPage = document.getElementById('aboutPage');
            const isOnAboutPage = aboutPage && aboutPage.classList.contains('active');
            
            if (!isOnAboutPage) {
                // Premier clic : naviguer vers la page À propos
                mobileDropdownContent.classList.remove('active');
                if (mobileDropdownArrow) {
                    mobileDropdownArrow.classList.remove('active');
                }
                navigateToPage('about');
                // Fermer le menu mobile
                mobileMenuBtn.classList.remove('active');
                mobileMenu.classList.remove('active');
            } else {
                // Deuxième clic : ouvrir/fermer le dropdown
                mobileDropdownContent.classList.toggle('active');
                if (mobileDropdownArrow) {
                    mobileDropdownArrow.classList.toggle('active');
                }
            }
        });
        
        // Gestion des items du dropdown mobile
        document.querySelectorAll('.mobile-dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const modal = item.dataset.modal;
                if (modal === 'privacy') {
                    showPrivacyModal();
                } else if (modal === 'contact') {
                    showContactModal();
                }
                // Fermer le dropdown après le clic
                mobileDropdownContent.classList.remove('active');
                if (mobileDropdownArrow) {
                    mobileDropdownArrow.classList.remove('active');
                }
            });
        });
    }
});
