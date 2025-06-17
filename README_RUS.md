# DNS станция

В данном проекте dns-сервер представляет собой черный ящик. Взаимодействие с которым происходит через python скрипты.
gen_in_yml.py добавляет новую зону в zones/zones.yml
zones/zones.yml можно добавлять и руками в том числе.
На основе zones/zones.yml работает render_zones.py. Он генерирует конфиги на основе tempates/*.j2
На основе сгенирированных конфигов зоны подключаются к корневому named.conf.

## Требования:
  - Docker version 25.0.7
  - Docker Compose version v2.27.1 
  - Python от 3.8.20

DNS сервер запускается в docker контейнере на базе fedora. 

## Используйте make для комфортного испозования:

```bash 
make all``` 
###  Описание:
1. Добавление зоны в zones.yml
2. Рендер конфигов
3. Обновление named.conf
4. docker compose down если было up
5. Сборка
6. docker compose up -d 
7. Пуш изменений в ветку develop. Если ее нет, она создастся.

```bash
make all```

```bash
make clean```
### Описание
- Удаляет все сгенированные конфиги в zones/* не трогая файл zones/zones.yml
