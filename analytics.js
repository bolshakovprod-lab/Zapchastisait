'use strict';
// ─────────────────────────────────────────────────────────────
//  Аналитика: Яндекс.Метрика, цели и метка источника рекламы.
//  Номер счётчика вписывается в config.js -> SHOP.metrika
// ─────────────────────────────────────────────────────────────
(function () {
  const S = window.SHOP || {};

  // ─── счётчик Метрики ───
  if (S.metrika) {
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      k = e.createElement(t); a = e.getElementsByTagName(t)[0];
      k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    ym(S.metrika, 'init', {
      clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: true
    });
  }

  const goal = name => { if (S.metrika && window.ym) ym(S.metrika, 'reachGoal', name); };

  // ─── откуда пришёл человек: запоминаем на 30 дней ───
  const SOURCE_KEY = 'src';
  function saveSource() {
    const p = new URLSearchParams(location.search);
    const utm = p.get('utm_source');
    if (!utm) return;
    const label = [utm, p.get('utm_campaign'), p.get('utm_content')].filter(Boolean).join(' / ');
    try {
      localStorage.setItem(SOURCE_KEY, JSON.stringify({ label, at: Date.now() }));
    } catch (e) { /* приватный режим */ }
  }
  function source() {
    try {
      const raw = JSON.parse(localStorage.getItem(SOURCE_KEY) || 'null');
      if (!raw) return '';
      if (Date.now() - raw.at > 30 * 24 * 3600 * 1000) return '';
      return raw.label;
    } catch (e) { return ''; }
  }
  saveSource();

  // ─── метка источника в текст сообщения WhatsApp ───
  // Так в переписке сразу видно, с какой рекламы пришёл человек.
  function tagLinks() {
    const src = source();
    if (!src) return;
    document.querySelectorAll('a[href*="wa.me/"]').forEach(a => {
      if (a.dataset.tagged) return;
      a.dataset.tagged = '1';
      const url = new URL(a.href);
      const text = url.searchParams.get('text') || '';
      url.searchParams.set('text', text + ` [${src}]`);
      a.href = url.toString();
    });
  }
  tagLinks();
  new MutationObserver(tagLinks).observe(document.body, { childList: true, subtree: true });

  // ─── цели: звонок, WhatsApp, открытие карточки ───
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (!a) return;
    if (a.href.startsWith('tel:')) goal('call');
    else if (a.href.includes('wa.me/')) goal('whatsapp');
    else if (a.href.includes('t.me/')) goal('telegram');
    else if (/\/p\/[^/]+\.html$/.test(a.getAttribute('href') || '')) goal('part_view');
  });

  // карточка товара на главной открывается без перехода — ловим отдельно
  document.addEventListener('click', e => {
    if (e.target.closest('#grid .card')) goal('part_view');
  });
})();
