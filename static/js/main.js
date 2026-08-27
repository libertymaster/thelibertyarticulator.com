(() => {
  "use strict";

  const header = document.querySelector("[data-site-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const navigation = document.querySelector("[data-primary-nav]");

  if (header && toggle && navigation) {
    header.setAttribute("data-menu-ready", "");

    const closeMenu = (returnFocus = false) => {
      header.removeAttribute("data-menu-open");
      toggle.setAttribute("aria-expanded", "false");
      if (returnFocus) toggle.focus();
    };

    toggle.addEventListener("click", () => {
      const isOpen = header.hasAttribute("data-menu-open");
      if (isOpen) {
        closeMenu();
      } else {
        header.setAttribute("data-menu-open", "");
        toggle.setAttribute("aria-expanded", "true");
      }
    });

    navigation.addEventListener("click", (event) => {
      if (event.target.closest("a")) closeMenu();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && header.hasAttribute("data-menu-open")) closeMenu(true);
    });

    window.matchMedia("(min-width: 48.01rem)").addEventListener("change", (event) => {
      if (event.matches) closeMenu();
    });
  }

  document.querySelectorAll("[data-print]").forEach((button) => {
    button.addEventListener("click", () => window.print());
  });

  document.querySelectorAll("[data-copy-link]").forEach((button) => {
    button.addEventListener("click", async () => {
      const status = document.querySelector("[data-copy-status]");
      try {
        await navigator.clipboard.writeText(window.location.href);
        if (status) status.textContent = "Link copied.";
      } catch (error) {
        const temporary = document.createElement("textarea");
        temporary.value = window.location.href;
        temporary.setAttribute("readonly", "");
        temporary.style.position = "fixed";
        temporary.style.opacity = "0";
        document.body.appendChild(temporary);
        temporary.select();
        const copied = document.execCommand("copy");
        temporary.remove();
        if (status) status.textContent = copied ? "Link copied." : "Copy the address from your browser.";
      }
      window.setTimeout(() => {
        if (status) status.textContent = "";
      }, 3500);
    });
  });
})();
