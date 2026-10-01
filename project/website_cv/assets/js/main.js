"use strict";

const THEME_STORAGE_KEY = "theme";
const COPY_FEEDBACK_DURATION_MS = 2000;
const HEADER_SCROLL_THRESHOLD_PX = 8;
const REVEAL_VISIBILITY_THRESHOLD = 0.15;
const CONTACT_EMAIL = "nisrine.khnifass@hotmail.com";

const MESSAGES = {
  fr: {
    enableDarkTheme: "Activer le thème sombre",
    enableLightTheme: "Activer le thème clair",
    openMenu: "Ouvrir le menu",
    closeMenu: "Fermer le menu",
    emailCopied: "Adresse copiée",
    copyFailed: "Copie impossible, sélectionnez l'adresse à la main",
    formSending: "Envoi en cours…",
    formSent: "Message envoyé. Je vous réponds sous 48 heures.",
    formFailed: `Le message n'est pas parti. Écrivez-moi directement à ${CONTACT_EMAIL}.`,
  },
  en: {
    enableDarkTheme: "Switch to dark theme",
    enableLightTheme: "Switch to light theme",
    openMenu: "Open menu",
    closeMenu: "Close menu",
    emailCopied: "Email address copied",
    copyFailed: "Copy failed, please select the address manually",
    formSending: "Sending…",
    formSent: "Message sent. I will reply within 48 hours.",
    formFailed: `The message could not be sent. Please email me directly at ${CONTACT_EMAIL}.`,
  },
};

const messages = MESSAGES[document.documentElement.lang] ?? MESSAGES.fr;

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    return true;
  } catch {
    return false;
  }
}

function initThemeToggle() {
  const toggleButton = document.querySelector("[data-theme-toggle]");
  if (!toggleButton) return;

  const root = document.documentElement;

  const isLightThemeActive = () => root.getAttribute("data-theme") === "light";

  const updateToggleLabel = () => {
    const isLight = isLightThemeActive();
    toggleButton.setAttribute("aria-label", isLight ? messages.enableDarkTheme : messages.enableLightTheme);
    toggleButton.setAttribute("aria-pressed", String(isLight));
  };

  toggleButton.addEventListener("click", () => {
    const nextTheme = isLightThemeActive() ? "dark" : "light";
    root.setAttribute("data-theme", nextTheme);
    saveTheme(nextTheme);
    updateToggleLabel();
  });

  updateToggleLabel();
}

function initMobileMenu() {
  const toggleButton = document.querySelector("[data-menu-toggle]");
  const navigation = document.getElementById("main-nav");
  if (!toggleButton || !navigation) return;

  const setMenuOpen = (isOpen) => {
    navigation.classList.toggle("nav--open", isOpen);
    toggleButton.setAttribute("aria-expanded", String(isOpen));
    toggleButton.setAttribute("aria-label", isOpen ? messages.closeMenu : messages.openMenu);
  };

  const isMenuOpen = () => toggleButton.getAttribute("aria-expanded") === "true";

  toggleButton.addEventListener("click", () => setMenuOpen(!isMenuOpen()));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isMenuOpen()) {
      setMenuOpen(false);
      toggleButton.focus();
    }
  });

  navigation.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMenuOpen(false));
  });
}

function initHeaderScrollState() {
  const header = document.querySelector(".header");
  if (!header) return;

  const updateHeaderBorder = () => {
    header.classList.toggle("header--scrolled", window.scrollY > HEADER_SCROLL_THRESHOLD_PX);
  };

  window.addEventListener("scroll", updateHeaderBorder, { passive: true });
  updateHeaderBorder();
}

function showPhotoFallbackIfMissing(media, photo) {
  const showFallback = () => media.classList.add("hero__media--fallback");

  photo.addEventListener("error", showFallback);

  if (photo.complete && photo.naturalWidth === 0) {
    showFallback();
  }
}

function initHeroPhotoFade() {
  const hero = document.querySelector("[data-hero]");
  if (!hero) return;

  const media = hero.querySelector(".hero__media");
  const photo = hero.querySelector(".hero__photo");

  if (media && photo) {
    showPhotoFallbackIfMissing(media, photo);
  }

  if (prefersReducedMotion) return;

  let isFrameRequested = false;

  const updateFadeProgress = () => {
    const fadeDistance = hero.offsetHeight * 0.8;
    const progress = Math.min(Math.max(window.scrollY / fadeDistance, 0), 1);
    hero.style.setProperty("--hero-progress", progress.toFixed(3));
    isFrameRequested = false;
  };

  const requestFadeUpdate = () => {
    if (isFrameRequested) return;
    isFrameRequested = true;
    window.requestAnimationFrame(updateFadeProgress);
  };

  window.addEventListener("scroll", requestFadeUpdate, { passive: true });
  updateFadeProgress();
}

function initRevealOnScroll() {
  const elements = document.querySelectorAll(".reveal");
  if (!elements.length) return;

  const revealElement = (element) => element.classList.add("is-visible");

  if (prefersReducedMotion || !("IntersectionObserver" in window)) {
    elements.forEach(revealElement);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries
        .filter((entry) => entry.isIntersecting)
        .forEach((entry) => {
          revealElement(entry.target);
          observer.unobserve(entry.target);
        });
    },
    { threshold: REVEAL_VISIBILITY_THRESHOLD }
  );

  elements.forEach((element) => observer.observe(element));
}

function initCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach((button) => {
    const defaultLabel = button.getAttribute("aria-label");

    const resetButton = () => {
      button.setAttribute("aria-label", defaultLabel);
      button.classList.remove("is-copied");
    };

    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        button.setAttribute("aria-label", messages.emailCopied);
        button.classList.add("is-copied");
      } catch {
        button.setAttribute("aria-label", messages.copyFailed);
      }

      window.setTimeout(resetButton, COPY_FEEDBACK_DURATION_MS);
    });
  });
}

async function sendContactForm(form) {
  const response = await fetch(form.action, {
    method: "POST",
    body: new FormData(form),
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Contact form request failed with status ${response.status}`);
  }
}

function initContactForm() {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const statusMessage = form.querySelector("[data-form-status]");
  const submitButton = form.querySelector("[type='submit']");

  const displayStatus = (message, type) => {
    statusMessage.textContent = message;
    statusMessage.className = `form__status form__status--${type}`;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    submitButton.disabled = true;
    displayStatus(messages.formSending, "success");

    try {
      await sendContactForm(form);
      form.reset();
      displayStatus(messages.formSent, "success");
    } catch {
      displayStatus(messages.formFailed, "error");
    } finally {
      submitButton.disabled = false;
    }
  });
}

function hideMissingLogos() {
  document.querySelectorAll("[data-logo]").forEach((logo) => {
    const removeLogo = () => logo.remove();

    logo.addEventListener("error", removeLogo);

    if (logo.complete && logo.naturalWidth === 0) {
      removeLogo();
    }
  });
}

function displayCurrentYear() {
  const currentYear = String(new Date().getFullYear());

  document.querySelectorAll("[data-year]").forEach((element) => {
    element.textContent = currentYear;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initMobileMenu();
  initHeaderScrollState();
  initHeroPhotoFade();
  initRevealOnScroll();
  initCopyButtons();
  initContactForm();
  hideMissingLogos();
  displayCurrentYear();
});
