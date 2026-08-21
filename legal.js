'use strict';
// Подставляет реквизиты из config.js в тексты документов
(function () {
  const S = window.SHOP || {}, L = window.LEGAL || {};
  const values = {
    entity: L.entity, inn: L.inn, ogrn: L.ogrn, address: L.address,
    email: L.email, updated: L.updated, phone: S.phone, hours: S.hours
  };
  document.querySelectorAll('[data-legal]').forEach(el => {
    el.textContent = values[el.dataset.legal] || '——————';
  });

  const p = document.querySelector('#headPhone');
  if (p) { p.textContent = S.phone || ''; p.href = 'tel:' + (S.phoneTel || ''); }
  const t = document.querySelector('.logo-text');
  if (t) t.textContent = S.name || '';

  const fc = document.querySelector('#footContacts');
  if (fc) fc.innerHTML = `<b>${S.name || ''}</b>${S.city ? ' · ' + S.city : ''} · ` +
    `<a href="tel:${S.phoneTel || ''}">${S.phone || ''}</a>`;
  const fh = document.querySelector('#footHours');
  if (fh) fh.textContent = [L.entity, S.hours].filter(Boolean).join(' · ');
})();
