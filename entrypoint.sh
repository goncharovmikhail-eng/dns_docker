#!/bin/bash
set -e

# Путь к папке с зонами и конфигами
ZONES_DIR="/var/named/zones"
ZONES_YML="${ZONES_DIR}/zones.yml"

# Логи
LOG_DIR="/var/named/logs"
mkdir -p "$LOG_DIR"

echo "🔄 Генерация DNS зон из zones.yml..."
python3 /app/render_zones.py

echo "🔄 Генерация основного named.conf..."
python3 /app/generate_named_conf.py > /etc/named.conf

echo "🧹 Проверяем права на /var/named и логи..."
chown -R named:named /var/named
chmod -R 755 /var/named

echo "🚀 Запускаем named..."
exec /usr/sbin/named -g -c /etc/named.conf
