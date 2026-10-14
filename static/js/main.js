document.addEventListener('DOMContentLoaded', () => {
  const importType = document.getElementById('import_type');
  const trainingSelect = document.getElementById('training-select');
  const toggleTraining = () => {
    if (!importType || !trainingSelect) return;
    trainingSelect.style.display = importType.value === 'training' ? 'block' : 'none';
  };
  if (importType) {
    importType.addEventListener('change', toggleTraining);
    toggleTraining();
  }
});

// 社内文書検索: フォーム送信中の状態を表示し、二重送信を防止する。
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('rag-search-form');
  const button = document.getElementById('rag-search-submit');
  const status = document.getElementById('rag-loading-status');
  if (!form || !button || !status) return;
  let submitting = false;
  form.addEventListener('submit', (event) => {
    if (submitting) { event.preventDefault(); return; }
    if (!form.checkValidity()) return;
    submitting = true;
    status.hidden = false;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.querySelector('.rag-submit-label').textContent = '検索中…';
    const result = document.querySelector('.result-title');
    if (result) result.scrollIntoView({block: 'nearest'});
    status.scrollIntoView({block: 'nearest', behavior: 'smooth'});
  });
  window.addEventListener('pageshow', () => {
    submitting = false;
    button.disabled = false;
    button.removeAttribute('aria-busy');
    button.querySelector('.rag-submit-label').textContent = '検索';
    status.hidden = true;
  });
});
