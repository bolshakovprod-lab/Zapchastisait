#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Обновление каталога целиком: прайс -> каталог -> фото -> сайт
#
#  Как пользоваться:
#   1. Положите свежий прайс .xls в папку prices/ (старый удалите)
#   2. Запустите:  ./update.sh
#   3. Дождитесь конца — сайт обновится сам
# ─────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")" || exit 1
PY=./venv/bin/python

echo "1/5  Собираю каталог из прайса"
$PY build.py

echo
echo "2/5  Качаю фото новых позиций (уже скачанные пропускаются)"
$PY download_photos.py

echo
echo "3/5  Обрабатываю фото: обрезка, поворот, водяной знак, два размера"
$PY process_photos.py

echo
echo "4/5  Пересобираю страницы для поисковиков"
$PY seo_build.py

echo
echo "5/5  Заливаю на GitHub"
git add -A
if git diff --cached --quiet; then
  echo "     изменений нет"
else
  git -c user.name="Andrey" -c user.email="andrej.bolschakov2014@gmail.com" \
      commit -q -m "Обновление наличия $(date +%d.%m.%Y)"
  $PY push_photos.py 2>/dev/null || git push
  git push
fi

echo
echo "Готово. Сайт: https://dvigatel-ekb.ru/"
