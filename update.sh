#!/bin/bash
# Обновление каталога: положите свежие прайсы .xls в папку prices/ (старые удалите) и запустите ./update.sh
cd "$(dirname "$0")" || exit 1
./venv/bin/python build.py
