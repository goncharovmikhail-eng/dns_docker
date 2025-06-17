.PHONY: all clean build git

all:
	@echo "[1] Генерация конфигураций..."
	python3 gen_in_yml.py
	python3 render_zones.py
	python3 generate_named_conf.py

	@echo "[2] Сборка и запуск контейнеров..."
	docker compose build
	docker compose up -d

	@echo "[3] Создание git-ветки и коммит..."
	@if git rev-parse --verify develop >/dev/null 2>&1; then \
		echo "Ветка 'develop' уже существует. Переключаемся..."; \
		git switch develop; \
	else \
		echo "Создаём ветку 'develop'..."; \
		git switch -c develop; \
	fi
	git add .
	git commit -m "add dns zone"
	git push -u origin develop

clean:
	rm -rf zones/*/
build:
	@echo "[1] Генерация конфигураций..."
	python3 gen_in_yml.py
	python3 render_zones.py
	python3 generate_named_conf.py

	@echo "[2] Сборка и запуск контейнеров..."
	docker compose down 2>/dev/null || true
	docker compose build
	docker compose up -d
git:
	@echo "[3] Создание git-ветки и коммит..."
	@if git rev-parse --verify develop >/dev/null 2>&1; then \
		echo "Ветка 'develop' уже существует. Переключаемся..."; \
		git switch develop; \
	else \
		echo "Создаём ветку 'develop'..."; \
		git switch -c develop; \
	fi
	git add .
	git commit -m "add dns zone"
	git push -u origin develop
