'use strict';
// ─────────────────────────────────────────────────────────────
//  Аналитика: Яндекс.Метрика, цели и метка источника рекламы.
//  Номер счётчика вписывается в config.js -> SHOP.metrika
// ─────────────────────────────────────────────────────────────
(function () {
  const S = window.SHOP || {};

  // ─── счётчик Метрики ───
  if (S.metrika) {
    // Сниппет в актуальном виде: id в адресе tag.js, проверка на повторную вставку.
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      for (var j = 0; j < e.scripts.length; j++) { if (e.scripts[j].src === r) return; }
      k = e.createElement(t); a = e.getElementsByTagName(t)[0];
      k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, 'script',
       'https://mc.yandex.ru/metrika/tag.js?id=' + S.metrika, 'ym');
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
  saveSource();

  // ─── цели: звонок, мессенджеры, открытие карточки ───
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (!a) return;
    if (a.href.startsWith('tel:')) goal('call');
    else if (a.href.includes('max.ru/')) goal('max');
    else if (a.href.includes('t.me/')) goal('telegram');
    else if (/\/p\/[^/]+\.html$/.test(a.getAttribute('href') || '')) goal('part_view');
  });

  // карточка товара на главной открывается без перехода — ловим отдельно
  document.addEventListener('click', e => {
    if (e.target.closest('#grid .card')) goal('part_view');
  });
})();
