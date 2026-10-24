// Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
/**
 * MARIHAR - Système de traduction robuste
 * Charge les dictionnaires JSON et applique les traductions via data-i18n
 * Support: Français (fr), Anglais (en), Italien (it), Malagasy (mg)
 */

// Stockage global des traductions
window.translations = {};
window.currentLang = "fr";

function normalizeLang(lang) {
  if (lang.includes("en")) return "en";
  if (lang.includes("fr")) return "fr";
  if (lang.includes("it")) return "it";
  if (lang.includes("mg")) return "mg";
  return "fr";
}

function saveLanguagePref(langSelected) {
  localStorage.setItem("mariharLanguage", langSelected);
}

function loadLanguagePref() {
  if (localStorage.getItem("mariharLanguage")) {
    var langSaved = localStorage.getItem("mariharLanguage");
    changeLanguage(langSaved);
  } else {
    checkBrowserLanguage();
  }
}

function checkBrowserLanguage() {
  var lang = navigator.language;
  changeLanguage(lang);
}

function t(key, placeholders) {
  var text = key;
  if (window.translations && window.translations[key]) {
    text = window.translations[key];
  } else {
    // Fallback: if translations not loaded yet, try to load them
    if (!window.translations || Object.keys(window.translations).length === 0) {
      console.warn('Translations not loaded yet, using key:', key);
    }
  }
  if (placeholders) {
    for (var p in placeholders) {
      if (placeholders.hasOwnProperty(p)) {
        text = text.replace(
          new RegExp("\\{" + p + "\\}", "g"),
          placeholders[p],
        );
      }
    }
  }
  return text;
}

function applyTranslations() {
  if (!window.translations) return;

  // Traduire les éléments avec data-i18n (texte simple)
  var elements = document.querySelectorAll("[data-i18n]");
  for (var i = 0; i < elements.length; i++) {
    var el = elements[i];
    var key = el.getAttribute("data-i18n");
    if (window.translations[key]) {
      el.textContent = window.translations[key];
    }
  }

  // Traduire les attributs title
  var titleElements = document.querySelectorAll("[data-i18n-title]");
  for (var i = 0; i < titleElements.length; i++) {
    var el = titleElements[i];
    var key = el.getAttribute("data-i18n-title");
    if (window.translations[key]) {
      el.setAttribute("title", window.translations[key]);
    }
  }

  // Traduire les attributs placeholder
  var placeholderElements = document.querySelectorAll(
    "[data-i18n-placeholder]",
  );
  for (var i = 0; i < placeholderElements.length; i++) {
    var el = placeholderElements[i];
    var key = el.getAttribute("data-i18n-placeholder");
    if (window.translations[key]) {
      el.setAttribute("placeholder", window.translations[key]);
    }
  }

  // Traduire le contenu HTML (pour les textes avec balises)
  var htmlElements = document.querySelectorAll("[data-i18n-html]");
  for (var i = 0; i < htmlElements.length; i++) {
    var el = htmlElements[i];
    var key = el.getAttribute("data-i18n-html");
    if (window.translations[key]) {
      el.innerHTML = window.translations[key];
    }
  }

  // Traduire les labels d'optgroup
  var labelElements = document.querySelectorAll("[data-i18n-label]");
  for (var i = 0; i < labelElements.length; i++) {
    var el = labelElements[i];
    var key = el.getAttribute("data-i18n-label");
    if (window.translations[key]) {
      el.setAttribute("label", window.translations[key]);
    }
  }
}

function changeLanguage(langSelected) {
  var lang = normalizeLang(langSelected);
  window.currentLang = lang;

  // Mettre à jour l'attribut lang du document
  document.documentElement.lang = lang;

  // Sauvegarder la préférence
  saveLanguagePref(lang);

  // Mettre à jour les indicateurs visuels de langue active
  updateLanguageIndicators(lang);

  // Charger le fichier JSON puis appliquer les traductions
  var jsonPath = "static/translations/" + lang + ".json";
  fetch(jsonPath)
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Erreur HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      window.translations = data;
      applyTranslations();
      // Notifier le backend Python des nouveaux textes de fermeture
      // afin que la fenêtre native de confirmation utilise la bonne langue.
      _syncQuitTextsToPython(data);
      // Conserver aussi la compatibilité avec le système CSS
      applyCSSLanguage(lang);
      // Mettre à jour les boutons de navigation du guide
      if (typeof updateGuideStepper === 'function') {
        updateGuideStepper();
      }
      // Mettre à jour la liste des fichiers téléchargés
      if (typeof loadDownloadsList === 'function') {
        loadDownloadsList();
      }
      // Re-display subtitles with the new translated messages
      if (typeof window.displaySubtitles === 'function' && (window.lastSubtitles !== null || window.lastAutoCaptions !== null)) {
        window.displaySubtitles(window.lastSubtitles, window.lastAutoCaptions);
      }
    })
    .catch(function (error) {
      console.warn("Impossible de charger les traductions pour", lang, error);
      // En cas d'erreur, on applique quand même le système CSS
      applyCSSLanguage(lang);
    });
}

/**
 * Envoie les textes de la fenêtre de fermeture au pont Python (pywebview js_api)
 * afin que la boîte de dialogue native affiche toujours la langue courante.
 * Pywebview injecte window.pywebview de façon asynchrone : on réessaie avec
 * un backoff exponentiel (max 10 tentatives) si l'API n'est pas encore prête.
 */
function _syncQuitTextsToPython(translations, _attempt) {
  _attempt = _attempt || 0;
  try {
    if (
      window.pywebview &&
      window.pywebview.api &&
      window.pywebview.api.update_quit_texts
    ) {
      window.pywebview.api.update_quit_texts(
        translations.quit_title || "",
        translations.quit_message || "",
        translations.btn_quit || "",
        translations.btn_cancel_quit || translations.dialog_cancel || "",
      );
      return; // Succès
    }
    // Pywebview pas encore prêt : réessayer (max 10 tentatives, délai croissant)
    if (_attempt < 10) {
      setTimeout(
        function () {
          _syncQuitTextsToPython(translations, _attempt + 1);
        },
        150 * (_attempt + 1),
      );
    }
  } catch (e) {
    // Silencieux : fonctionnement normal hors desktop (navigateur web classique)
  }
}

function applyCSSLanguage(lang) {
  // Cacher tous les éléments traduisibles (système CSS ancien)
  var allLangElements = document.getElementsByClassName("lang");
  for (var i = 0; i < allLangElements.length; i++) {
    allLangElements[i].style.display = "none";
  }

  // Afficher les éléments de la langue sélectionnée
  var langElements = document.getElementsByClassName(lang);
  for (var i = 0; i < langElements.length; i++) {
    var el = langElements[i];
    // Pour les éléments inline (span dans des boutons par exemple),
    // on utilise inline-block si le parent est en flex/inline,
    // sinon block pour les éléments de type block
    var parentDisplay = window.getComputedStyle(el.parentElement).display;
    if (
      parentDisplay.indexOf("flex") !== -1 ||
      parentDisplay.indexOf("inline") !== -1
    ) {
      el.style.display = "inline-block";
    } else {
      el.style.display = "block";
    }
  }
}

function setLanguage(lang) {
  changeLanguage(lang);
}

function updateLanguageIndicators(currentLang) {
  var langOptions = document.querySelectorAll(".lang-option");
  langOptions.forEach(function (option) {
    option.classList.remove("active");
    if (option.getAttribute("data-lang") === currentLang) {
      option.classList.add("active");
    }
  });
}

function initTranslations() {
  loadLanguagePref();
}

// Exporter les fonctions globalement
window.changeLanguage = changeLanguage;
window.setLanguage = setLanguage;
window.saveLanguagePref = saveLanguagePref;
window.loadLanguagePref = loadLanguagePref;
window.updateLanguageIndicators = updateLanguageIndicators;
window.initTranslations = initTranslations;
window.applyTranslations = applyTranslations;
window.t = t;

// Initialiser au chargement du DOM
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTranslations);
} else {
  initTranslations();
}
