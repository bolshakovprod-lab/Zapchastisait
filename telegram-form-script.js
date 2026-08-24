// ─────────────────────────────────────────────────────────────
//  Посредник «форма на сайте -> Telegram».
//  Куда вставлять: script.google.com -> Новый проект -> заменить
//  весь код на этот -> вписать свои TOKEN и CHAT_ID -> Развернуть.
//  Подробная инструкция — в README проекта.
// ─────────────────────────────────────────────────────────────

const TOKEN = 'СЮДА_ТОКЕН_БОТА';   // тот, что выдал @BotFather
const CHAT_ID = 'СЮДА_ID_ГРУППЫ';  // id группы «Заявки», начинается с -100

function doPost(e) {
  try {
    const d = JSON.parse(e.postData.contents);
    const text =
      '🔧 <b>Заявка с сайта</b>\n\n' +
      '📞 <b>Телефон:</b> ' + esc(d.phone) + '\n' +
      (d.car ? '🚗 <b>Машина:</b> ' + esc(d.car) + '\n' : '') +
      '📄 <b>Страница:</b> ' + esc(d.page) + '\n' +
      '📊 <b>Источник:</b> ' + esc(d.source) + '\n\n' +
      '<a href="' + esc(d.url) + '">открыть страницу</a>';

    UrlFetchApp.fetch('https://api.telegram.org/bot' + TOKEN + '/sendMessage', {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        chat_id: CHAT_ID,
        text: text,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    });
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('error: ' + err);
  }
}

function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Разовая проверка: запустите эту функцию, чтобы убедиться,
// что бот пишет в группу. В группе должно появиться «проверка связи».
function test() {
  UrlFetchApp.fetch('https://api.telegram.org/bot' + TOKEN + '/sendMessage', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ chat_id: CHAT_ID, text: 'проверка связи' })
  });
}
