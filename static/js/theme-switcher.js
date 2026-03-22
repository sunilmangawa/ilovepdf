/**
 * Theme Switcher - Modern Dark/Light Mode Toggle
 * Targets the #themeToggle button in the navbar
 * Saves preference to localStorage
 */

(function() {
  'use strict';

  // Theme configuration
  const THEME_STORAGE_KEY = 'ilovepdf-theme-preference';
  const DARK_THEME = 'dark';
  const LIGHT_THEME = 'light';

  /**
   * Get current theme from localStorage or system preference.
   */
  function getCurrentTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme) {
      return savedTheme;
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return DARK_THEME;
    }
    return LIGHT_THEME;
  }

  /**
   * Apply theme to document.
   */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
  }

  /**
   * Update theme toggle icon visibility.
   */
  function updateThemeIcon(theme) {
    const sunIcon = document.querySelector('.theme-icon-sun');
    const moonIcon = document.querySelector('.theme-icon-moon');
    if (!sunIcon || !moonIcon) return;

    if (theme === DARK_THEME) {
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'inline-block';
    } else {
      sunIcon.style.display = 'inline-block';
      moonIcon.style.display = 'none';
    }
  }

  /**
   * Toggle between dark and light themes.
   */
  function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
    applyTheme(newTheme);

    // Smooth transition effect
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    setTimeout(() => {
      document.body.style.transition = '';
    }, 300);
  }

  /**
   * Initialize theme and bind click to existing navbar button.
   */
  function init() {
    const theme = getCurrentTheme();
    applyTheme(theme);

    // Bind to the navbar button (#themeToggle already in HTML)
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleTheme);
    }

    // Listen for system theme changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem(THEME_STORAGE_KEY)) {
          applyTheme(e.matches ? DARK_THEME : LIGHT_THEME);
        }
      });
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export for programmatic use
  window.ThemeSwitcher = {
    toggle: toggleTheme,
    setTheme: (theme) => {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
      applyTheme(theme);
    },
    getCurrentTheme: getCurrentTheme
  };
})();