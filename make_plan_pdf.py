# -*- coding: utf-8 -*-
"""Рекламный план в PDF."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# IBM Plex и Oswald — те же шрифты, что в веб-версии плана.
# В системных Arial и Menlo нет символа рубля, поэтому берём эти.
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
pdfmetrics.registerFont(TTFont("Body", os.path.join(F, "PlexSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Bold", os.path.join(F, "PlexSans-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Narrow", os.path.join(F, "Oswald-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Mono", os.path.join(F, "PlexMono-Regular.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Bold")

INK = colors.HexColor("#14181f")
SOFT = colors.HexColor("#5b6472")
ACCENT = colors.HexColor("#e8442a")
LINE = colors.HexColor("#d8dce4")
LINE2 = colors.HexColor("#eaedf2")
OK = colors.HexColor("#0d7a4a")
WARN = colors.HexColor("#b7791f")

S = {
    "h1": ParagraphStyle("h1", fontName="Narrow", fontSize=30, leading=32, textColor=INK,
                         spaceAfter=8),
    "eyebrow": ParagraphStyle("eyebrow", fontName="Mono", fontSize=7.5, leading=10,
                              textColor=ACCENT, spaceAfter=8, tracking=1),
    "lede": ParagraphStyle("lede", fontName="Body", fontSize=10, leading=15, textColor=SOFT,
                           spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName="Mono", fontSize=7.5, leading=11, textColor=SOFT),
    "h2": ParagraphStyle("h2", fontName="Narrow", fontSize=14, leading=17, textColor=INK,
                         spaceBefore=0, spaceAfter=0),
    "h3": ParagraphStyle("h3", fontName="Bold", fontSize=9.5, leading=13, textColor=INK,
                         spaceBefore=10, spaceAfter=3),
    "sub": ParagraphStyle("sub", fontName="Body", fontSize=9, leading=13, textColor=SOFT,
                          spaceAfter=8),
    "p": ParagraphStyle("p", fontName="Body", fontSize=9.5, leading=14, textColor=INK,
                        spaceAfter=7),
    "li": ParagraphStyle("li", fontName="Body", fontSize=9.5, leading=13.5, textColor=INK,
                         leftIndent=12, bulletIndent=2, spaceAfter=4),
    "small": ParagraphStyle("small", fontName="Body", fontSize=8.5, leading=12, textColor=SOFT),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=9, leading=12.5, textColor=INK),
    "cellsoft": ParagraphStyle("cellsoft", fontName="Body", fontSize=9, leading=12.5, textColor=SOFT),
    "num": ParagraphStyle("num", fontName="Mono", fontSize=9, leading=12.5, textColor=INK,
                          alignment=TA_RIGHT),
    "url": ParagraphStyle("url", fontName="Mono", fontSize=7.2, leading=11, textColor=INK,
                          backColor=colors.HexColor("#f5f6f8"), borderPadding=5,
                          spaceAfter=4, spaceBefore=2),
    "note": ParagraphStyle("note", fontName="Body", fontSize=9, leading=13.5, textColor=SOFT,
                           leftIndent=10, borderColor=ACCENT, borderWidth=0,
                           spaceBefore=6, spaceAfter=10),
    "big": ParagraphStyle("big", fontName="Mono", fontSize=17, leading=20, textColor=ACCENT),
}


def h2(num, text):
    """Номер в рамке, заголовок отдельной колонкой — иначе рамка налезает на текст."""
    badge = Table([[Paragraph(num, ParagraphStyle("n", fontName="Mono", fontSize=8,
                                                  textColor=ACCENT, leading=10))]],
                  colWidths=[9 * mm], rowHeights=[6 * mm])
    badge.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    t = Table([[badge, Paragraph(text.upper(), S["h2"])]], colWidths=[14 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def table(rows, widths, aligns=None, total_row=False):
    data = []
    for i, row in enumerate(rows):
        cells = []
        for j, val in enumerate(row):
            style = "cellsoft" if i == 0 else ("num" if aligns and aligns[j] == "r" else "cell")
            if i == 0:
                style = "cellsoft"
            txt = f'<font face="Mono" size="7">{val.upper()}</font>' if i == 0 else val
            if i > 0 and aligns and aligns[j] == "r":
                cells.append(Paragraph(val, S["num"]))
            elif i > 0 and total_row and i == len(rows) - 1:
                cells.append(Paragraph(f"<b>{val}</b>", S["cell"]))
            else:
                cells.append(Paragraph(txt, S[style]))
        data.append(cells)
    t = Table(data, colWidths=widths, hAlign="LEFT")
    cmds = [
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINE2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if total_row:
        cmds.append(("LINEABOVE", (0, -1), (-1, -1), 0.9, INK))
    t.setStyle(TableStyle(cmds))
    return t


def check(items):
    data = []
    for done, title, note in items:
        # квадратик рисуем таблицей: символов □ и ■ в шрифте нет
        box = Table([[""]], colWidths=[3.4 * mm], rowHeights=[3.4 * mm])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, OK if done else LINE),
            ("BACKGROUND", (0, 0), (-1, -1), OK if done else colors.white),
        ]))
        body = [Paragraph(f"<b>{title}</b>", S["cell"]), Paragraph(note, S["small"])]
        data.append([box, body])
    t = Table(data, colWidths=[8 * mm, None], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def card(title, tag, tag_color, text):
    head = Table([[Paragraph(f"<b>{title.upper()}</b>",
                             ParagraphStyle("ct", fontName="Narrow", fontSize=11.5,
                                            leading=14, textColor=INK)),
                   Paragraph(f'<font face="Mono" size="7" color="{tag_color.hexval()}">{tag.upper()}</font>',
                             ParagraphStyle("tg", alignment=TA_RIGHT, fontName="Mono",
                                            fontSize=7, leading=12))]],
                 colWidths=[None, 30 * mm])
    head.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    inner = Table([[head], [Paragraph(text, S["cell"])]], colWidths=[None])
    inner.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return inner


OUT = os.path.expanduser("~/Desktop/Рекламный-план-ДВС-ЕКБ.pdf")
doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=16 * mm,
                        title="Рекламный план ДВС-ЕКБ",
                        author="dvigatel-ekb.ru")

st = []
st.append(Paragraph("ЗАПУСК ПЛАТНОГО ТРАФИКА · АВГУСТ 2026", S["eyebrow"]))
st.append(Paragraph("РЕКЛАМНЫЙ ПЛАН ДВС-ЕКБ", S["h1"]))
st.append(Paragraph("Два канала: реклама внутри Авито и Яндекс.Директ. Что сделать до запуска, "
                    "сколько платить за обращение, какие цифры считать и когда резать.", S["lede"]))
st.append(Paragraph("Сайт dvigatel-ekb.ru　·　Каталог 1 182 агрегата　·　Медианная маржа 23 500 ₽",
                    S["meta"]))
st.append(Spacer(1, 6))
st.append(HRFlowable(width="100%", thickness=1.2, color=INK, spaceAfter=4))

# 01
st.append(h2("01", "Экономика: сколько можно платить"))
st.append(Paragraph("Всё остальное — производные от этой цифры. Считаем от маржи, "
                    "а не от «сколько не жалко».", S["sub"]))
st.append(table([
    ["Показатель", "Значение", "Откуда"],
    ["Маржа с продажи, медиана", "23 500 ₽", "факт, из каталога"],
    ["Нижняя четверть позиций", "14 000 ₽", "факт, минимальная маржа"],
    ["Из обращений становятся сделками", "20 %", "гипотеза, проверяем"],
    ["Ценность одного обращения", "4 700 ₽", "23 500 × 0,2"],
    ["Целевая цена обращения", "≤ 1 500 ₽", "втрое ниже ценности"],
], widths=[75 * mm, 30 * mm, None], aligns=[None, "r", None], total_row=True))
st.append(Spacer(1, 8))
st.append(Paragraph("<b>Почему втрое, а не впритык.</b> Между обращением и деньгами стоят возвраты, "
                    "срывы доставки и время менеджера. Запас в три раза — это то, что отличает рекламу, "
                    "которая кормит, от рекламы, которая «вроде работает».", S["note"]))

two = Table([[card("Авито Реклама", "старт", ACCENT,
                   '<font face="Mono" size="14" color="#e8442a">110–1 500 ₽</font><br/>'
                   '<font size="8" color="#5b6472">цена обращения при клике 8–45 ₽ '
                   'и конверсии сайта 3–7 %</font>'),
              card("Яндекс.Директ", "осторожно", WARN,
                   '<font face="Mono" size="14" color="#e8442a">430–3 300 ₽</font><br/>'
                   '<font size="8" color="#5b6472">цена обращения при клике 30–100 ₽ '
                   'и той же конверсии</font>')]],
            colWidths=[82 * mm, 82 * mm], hAlign="LEFT")
two.setStyle(TableStyle([("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 6),
                         ("LEFTPADDING", (1, 0), (1, 0), 6), ("RIGHTPADDING", (1, 0), (1, 0), 0),
                         ("VALIGN", (0, 0), (-1, -1), "TOP")]))
st.append(two)
st.append(Spacer(1, 8))
st.append(Paragraph("Отсюда порядок: сначала Авито, где верхняя граница укладывается в целевые "
                    "1 500 ₽, потом Директ — и только на узких запросах, где клик дешевле сотни.", S["p"]))

# 02
st.append(h2("02", "Перед запуском"))
st.append(Paragraph("Два дня работы. Без первых трёх пунктов запускать нельзя — "
                    "деньги пойдут вслепую.", S["sub"]))
st.append(check([
    (False, "Счётчик Метрики",
     "Создать на metrika.yandex.ru, прислать номер. Цели уже написаны: звонок, MAX, "
     "Telegram, отправка формы, просмотр карточки."),
    (False, "MAX у менеджера + ваше устройство",
     "Инструкция выдана. Пока не подключено — половина обращений видна только менеджеру."),
    (False, "Перевыпустить токен бота",
     "@BotFather → /mybots → API Token → Revoke. Токен засветился на скриншоте."),
    (True, "Реквизиты ИП на сайте",
     "Заполнены. Директ проверяет продавца на модерации — без них заворачивают."),
    (True, "Посадочные страницы",
     "493 страницы под категории, марки и модели. Каждое объявление ведёт на свою, а не на главную."),
    (True, "Баннеры",
     "12 файлов в папке banners: двигатели, коробки, подбор по VIN — в четырёх форматах Авито."),
    (True, "Приём заявок",
     "Форма и Telegram-бот шлют в общую группу, видят оба. Метка источника подставляется автоматически."),
]))

# 03
st.append(h2("03", "Авито Реклама — первые две недели"))
st.append(Paragraph("Основной канал. Порог входа 5 000 ₽, аудитория уже ищет запчасти — "
                    "не надо объяснять, зачем им двигатель.", S["sub"]))
st.append(Paragraph("Три кампании", S["h3"]))
st.append(table([
    ["Баннер", "Ведёт на", "Бюджет"],
    ["609 моторов", "раздел «Двигатели»", "4 000 ₽"],
    ["467 коробок", "раздел «АКПП и вариаторы»", "4 000 ₽"],
    ["Подбор по VIN", "главная", "2 000 ₽"],
    ["Итого на тест", "", "10 000 ₽"],
], widths=[50 * mm, None, 28 * mm], aligns=[None, None, "r"], total_row=True))
st.append(Paragraph("Ссылки для кампаний", S["h3"]))
st.append(Paragraph("Скопировать целиком — метка источника долетит до заявки в Telegram:", S["p"]))
for u in ["https://dvigatel-ekb.ru/k/dvigateli.html?utm_source=avito_ads&amp;utm_campaign=dvs",
          "https://dvigatel-ekb.ru/k/akpp.html?utm_source=avito_ads&amp;utm_campaign=akpp",
          "https://dvigatel-ekb.ru/?utm_source=avito_ads&amp;utm_campaign=vin"]:
    st.append(Paragraph(u, S["url"]))
st.append(Paragraph("Настройки", S["h3"]))
for b in ["География: Екатеринбург и область — на старте. Доставка есть по всей России, "
          "но сначала проверяем на близких",
          "Ставка: ручная, начинать с нижней границы и поднимать, если показов мало",
          "Время показа: 9:00–21:00 — вне этих часов отвечать некому, а клик оплачен"]:
    st.append(Paragraph(b, S["li"], bulletText="—"))

# 04
st.append(h2("04", "Яндекс.Директ — со второй недели"))
st.append(Paragraph("Только поиск, без РСЯ. В РСЯ клики дешевле, но это люди, которые двигатель "
                    "не ищут — вы уже обожглись на дороговизне Директа, и половина причины именно в этом.",
                    S["sub"]))
st.append(Paragraph("Структура: группа на марку, а не общая свалка", S["h3"]))
st.append(table([
    ["Группа", "Примеры запросов", "Посадочная"],
    ["Двигатели Audi", "контрактный двигатель ауди, двигатель audi бу купить", "/k/dvigateli-audi.html"],
    ["АКПП Mazda", "акпп мазда бу, коробка автомат mazda контрактная", "/k/akpp-mazda.html"],
    ["Двигатели VAG", "двигатель фольксваген бу, мотор шкода контрактный", "/m/volkswagen.html"],
    ["Подбор по VIN", "подобрать двигатель по vin, какой двигатель подойдёт", "главная"],
], widths=[36 * mm, None, 42 * mm]))
st.append(Spacer(1, 6))
st.append(Paragraph("Под каждую марку страница уже существует — это и снижает цену клика: "
                    "Яндекс считает соответствие объявления и страницы, а у вас оно точное.", S["p"]))
st.append(Paragraph("Минус-слова — обязательно", S["h3"]))
st.append(Paragraph('<font face="Mono" size="8">ремонт · схема · своими руками · форум · отзывы · '
                    'бесплатно · новый · разбор авто · масло · фильтр · прокладка · сальник · '
                    'датчик · чертёж · инструкция · какой лучше</font>', S["p"]))
st.append(Paragraph("Бюджет и ограничения", S["h3"]))
for b in ["15 000 ₽ на две недели, дневной лимит 1 000 ₽",
          "Стратегия: ручное управление ставками. Автостратегии на малом бюджете разгоняют цену",
          "Регион: Екатеринбург и область; расширять только после первых сделок",
          "Отключить показы в мобильных приложениях — там много случайных кликов"]:
    st.append(Paragraph(b, S["li"], bulletText="—"))

# 05
st.append(h2("05", "Что считать"))
st.append(Paragraph("Раз в неделю, пять строк. Больше не нужно, меньше — не увидите проблему.", S["sub"]))
st.append(table([
    ["Метрика", "Где смотреть", "Норма"],
    ["Кликов", "кабинет рекламы", "—"],
    ["Цена клика", "кабинет рекламы", "до 45 / 100 ₽"],
    ["Обращений", "группа в Telegram + Метрика", "—"],
    ["Цена обращения", "расход ÷ обращения", "≤ 1 500 ₽"],
    ["Сделок", "вы сами", "от 20 %"],
], widths=[45 * mm, None, 32 * mm], aligns=[None, None, "r"]))
st.append(Spacer(1, 8))
st.append(Paragraph("<b>Главная цифра — цена обращения.</b> Клики и показы ничего не говорят: "
                    "можно получить тысячу переходов и ноль звонков. Считайте деньги за живого "
                    "человека, который написал.", S["note"]))

# 06
st.append(h2("06", "Развилки на 30-й день"))
st.append(card("Обращение дешевле 1 500 ₽", "масштабировать", OK,
               "Поднять бюджет вдвое, расширить географию на соседние области. "
               "Каталог отправляет по всей России — ограничение только в голове."))
st.append(Spacer(1, 6))
st.append(card("1 500–4 000 ₽", "чинить", WARN,
               "Канал жив, но течёт. Резать неэффективные группы, менять баннеры, "
               "смотреть в Метрике, с каких страниц уходят без обращения."))
st.append(Spacer(1, 6))
st.append(card("Дороже 4 000 ₽", "выключать", SOFT,
               "Канал не окупается даже теоретически. Выключить, деньги перевести "
               "во второй канал и не возвращаться месяца три."))
st.append(Spacer(1, 8))
st.append(Paragraph("Отдельная развилка — если обращений много, а сделок нет. Тогда проблема "
                    "не в рекламе, а в цене, наличии или скорости ответа. Реклама тут ни при чём, "
                    "и добавлять бюджет бессмысленно.", S["p"]))

# 07
st.append(h2("07", "Чего опасаться"))
for b in ["<b>Модерация Директа.</b> Продажа б/у агрегатов проходит, но могут запросить документы ИП. "
          "Реквизиты на сайте уже есть — это половина дела",
          "<b>Скорость ответа.</b> Оплаченный клик живёт минут пятнадцать: человек пишет троим сразу "
          "и покупает у того, кто ответил первым",
          "<b>Наличие.</b> Каталог обновляется вручную из прайса. Если рекламировать позицию, "
          "которая уже продана, деньги за клик потрачены на разочарование",
          "<b>Соблазн включить всё сразу.</b> Два канала одновременно — и через месяц непонятно, "
          "что сработало. Поэтому Авито первым, Директ через неделю"]:
    st.append(Paragraph(b, S["li"], bulletText="—"))

st.append(Spacer(1, 14))
st.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=8))
st.append(Paragraph("План на 25 000 ₽ и месяц теста. При целевой цене обращения это примерно "
                    "<b>16 обращений и 3 сделки</b> — около 70 000 ₽ маржи. "
                    "Цифры конверсий — гипотезы, факт будет виден на второй неделе.", S["small"]))

doc.build(st)
print("готово:", OUT)
print("страниц:", len(__import__("subprocess").run(
    ["mdls", "-name", "kMDItemNumberOfPages", OUT], capture_output=True, text=True).stdout.strip()) and
    __import__("subprocess").run(["mdls", "-name", "kMDItemNumberOfPages", OUT],
                                 capture_output=True, text=True).stdout.strip())
