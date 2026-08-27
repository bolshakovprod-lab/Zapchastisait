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

  const msg = encodeURIComponent('Здравствуйте! Хочу записаться на замену агрегата. Машина: ');
  const wa = document.getElementById('srvWa');
  if (wa) { if (S.whatsapp) wa.href = `https://wa.me/${S.whatsapp}?text=${msg}`; else wa.remove(); }

  const map = document.getElementById('srvMap');
  if (map) { if (V.map) map.href = V.map; else map.remove(); }

  const hCall = document.getElementById('helpCall');
  if (hCall) { hCall.href = 'tel:' + (S.phoneTel || ''); hCall.textContent = 'Позвонить ' + (S.phone || ''); }
  const hWa = document.getElementById('helpWa');
  if (hWa) { if (S.whatsapp) hWa.href = `https://wa.me/${S.whatsapp}?text=${msg}`; else hWa.remove(); }
})();
