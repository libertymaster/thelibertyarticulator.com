document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy-citation]');
  if (!button) return;
  const text = document.getElementById(button.dataset.copyCitation)?.textContent;
  const status = button.parentElement.querySelector('[data-copy-status]');
  if (!text || !status) return;
  try {
    if (!navigator.clipboard) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(text.trim());
    status.textContent = 'Citation copied.';
  } catch {
    status.textContent = 'Clipboard access is unavailable. Select and copy the citation text above.';
  }
});
