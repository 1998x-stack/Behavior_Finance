/* This script runs before the deferred MathJax library. */
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']]
  },
  options: { renderActions: { addMenu: [0, '', ''] } }
};

(function () {
  'use strict';
  const VERSION = 1;
  const MAX_NOTE_LENGTH = 2000;

  function init() {
    const article = document.querySelector('.container');
    if (!article) return;
    const storageKey = 'behavior-finance:annotations:v1:' + location.pathname;
    const status = document.createElement('span');
    status.className = 'note-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    const notes = loadNotes();

    function loadNotes() {
      try {
        const data = JSON.parse(localStorage.getItem(storageKey) || '{}');
        if (data && data.version === VERSION && data.notes && typeof data.notes === 'object' && !Array.isArray(data.notes)) {
          return data.notes;
        }
      } catch (_) { /* Storage can be unavailable on file: URLs. */ }
      return Object.create(null);
    }

    function storeNotes() {
      try {
        localStorage.setItem(storageKey, JSON.stringify({ version: VERSION, notes: notes }));
        status.textContent = '批注已保存到本浏览器';
      } catch (_) {
        status.textContent = '无法本地保存；请导出文章与批注以免丢失';
      }
    }

    function addRenderedNote(block, value) {
      const box = document.createElement('aside');
      box.className = 'comment';
      box.textContent = value; // Never interpret reader input as HTML.
      block.appendChild(box);
    }

    function edit(block, anchor) {
      if (block.querySelector('.comment-editor')) return;
      const wrap = document.createElement('span');
      wrap.className = 'comment-editor';
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = MAX_NOTE_LENGTH;
      input.placeholder = '输入批注，回车保存，Esc 取消';
      input.setAttribute('aria-label', '批注内容');
      wrap.appendChild(input);
      block.appendChild(wrap);
      let finished = false;
      function close(save) {
        if (finished) return;
        finished = true;
        const value = input.value.trim();
        wrap.remove();
        if (save && value) {
          const existing = Array.isArray(notes[anchor]) ? notes[anchor] : [];
          notes[anchor] = [...existing, value];
          addRenderedNote(block, value);
          storeNotes();
        }
      }
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') { event.preventDefault(); close(true); }
        if (event.key === 'Escape') { event.preventDefault(); close(false); }
      });
      input.addEventListener('blur', function () { close(true); });
      input.focus();
    }

    const blocks = Array.from(article.querySelectorAll('p, li')).filter(function (block) {
      return block.tagName === 'LI' || !block.closest('li');
    });
    blocks.forEach(function (block, index) {
      const anchor = 'block-' + String(index + 1).padStart(4, '0');
      block.dataset.noteAnchor = anchor;
      const saved = Array.isArray(notes[anchor]) ? notes[anchor] : [];
      saved.filter(value => typeof value === 'string').forEach(value => addRenderedNote(block, value));
      block.addEventListener('dblclick', function (event) {
        if (!event.target.closest('button, input, a')) edit(block, anchor);
      });
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'comment-add';
      button.textContent = '批注';
      button.setAttribute('aria-label', '为这一段添加批注');
      button.addEventListener('click', function () { edit(block, anchor); });
      block.appendChild(button);
    });

    article.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(function (heading) {
      heading.addEventListener('click', function () {
        heading.scrollIntoView({ behavior: 'smooth' });
      });
    });

    const toolbar = document.createElement('div');
    toolbar.className = 'note-toolbar';
    const exportButton = document.createElement('button');
    exportButton.className = 'save-button';
    exportButton.type = 'button';
    exportButton.textContent = '导出文章与批注';
    exportButton.addEventListener('click', function () {
      const copy = article.cloneNode(true);
      copy.querySelectorAll('.comment-add, .comment-editor').forEach(node => node.remove());
      copy.querySelectorAll('[data-note-anchor]').forEach(node => node.removeAttribute('data-note-anchor'));
      const safeTitle = document.title.replace(/[<>]/g, '');
      const html = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">' +
        '<meta name="viewport" content="width=device-width, initial-scale=1">' +
        '<title>' + safeTitle + '</title>' +
        '<style>body{font:16px/1.8 system-ui,sans-serif;max-width:850px;margin:2rem auto;padding:0 1rem;overflow-wrap:anywhere}' +
        '.comment{margin:.5rem 0;padding:.6rem;background:#e7f3ff;border-left:3px solid #2769aa;white-space:pre-wrap}' +
        'pre{overflow-x:auto}table{display:block;overflow-x:auto;border-collapse:collapse}td,th{border:1px solid #ddd;padding:.5rem}</style>' +
        '</head><body>' + copy.outerHTML + '</body></html>';
      const objectUrl = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = 'behavior-finance-annotated.html';
      link.click();
      setTimeout(function () { URL.revokeObjectURL(objectUrl); }, 1000);
    });
    toolbar.appendChild(exportButton);
    toolbar.appendChild(status);
    document.body.appendChild(toolbar);
    if (window.hljs && typeof window.hljs.highlightAll === 'function') window.hljs.highlightAll();
    // MathJax automatically typesets on startup; no DOMContentLoaded race.
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}());
