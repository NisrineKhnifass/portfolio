"use strict";

(function applySavedTheme() {
  const THEME_STORAGE_KEY = "theme";
  const SUPPORTED_THEMES = ["light", "dark"];

  function readSavedTheme() {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY);
    } catch {
      return null;
    }
  }

  const savedTheme = readSavedTheme();

  if (SUPPORTED_THEMES.includes(savedTheme)) {
    document.documentElement.setAttribute("data-theme", savedTheme);
  }

  document.documentElement.classList.add("js");
})();
