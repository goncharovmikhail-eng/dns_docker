#!/bin/bash
set -e

# Устанавливаем права на папки
chown -R named:named /var/named
chmod -R 777 /var/named
chmod -R 777 /var/named/zones

echo "🚀 Запуск named..."
exec su -s /bin/bash named -c "/usr/sbin/named -g -c /etc/named.conf"
