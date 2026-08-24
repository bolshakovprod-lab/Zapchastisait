'use strict';
// ─────────────────────────────────────────────────────────────
//  Форма заявки. Отправляется через formsubmit.co — заявка
//  приходит письмом на почту (и копией второму адресу).
//  Адреса задаются в config.js -> SHOP.formTo и SHOP.formCc
// ─────────────────────────────────────────────────────────────
(function () {
  const S = window.SHOP || {};
  if (!S.formTo) return;

  function source() {
    try {
      const raw = JSON.parse(localStorage.getItem('src') || 'null');
      return raw && raw.label ? raw.label : 'прямой заход';
    } catch (e) { return ''; }
  }

  function subject() {
    const h1 = document.querySelector('.m-title, h1');
    return (h1 ? h1.textContent : document.title).trim().slice(0, 120);
  }

  const box = document.createElement('section');
  box.className = 'wrap';
  box.innerHTML = `
  <form class="lead-form" id="leadForm" method="POST"
        action="https://formsubmit.co/${S.formTo}">
    <div class="lf-head">
      <h2>Подберём агрегат под вашу машину</h2>
      <p>Оставьте номер и VIN — проверим по складу и ответим. Обычно в течение часа.</p>
    </div>
    <div class="lf-row">
      <input name="Телефон" type="tel" required placeholder="Ваш телефон" autocomplete="tel">
      <input name="Машина" type="text" placeholder="Марка, модель, год или VIN">
      <button type="submit">Отправить заявку</button>
    </div>
    <label class="lf-agree">
      <input type="checkbox" required>
      <span>Согласен на обработку персональных данных
        (<a href="${location.pathname.includes('/') && location.pathname.split('/').length > 2 ? '../' : ''}privacy.html">политика</a>)</span>
    </label>
    <input type="hidden" name="Страница" value="">
    <input type="hidden" name="Источник" value="">
    <input type="hidden" name="_subject" value="Заявка с сайта">
    <input type="hidden" name="_captcha" value="false">
    <input type="hidden" name="_template" value="table">
    ${S.formCc ? `<input type="hidden" name="_cc" value="${S.formCc}">` : ''}
    <input type="hidden" name="_next" value="${location.origin}${location.pathname}?sent=1">
    <input type="text" name="_honey" style="display:none">
  </form>`;

  const anchor = document.querySelector('.help') || document.querySelector('.foot');
  (anchor && anchor.parentNode).insertBefore(box, anchor);

  const f = box.querySelector('#leadForm');
  f.querySelector('[name="Страница"]').value = subject();
  f.querySelector('[name="Источник"]').value = source();
  f.addEventListener('submit', () => {
    if (S.metrika && window.ym) ym(S.metrika, 'reachGoal', 'lead_form');
  });

  // вернулись после отправки — показываем спасибо
  if (new URLSearchParams(location.search).get('sent') === '1') {
    f.innerHTML = `<div class="lf-done">
      <b>Заявка отправлена.</b> Перезвоним или напишем в течение часа в рабочее время.
      Если срочно — звоните: <a href="tel:${S.phoneTel}">${S.phone}</a></div>`;
  }
})();
