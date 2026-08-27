'use strict';
// Подставляет данные сервиса и контакты на странице установочного центра
(function () {
  const S = window.SHOP || {}, V = window.SERVICE || {};
  const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };

  set('srvAddress', V.address || '');
  set('srvHours', V.hours || '');
  set('srvPhone', S.phone || '');

  const phone = document.getElementById('srvPhone');
  if (phone) phone.href = 'tel:' + (S.phoneTel || '');

  const call = document.getElementById('srvCall');
  if (call) { call.href = 'tel:' + (S.phoneTel || ''); call.textContent = 'Позвонить ' + (S.phone || ''); }

  const maxLink = S.max ? `https://max.ru/${S.max}` : '';
  const srvMax = document.getElementById('srvMax');
  if (srvMax) { if (maxLink) srvMax.href = maxLink; else srvMax.remove(); }

  // кнопка в шапке: на этой странице нет app.js, поэтому подставляем здесь
  const headMax = document.getElementById('headMax');
  if (headMax) { if (maxLink) headMax.href = maxLink; else headMax.remove(); }

  const map = document.getElementById('srvMap');
  if (map) { if (V.map) map.href = V.map; else map.remove(); }

  const hCall = document.getElementById('helpCall');
  if (hCall) { hCall.href = 'tel:' + (S.phoneTel || ''); hCall.textContent = 'Позвонить ' + (S.phone || ''); }
  const hMax = document.getElementById('helpMax');
  if (hMax) { if (maxLink) hMax.href = maxLink; else hMax.remove(); }
})();
