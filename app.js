'use strict';
const S = window.SHOP || {};
const PAGE = 60;
let DB = null, view = [], shown = 0;

const $ = s => document.querySelector(s);
const els = {
  q: $('#q'), grid: $('#grid'), status: $('#status'), more: $('#more'),
  brand: $('#fBrand'), cat: $('#fCat'),
  min: $('#fMin'), max: $('#fMax'), sort: $('#fSort'), photo: $('#fPhoto'),
  filters: $('#filters'), modal: $('#modal'), modalBody: $('#modalBody')
};

const money = n => n ? n.toLocaleString('ru-RU') + ' ₽' : 'цена по запросу';
const plural = (n, one, few, many) => {
  const a = Math.abs(n) % 100, b = a % 10;
  return a > 10 && a < 20 ? many : b > 1 && b < 5 ? few : b === 1 ? one : many;
};
const pad = i => String(i).padStart(8, '0');
const photoUrl = (it, n) => DB.photoBase[it.g] + pad(it.i) + '_' + n + '.jpg';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : '';
const carLine = it => [it.b, it.m, it.k, it.e].filter(Boolean).join(' ');
const alnum = s => s.toLowerCase().replace(/[^a-zа-я0-9]/gi, '');

// ─── контакты ───
function contacts() {
  document.title = S.city ? `${S.name} — ${S.city}` : S.name;
  $('#headPhone').textContent = S.phone || '';
  $('#headPhone').href = 'tel:' + (S.phoneTel || '');
  $('.logo').lastChild.textContent = ' ' + (S.name || 'Запчасти');
  $('#footContacts').innerHTML =
    `<b>${esc(S.name)}</b>${S.city ? ' · ' + esc(S.city) : ''} · ` +
    `<a href="tel:${esc(S.phoneTel)}">${esc(S.phone)}</a>` +
    (S.updated ? ` · каталог обновлён ${esc(S.updated)}` : '');
}

// ─── загрузка ───
async function load() {
  contacts();
  try {
    const r = await fetch('data/parts.json');
    DB = await r.json();
  } catch (e) {
    els.status.textContent = 'Не удалось загрузить каталог. Обновите страницу.';
    return;
  }
  DB.items.forEach(it => {
    it._h = [it.n, it.b, it.m, it.k, it.e, it.d, it.o, it.t, it.y].join(' ').toLowerCase();
    it._a = alnum(it.d + ' ' + it.o);
  });
  fill(els.brand, DB.brands);
  fill(els.cat, DB.cats.map(([n, c]) => [cap(n), c]), DB.cats.map(([n]) => n));
  readUrl();
  apply();
}

function fill(sel, pairs, values) {
  sel.append(...pairs.map(([label, count], i) => {
    const o = document.createElement('option');
    o.value = values ? values[i] : label;
    o.textContent = `${label} (${count})`;
    return o;
  }));
}

// ─── фильтрация ───
function apply(push = true) {
  const terms = els.q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const aq = alnum(els.q.value);
  const b = els.brand.value, c = els.cat.value;
  const mn = +els.min.value || 0, mx = +els.max.value || Infinity;
  const onlyPhoto = els.photo.checked;

  view = DB.items.filter(it => {
    if (b && it.b !== b) return false;
    if (c && it.n !== c) return false;
    if (it.p < mn || it.p > mx) return false;
    if (onlyPhoto && !it.f) return false;
    if (!terms.length) return true;
    // запрос целиком похож на номер детали — ищем по номерам без разделителей
    if (aq.length >= 5 && it._a.includes(aq)) return true;
    return terms.every(t => it._h.includes(t));
  });

  const s = els.sort.value;
  if (s === 'asc') view.sort((x, y) => (x.p || 1e9) - (y.p || 1e9));
  else if (s === 'desc') view.sort((x, y) => (y.p || 0) - (x.p || 0));

  els.status.textContent = view.length
    ? `Найдено ${view.length.toLocaleString('ru-RU')} ${plural(view.length, 'позиция', 'позиции', 'позиций')} из ${DB.count.toLocaleString('ru-RU')}`
    : 'Ничего не нашли. Попробуйте короче: марка и модель двигателя — «мазда lf-ve».';
  els.grid.innerHTML = '';
  shown = 0;
  render();
  if (push) writeUrl();
}

function render() {
  const part = view.slice(shown, shown + PAGE);
  const html = part.map(it => `
    <article class="card" data-i="${it.i}" data-g="${it.g}">
      <div class="thumb">${it.f
        ? `<img loading="lazy" src="${photoUrl(it, 1)}" alt="${esc(it.n)} ${esc(carLine(it))}"
             onerror="this.parentNode.innerHTML='<span class=nophoto>без фото</span>'">`
        : '<span class="nophoto">без фото</span>'}</div>
      <div class="card-b">
        <div class="card-title">${esc(cap(it.t || it.n))}</div>
        <div class="card-car">${esc(carLine(it))}${it.y ? ', ' + esc(it.y) : ''}</div>
        <div class="card-price">${money(it.p)}</div>
      </div>
    </article>`).join('');
  els.grid.insertAdjacentHTML('beforeend', html);
  shown += part.length;
  els.more.hidden = shown >= view.length;
}

// ─── карточка товара ───
function openPart(i, g) {
  const it = DB.items.find(x => x.i === i && x.g === g);
  if (!it) return;
  const shots = Array.from({ length: it.f }, (_, k) => photoUrl(it, k + 1));
  const row = (k, v) => v ? `<tr><td>${k}</td><td>${esc(v)}</td></tr>` : '';
  const msg = encodeURIComponent(
    `Здравствуйте! Интересует: ${cap(it.t || it.n)} (${carLine(it)}), артикул ${it.i}, ${money(it.p)}. В наличии?`);

  els.modalBody.innerHTML = `
    <div class="m-top">
      <div>
        ${shots.length
          ? `<img class="gal-main" id="galMain" src="${shots[0]}" alt="${esc(it.n)}">
             <div class="gal-strip">${shots.map((u, k) =>
               `<img src="${u}" class="${k ? '' : 'on'}" data-u="${u}" alt=""
                  onerror="this.remove()">`).join('')}</div>`
          : `<div class="gal-main" style="display:grid;place-items:center;color:var(--muted)">Фото нет</div>`}
      </div>
      <div>
        <h2 class="m-title">${esc(cap(it.t || it.n))}</h2>
        <span class="badge">${esc(it.c)}</span>
        <span class="badge">арт. ${esc(it.i)}</span>
        <div class="m-price">${money(it.p)}</div>
        <table class="specs">
          ${row('Марка', it.b)}${row('Модель', it.m)}${row('Кузов', it.k)}
          ${row('Двигатель', it.e)}${row('Год', it.y)}${row('Расположение', it.s)}
          ${row('Номер детали', it.d)}${row('OEM-номера', it.o)}
          ${row('Категория', cap(it.n))}
        </table>
        <div class="cta">
          <a class="call" href="tel:${esc(S.phoneTel)}">Позвонить</a>
          ${S.whatsapp ? `<a class="wa" target="_blank" rel="noopener"
             href="https://wa.me/${S.whatsapp}?text=${msg}">WhatsApp</a>` : ''}
          ${S.telegram ? `<a class="tg" target="_blank" rel="noopener"
             href="https://t.me/${S.telegram}">Telegram</a>` : ''}
        </div>
        <p class="muted" style="margin-top:12px">Отправим фото и видео детали, поможем с подбором по VIN.</p>
      </div>
    </div>`;
  els.modal.hidden = false;
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  els.modal.hidden = true;
  document.body.style.overflow = '';
}

// ─── состояние в адресе страницы ───
function writeUrl() {
  const p = new URLSearchParams();
  const add = (k, v) => v && p.set(k, v);
  add('q', els.q.value.trim());
  add('b', els.brand.value); add('c', els.cat.value);
  add('min', els.min.value); add('max', els.max.value);
  if (els.photo.checked) p.set('ph', '1');
  if (els.sort.value !== 'rel') p.set('s', els.sort.value);
  history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
}
function readUrl() {
  const p = new URLSearchParams(location.search);
  els.q.value = p.get('q') || '';
  els.brand.value = p.get('b') || ''; els.cat.value = p.get('c') || '';
  els.min.value = p.get('min') || ''; els.max.value = p.get('max') || '';
  els.photo.checked = p.get('ph') === '1'; els.sort.value = p.get('s') || 'rel';
  if ([...p.keys()].some(k => k !== 'q')) els.filters.classList.add('open');
}

// ─── события ───
let t;
els.q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(apply, 200); });
['change'].forEach(ev => [els.brand, els.cat, els.sort, els.photo]
  .forEach(el => el.addEventListener(ev, () => apply())));
[els.min, els.max].forEach(el => el.addEventListener('input', () => { clearTimeout(t); t = setTimeout(apply, 350); }));
$('#filtersBtn').onclick = () => els.filters.classList.toggle('open');
$('#reset').onclick = () => {
  els.q.value = ''; els.brand.value = ''; els.cat.value = '';
  els.min.value = ''; els.max.value = ''; els.photo.checked = false; els.sort.value = 'rel';
  apply();
};
els.more.onclick = render;
els.grid.addEventListener('click', e => {
  const c = e.target.closest('.card');
  if (c) openPart(c.dataset.i, c.dataset.g);
});
els.modal.addEventListener('click', e => {
  if (e.target.dataset.close !== undefined) closeModal();
  const th = e.target.closest('.gal-strip img');
  if (th) {
    $('#galMain').src = th.dataset.u;
    els.modalBody.querySelectorAll('.gal-strip img').forEach(i => i.classList.toggle('on', i === th));
  }
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
new IntersectionObserver(en => {
  if (en[0].isIntersecting && DB && shown < view.length) render();
}, { rootMargin: '600px' }).observe($('#sentinel'));

load();
