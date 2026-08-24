'use strict';
// ─────────────────────────────────────────────────────────────
//  Кнопка связи: выбор мессенджера. Сообщение уходит с контекстом
//  страницы и меткой рекламного источника.
// ─────────────────────────────────────────────────────────────
(function () {
  const S = window.SHOP || {};

  // о чём страница — подставим в первое сообщение
  function subject() {
    const h1 = document.querySelector('.m-title, h1');
    const t = (h1 ? h1.textContent : document.title).trim();
    const art = document.querySelector('.m-tags .tag:last-child');
    const artText = art && art.textContent.includes('арт.') ? ', ' + art.textContent.trim() : '';
    return t.length > 90 ? t.slice(0, 90) + '…' : t + artText;
  }

  function source() {
    try {
      const raw = JSON.parse(localStorage.getItem('src') || 'null');
      return raw && raw.label ? ` [${raw.label}]` : '';
    } catch (e) { return ''; }
  }

  function message() {
    const onPart = location.pathname.includes('/p/');
    const head = onPart ? 'Здравствуйте! Интересует: ' : 'Здравствуйте! Подскажите по агрегату. ';
    return head + (onPart ? subject() : '') + source();
  }

  const CHANNELS = [
    { key: 'whatsapp', name: 'WhatsApp', cls: 'wa', color: '#25D366',
      href: () => `https://wa.me/${S.whatsapp}?text=${encodeURIComponent(message())}`,
      icon: '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5.1-1.3A10 10 0 1 0 12 2Zm5.8 14.2c-.2.7-1.4 1.3-2 1.4-.5.1-1.1.1-1.8-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5.1-4.5-.1-.2-1.2-1.5-1.2-2.9 0-1.4.7-2 1-2.3.2-.3.6-.4.8-.4h.6c.2 0 .4 0 .7.5l.9 2.1c.1.2.1.4 0 .6l-.4.6-.3.3c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.2.4-.2.6-.1l2 1c.3.1.5.2.5.3.1.2.1.6 0 1Z"/>' },
    { key: 'telegram', name: 'Telegram', cls: 'tg', color: '#2AABEE',
      href: () => `https://t.me/${S.telegram}`,
      icon: '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm4.6 6.8-1.6 7.5c-.1.5-.4.7-.9.4l-2.4-1.8-1.2 1.1c-.1.1-.3.3-.6.3l.2-2.5 4.5-4c.2-.2 0-.3-.3-.1l-5.5 3.5-2.4-.7c-.5-.2-.5-.5.1-.8l9.3-3.6c.4-.2.8.1.8.7Z"/>' },
    { key: 'max', name: 'MAX', cls: 'max', color: '#7C5CFF',
      href: () => `https://max.ru/${S.max}`,
      icon: '<path d="M4 4h3.2l4.8 7.4L16.8 4H20v16h-3.2V9.6l-4.1 6.2h-.4L8.2 9.6V20H5V4Z"/>' },
    { key: 'phone', name: 'Позвонить', cls: 'call', color: '#e8442a',
      href: () => `tel:${S.phoneTel}`,
      icon: '<path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.4 2.4.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.4c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 .8-.2 1l-2.2 2.2Z"/>' },
  ];

  const active = CHANNELS.filter(c =>
    (c.key === 'whatsapp' && S.whatsapp) ||
    (c.key === 'telegram' && S.telegram) ||
    (c.key === 'max' && S.max) ||
    (c.key === 'phone' && S.phoneTel));
  if (!active.length) return;

  const box = document.createElement('div');
  box.className = 'chat-widget';
  box.innerHTML = `
    <div class="chat-list" id="chatList" hidden>
      <div class="chat-head">Как вам удобнее написать?</div>
      ${active.map(c => `
        <a class="chat-item ${c.cls}" href="#" data-key="${c.key}" target="_blank" rel="noopener">
          <span class="chat-ico" style="background:${c.color}">
            <svg viewBox="0 0 24 24" width="19" height="19" fill="#fff">${c.icon}</svg>
          </span>
          <span>${c.name}</span>
        </a>`).join('')}
      <div class="chat-note">Ответим и подберём по VIN — даже если этого агрегата нет в наличии</div>
    </div>
    <button class="chat-fab" id="chatFab" type="button" aria-label="Связаться">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
        <path d="M12 3c5 0 9 3.4 9 7.5S17 18 12 18c-1 0-2-.1-2.9-.4L4 19l1.3-3.2C3.9 14.5 3 12.6 3 10.5 3 6.4 7 3 12 3Z"/>
      </svg>
      <span class="chat-fab-text">Написать</span>
    </button>`;
  document.body.appendChild(box);

  const list = box.querySelector('#chatList');
  const fab = box.querySelector('#chatFab');

  fab.onclick = () => {
    list.hidden = !list.hidden;
    box.classList.toggle('open', !list.hidden);
    if (!list.hidden) {
      // ссылки строим в момент открытия: текст зависит от страницы
      active.forEach(c => {
        const a = list.querySelector(`[data-key="${c.key}"]`);
        a.href = c.href();
        if (c.key === 'phone') a.removeAttribute('target');
      });
    }
  };
  document.addEventListener('click', e => {
    if (!box.contains(e.target) && !list.hidden) {
      list.hidden = true;
      box.classList.remove('open');
    }
  });
})();
