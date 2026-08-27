'use strict';
// ─────────────────────────────────────────────────────────────
//  Форма заявки. Отправляется в Telegram-бота через посредника
//  на Google Apps Script (адрес задаётся в config.js -> formEndpoint).
//  Токен бота хранится в скрипте, на сайте его нет.
// ─────────────────────────────────────────────────────────────
(function () {
  const S = window.SHOP || {};
  if (!S.formEndpoint) return;

  const source = () => {
    try {
      const raw = JSON.parse(localStorage.getItem('src') || 'null');
      return raw && raw.label ? raw.label : 'прямой заход';
    } catch (e) { return 'прямой заход'; }
  };

  const subject = () => {
    const h1 = document.querySelector('.m-title, h1');
    return (h1 ? h1.textContent : document.title).trim().slice(0, 120);
  };

  const up = location.pathname.split('/').length > 2 ? '../' : '';

  const box = document.createElement('section');
  box.className = 'wrap';
  box.innerHTML = `
  <form class="lead-form" id="leadForm">
    <div class="lf-head">
      <h2>Подберём агрегат под вашу машину</h2>
      <p>Оставьте номер и VIN — проверим по складу и ответим. Обычно в течение часа.</p>
    </div>
    <div class="lf-row">
      <input name="phone" type="tel" required placeholder="Ваш телефон" autocomplete="tel">
      <input name="car" type="text" placeholder="Марка, модель, год или VIN">
      <button type="submit">Отправить заявку</button>
    </div>
    <label class="lf-agree">
      <input type="checkbox" required>
      <span>Согласен на обработку персональных данных
        (<a href="${up}privacy.html">политика</a>)</span>
    </label>
    <input type="text" name="trap" style="display:none" tabindex="-1" autocomplete="off">
  </form>`;

  const anchor = document.querySelector('.help') || document.querySelector('.foot');
  (anchor && anchor.parentNode).insertBefore(box, anchor);

  const form = box.querySelector('#leadForm');
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (form.trap.value) return;                    // ловушка для роботов
    const btn = form.querySelector('button');
    btn.disabled = true;
    btn.textContent = 'Отправляем…';

    const data = {
      phone: form.phone.value.trim(),
      car: form.car.value.trim(),
      page: subject(),
      url: location.href,
      source: source()
    };

    try {
      await fetch(S.formEndpoint, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(data)
      });
      if (S.metrika && window.ym) ym(S.metrika, 'reachGoal', 'lead_form');
      form.innerHTML = `<div class="lf-done">
        <b>Заявка отправлена.</b> Ответим в течение часа в рабочее время.
        Если срочно — звоните: <a href="tel:${S.phoneTel}">${S.phone}</a></div>`;
    } catch (err) {
      btn.disabled = false;
      btn.textContent = 'Отправить заявку';
      alert('Не удалось отправить. Позвоните или напишите в MAX: ' + (S.phone || ''));
    }
  });
})();
