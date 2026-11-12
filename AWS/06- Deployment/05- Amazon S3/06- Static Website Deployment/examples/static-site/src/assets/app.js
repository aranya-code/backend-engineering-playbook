(() => {
  "use strict";

  const menuToggle = document.querySelector("#menu-toggle");
  const primaryNavigation = document.querySelector("#primary-navigation");
  const currentYear = document.querySelector("#current-year");

  /**
   * Keep the footer year current without requiring a deployment update.
   */
  if (currentYear) {
    currentYear.textContent = String(new Date().getFullYear());
  }

  if (!menuToggle || !primaryNavigation) {
    return;
  }

  const mobileViewport = window.matchMedia("(max-width: 760px)");

  /**
   * Synchronize the mobile navigation visibility and accessibility state.
   */
  const setNavigationOpen = (isOpen) => {
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    primaryNavigation.classList.toggle("is-open", isOpen);
  };

  const isNavigationOpen = () =>
    menuToggle.getAttribute("aria-expanded") === "true";

  const closeNavigation = ({ restoreFocus = false } = {}) => {
    if (!isNavigationOpen()) {
      return;
    }

    setNavigationOpen(false);

    if (restoreFocus) {
      menuToggle.focus();
    }
  };

  menuToggle.addEventListener("click", () => {
    setNavigationOpen(!isNavigationOpen());
  });

  /**
   * Close the menu after a navigation link is selected.
   */
  primaryNavigation.addEventListener("click", (event) => {
    const link = event.target.closest("a");

    if (!link || !primaryNavigation.contains(link)) {
      return;
    }

    closeNavigation();
  });

  /**
   * Allow keyboard users to dismiss the expanded navigation.
   */
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isNavigationOpen()) {
      closeNavigation({ restoreFocus: true });
    }
  });

  /**
   * Close the menu when the user clicks outside the navigation controls.
   */
  document.addEventListener("click", (event) => {
    if (!isNavigationOpen()) {
      return;
    }

    const clickedInsideNavigation =
      primaryNavigation.contains(event.target) ||
      menuToggle.contains(event.target);

    if (!clickedInsideNavigation) {
      closeNavigation();
    }
  });

  /**
   * Reset mobile navigation state when returning to the desktop layout.
   */
  const handleViewportChange = (event) => {
    if (!event.matches) {
      closeNavigation();
      primaryNavigation.classList.remove("is-open");
    }
  };

  if (typeof mobileViewport.addEventListener === "function") {
    mobileViewport.addEventListener("change", handleViewportChange);
  } else {
    // Compatibility fallback for older browser implementations.
    mobileViewport.addListener(handleViewportChange);
  }
})();