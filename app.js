'use strict';
const S = window.SHOP || {};
const PAGE = 60;
let DB = null, view = [], shown = 0;

const $ = s => document.querySelector(s);
const els = {
  q: $('#q'), grid: $('#grid'), status: $('#status'), more: $('#more'),
  brand: $('#fBrand'), cat: $('#fCat'),
  min: $('#fMin'), max: $('#fMax'), sort: $('#fSort'), photo: $('#fPhoto'), km: $('#fKm'),
  filters: $('#filters')
};

const money = n => n ? n.toLocaleString('ru-RU') + ' ₽' : 'цена по запросу';
const plural = (n, one, few, many) => {
  const a = Math.abs(n) % 100, b = a % 10;
  return a > 10 && a < 20 ? many : b > 1 && b < 5 ? few : b === 1 ? one : many;
};
const photoUrl = (it, n, size = 'big') => DB.photoBase[size] + it.ph + '_' + n + '.jpg';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : '';
const catLabel = n => (DB.catLabels && DB.catLabels[n]) || cap(n);
const carLine = it => [it.b, it.m, it.k, it.e].filter(Boolean).join(' ');
const alnum = s => s.toLowerCase().replace(/[^a-zа-я0-9]/gi, '');

// ─── контакты ───
function contacts() {
  // заголовок задан в HTML и важен для поисковиков — не трогаем
  $('#headPhone').textContent = S.phone || '';
  $('#headPhone').href = 'tel:' + (S.phoneTel || '');
  $('.logo-text').textContent = S.name || 'Запчасти';
  if (S.tagline) $('#heroSub').textContent = S.tagline;

  const max = S.max ? 'https://max.ru/' + S.max : '';
  const call = $('#helpCall');
  if (call) { call.href = 'tel:' + (S.phoneTel || ''); call.textContent = 'Позвонить ' + (S.phone || ''); }
  const hmax = $('#helpMax');
  if (hmax) {
    if (max) hmax.href = max;
    else hmax.remove();
  }
  [['#headMax', max]].forEach(([sel, href]) => {
    const el = $(sel);
    if (href) el.href = href; else el.remove();
  });

  $('#footContacts').innerHTML =
    `<b>${esc(S.name)}</b>${S.city ? ' · ' + esc(S.city) : ''} · ` +
    `<a href="tel:${esc(S.phoneTel)}">${esc(S.phone)}</a>`;
  // дату обновления каталога не показываем: прайс обновляется не каждый день,
  // а старая дата на витрине читается как «наличие неактуально»
  $('#footHours').textContent = S.hours || '';

  // реквизиты продавца — требование закона о защите прав потребителей
  const L = window.LEGAL || {};
  $('#footLegal').textContent = [L.entity, L.inn && 'ИНН ' + L.inn,
    L.ogrn && 'ОГРН ' + L.ogrn, L.address].filter(Boolean).join(' · ');

  // уведомление о cookie — показываем один раз
  const box = $('#cookie');
  if (box && !localStorage.getItem('cookieOk')) {
    box.classList.add('show');
    $('#cookieOk').onclick = () => {
      localStorage.setItem('cookieOk', '1');
      box.classList.remove('show');
    };
  }
}

// ─── карусель преимуществ ───
const ICONS = {
  shield: '<path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Zm-1 14-4-4 1.4-1.4L11 13.2l4.6-4.6L17 10l-6 6Z"/>',
  truck:  '<path d="M3 6h11v9H3V6Zm12 3h3.5l2.5 3v3h-6V9ZM6.5 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm11 0a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/>',
  gauge:  '<path d="M12 4a9 9 0 0 0-7.7 13.7l1.7-1A7 7 0 1 1 18 16.7l1.7 1A9 9 0 0 0 12 4Zm3.5 4.5-4.6 3.1a1.6 1.6 0 0 0 1.8 2.6l3.5-4.3a.6.6 0 0 0-.7-1.4Z"/>',
  video:  '<path d="M4 6h11v12H4V6Zm13 4 4-2.5v9L17 14v-4Z"/>',
  doc:    '<path d="M6 2h8l4 4v16H6V2Zm7 1.5V7h3.5L13 3.5ZM8 11h8v2H8v-2Zm0 4h8v2H8v-2Z"/>',
  vin:    '<path d="M3 5h18v4H3V5Zm0 6h18v8H3v-8Zm2 2v4h3v-4H5Zm5 0v4h9v-4h-9Z"/>',
  swap:   '<path d="M7 4 3 8l4 4V9h10V7H7V4Zm10 16 4-4-4-4v3H7v2h10v3Z"/>',
  ruble:  '<path d="M8 4h5a4.5 4.5 0 0 1 0 9h-3v2h5v2h-5v3H8v-3H6v-2h2v-2H6v-2h2V4Zm2 2v5h3a2.5 2.5 0 0 0 0-5h-3Z"/>'
};

function benefits() {
  const list = window.BENEFITS || [];
  const track = $('#beneTrack'), dots = $('#beneDots');
  if (!list.length || !track) return;

  track.innerHTML = list.map(b => `
    <div class="bene-item">
      <div class="bene-ico">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">${ICONS[b.icon] || ICONS.shield}</svg>
      </div>
      <div>
        <div class="bene-t">${esc(b.title)}</div>
        <div class="bene-x">${esc(b.text)}</div>
      </div>
    </div>`).join('');

  // листаем ровно по экрану, чтобы слайды всегда стояли по краю, а точки совпадали.
  // ширину берём с запасом: в скрытой или ещё не разложенной вкладке она равна нулю
  const pages = () => {
    const w = track.clientWidth;
    if (!w) return 1;
    return Math.min(list.length, Math.max(1, Math.round(track.scrollWidth / w)));
  };

  let marks = [];
  function drawDots() {
    const n = pages();
    if (marks.length === n) return;
    dots.innerHTML = Array.from({ length: n }, (_, i) =>
      `<button type="button" aria-label="Слайд ${i + 1}"${i ? '' : ' class="on"'}></button>`).join('');
    marks = [...dots.children];
    marks.forEach((d, i) => d.onclick = () => {
      stop();
      track.scrollTo({ left: i * track.clientWidth });
    });
  }
  drawDots();
  // ширина меняется при повороте телефона и когда вкладка наконец показалась
  if (window.ResizeObserver) new ResizeObserver(drawDots).observe(track);
  else window.addEventListener('resize', drawDots);

  track.addEventListener('scroll', () => {
    const w = track.clientWidth;
    if (!w) return;
    const i = Math.round(track.scrollLeft / w);
    marks.forEach((d, k) => d.classList.toggle('on', k === i));
  }, { passive: true });

  // автопрокрутка, пока пользователь не тронул карусель
  let timer = setInterval(() => {
    const end = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
    track.scrollTo({ left: end ? 0 : track.scrollLeft + track.clientWidth });
  }, 4500);
  function stop() { clearInterval(timer); timer = null; }
  ['pointerdown', 'wheel', 'touchstart'].forEach(e =>
    track.addEventListener(e, stop, { once: true, passive: true }));
  track.addEventListener('mouseenter', stop, { once: true });
}

// ─── цифры в шапке ───
function heroStats() {
  const withKm = DB.items.filter(i => i.km);
  const avg = withKm.length
    ? Math.round(withKm.reduce((s, i) => s + i.km, 0) / withKm.length) : 0;
  const stats = [
    [DB.count.toLocaleString('ru-RU'), 'агрегатов в наличии'],
    [DB.brands.length, 'марок автомобилей'],
    [avg ? avg + ' 000 км' : '—', 'средний пробег'],
    [(DB.cats.find(c => c[0] === 'двс') || [0, 0])[1], 'двигателей']
  ];
  $('#heroStats').innerHTML = stats.map(([n, s]) =>
    `<div class="stat"><b>${n}</b><span>${s}</span></div>`).join('');
}

// ─── загрузка ───
async function load() {
  contacts();
  benefits();
  try {
    const r = await fetch('data/parts.json');
    DB = await r.json();
  } catch (e) {
    els.status.textContent = 'Не удалось загрузить каталог. Обновите страницу.';
    return;
  }
  DB.items.forEach(it => {
    it._h = [it.n, it.x, it.a, it.b, (it.bs || []).join(' '), it.m, (it.ms || []).join(' '),
      it.k, it.e, it.d, it.o, it.t, it.y].join(' ').toLowerCase();
    it._a = alnum(it.d + ' ' + it.o + ' ' + it.a);
  });
  heroStats();
  sectionCounts();
  fill(els.brand, DB.brands);
  brandLinks();
  fill(els.cat, DB.cats.map(([n, c]) => [catLabel(n), c]), DB.cats.map(([n]) => n));
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

// количество агрегатов в кнопках разделов
function sectionCounts() {
  const counts = Object.fromEntries(DB.cats);
  document.querySelectorAll('.sc-count[data-cat]').forEach(el => {
    const n = counts[el.dataset.cat] || 0;
    el.textContent = n + ' ' + plural(n, 'агрегат', 'агрегата', 'агрегатов');
  });
}

// ссылки на страницы марок — путь робота вглубь каталога
function brandLinks() {
  const box = $('#brandLinks');
  if (!box) return;
  const slug = b => b.toLowerCase().replace(/[\/ ]+/g, '-')
    .replace(/[^a-z0-9-]/g, '').replace(/-{2,}/g, '-').replace(/^-|-$/g, '');
  box.innerHTML = '<div class="tiles">' + DB.brands
    .filter(([, c]) => c >= 3)
    .map(([b, c]) => `<a class="tile" href="m/${slug(b)}.html">
      <span class="tile-n">${esc(b.charAt(0) + b.slice(1).toLowerCase())}</span>
      <span class="tile-c">${c}</span></a>`)
    .join('') + '</div>';
}

// ─── фильтрация ───
function apply(push = true) {
  const terms = els.q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const aq = alnum(els.q.value);
  const b = els.brand.value, c = els.cat.value;
  const mn = +els.min.value || 0, mx = +els.max.value || Infinity;
  const onlyPhoto = els.photo.checked, onlyKm = els.km.checked;

  view = DB.items.filter(it => {
    if (b && !(it.bs || [it.b]).includes(b)) return false;
    if (c && it.n !== c) return false;
    if (it.p < mn || it.p > mx) return false;
    if (onlyPhoto && !it.f) return false;
    if (onlyKm && !(it.km && it.km <= 100)) return false;
    if (!terms.length) return true;
    // запрос целиком похож на номер детали — ищем по номерам без разделителей
    if (aq.length >= 5 && it._a.includes(aq)) return true;
    return terms.every(t => it._h.includes(t));
  });

  const s = els.sort.value;
  if (s === 'asc') view.sort((x, y) => (x.p || 1e9) - (y.p || 1e9));
  else if (s === 'desc') view.sort((x, y) => (y.p || 0) - (x.p || 0));
  else if (s === 'km') view.sort((x, y) => (x.km || 1e6) - (y.km || 1e6));

  els.status.textContent = view.length
    ? `Найдено ${view.length.toLocaleString('ru-RU')} ${plural(view.length, 'позиция', 'позиции', 'позиций')} из ${DB.count.toLocaleString('ru-RU')}`
    : 'Ничего не нашли. Попробуйте короче: марка и модель двигателя — «мазда lf-ve».';
  els.grid.innerHTML = '';
  shown = 0;
  render();
  if (push) writeUrl();
}

const kmText = km => (km * 1000).toLocaleString('ru-RU') + ' км';
// характеристики — это хвост описания после тире
const details = it => (it.t || '').split(' — ')[1]?.replace(/\.$/, '') || carLine(it);
function tags(it) {
  const list = [];
  if (it.kind) list.push(`<span class="tag">${esc(it.kind)}</span>`);
  if (it.km) list.push(`<span class="tag km">${kmText(it.km)}</span>`);
  return list.length ? `<div class="tags">${list.join('')}</div>` : '';
}

function render() {
  const part = view.slice(shown, shown + PAGE);
  const html = part.map(it => `
    <a class="card" href="${it.u}">
      <div class="thumb">${tags(it)}${it.f
        ? `<img loading="lazy" src="${photoUrl(it, 1, 'thumb')}" alt="${esc(it.n)} ${esc(carLine(it))}"
             onerror="this.parentNode.innerHTML='<span class=nophoto>без фото</span>'">`
        : '<span class="nophoto">без фото</span>'}</div>
      <div class="card-b">
        <div class="card-title">${esc(it.ti || cap(it.n))}</div>
        <div class="card-car">${esc(details(it))}</div>
        <div class="card-price">${money(it.p)}</div>
      </div>
    </a>`).join('');
  els.grid.insertAdjacentHTML('beforeend', html);
  shown += part.length;
  els.more.hidden = shown >= view.length;
}

// ─── состояние в адресе страницы ───
function writeUrl() {
  const p = new URLSearchParams();
  const add = (k, v) => v && p.set(k, v);
  add('q', els.q.value.trim());
  add('b', els.brand.value); add('c', els.cat.value);
  add('min', els.min.value); add('max', els.max.value);
  if (els.photo.checked) p.set('ph', '1');
  if (els.km.checked) p.set('km', '1');
  if (els.sort.value !== 'rel') p.set('s', els.sort.value);
  history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
}
function readUrl() {
  const p = new URLSearchParams(location.search);
  els.q.value = p.get('q') || '';
  els.brand.value = p.get('b') || ''; els.cat.value = p.get('c') || '';
  els.min.value = p.get('min') || ''; els.max.value = p.get('max') || '';
  els.photo.checked = p.get('ph') === '1'; els.km.checked = p.get('km') === '1';
  els.sort.value = p.get('s') || 'rel';
  if ([...p.keys()].some(k => k !== 'q')) els.filters.classList.add('open');
}

// ─── события ───
let t;
els.q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(apply, 200); });
['change'].forEach(ev => [els.brand, els.cat, els.sort, els.photo, els.km]
  .forEach(el => el.addEventListener(ev, () => apply())));
[els.min, els.max].forEach(el => el.addEventListener('input', () => { clearTimeout(t); t = setTimeout(apply, 350); }));
$('#filtersBtn').onclick = () => els.filters.classList.toggle('open');
$('#reset').onclick = () => {
  els.q.value = ''; els.brand.value = ''; els.cat.value = '';
  els.min.value = ''; els.max.value = ''; els.photo.checked = false;
  els.km.checked = false; els.sort.value = 'rel';
  apply();
};
els.more.onclick = render;
new IntersectionObserver(en => {
  if (en[0].isIntersecting && DB && shown < view.length) render();
}, { rootMargin: '600px' }).observe($('#sentinel'));

load();
