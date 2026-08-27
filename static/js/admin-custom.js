(() => {
  "use strict";

  const doiPattern = /^10\.\d{4,9}\/[-._;()/:A-Z0-9]+$/i;
  const orcidPattern = /^(?:https?:\/\/orcid\.org\/)?\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/i;

  const normalizeDoi = (value) => value.trim().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");

  const validateIdentifier = (input) => {
    const key = `${input.name} ${input.id}`.toLowerCase();
    const value = input.value.trim();
    let message = "";

    if (value && key.includes("doi") && !doiPattern.test(normalizeDoi(value))) {
      message = "Enter a DOI such as 10.1000/example (a doi.org URL is also accepted).";
    }
    if (value && key.includes("orcid") && !orcidPattern.test(value)) {
      message = "Enter an ORCID such as 0000-0002-1825-0097.";
    }

    input.setCustomValidity(message);
    input.toggleAttribute("aria-invalid", Boolean(message));
  };

  const enhance = (root = document) => {
    root.querySelectorAll("input[name*='doi' i], input[id*='doi' i], input[name*='orcid' i], input[id*='orcid' i]").forEach((input) => {
      if (input.dataset.identifierValidationReady) return;
      input.dataset.identifierValidationReady = "true";
      input.addEventListener("input", () => validateIdentifier(input));
      input.addEventListener("blur", () => {
        validateIdentifier(input);
        if (!input.checkValidity()) input.reportValidity();
      });
    });
  };

  enhance();
  new MutationObserver((mutations) => {
    mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) enhance(node);
    }));
  }).observe(document.body, { childList: true, subtree: true });
})();
