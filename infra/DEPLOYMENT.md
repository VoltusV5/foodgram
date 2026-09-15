# Foodgram: сервер и CI/CD

Сайт: https://foodgram.srv-node.com/
Сервер: `ssh -p 22222 admin@srv-node.com` из Ubuntu WSL.
Каталог: `/opt/foodgram`. Compose-проект: `foodgram`.
Gateway: `127.0.0.1:8080`; PostgreSQL не публикует порт наружу.

## GitHub Actions

В репозитории откройте Settings → Secrets and variables → Actions → New repository secret.

- `HOST`: `srv-node.com`
- `USER`: `admin`
- `SSH_PORT`: `22222`
- `SSH_HOST_FINGERPRINT`: `SHA256:Yd94qghKV0QZeV0/lewPM2ee8dl4v9rkOhPAtg2sA5U`
- `SSH_KEY`: содержимое приватного ключа `/home/user/.ssh/id_ed25519` из Ubuntu WSL, включая строки BEGIN/END. Это уже авторизованный ключ. Не добавляйте его в репозиторий и не отправляйте в чат. Отдельный ключ CI/CD не создавался.
- `DOCKER_USERNAME`: ваш логин Docker Hub (нижний регистр).
- `DOCKER_PASSWORD`: Docker Hub access token с правом Read & Write.

Чтобы скопировать SSH_KEY в буфер обмена Windows, выполните в Ubuntu WSL:

```bash
cat ~/.ssh/id_ed25519 | clip.exe
```

Создайте в Docker Hub три PUBLIC-репозитория: `foodgram_backend`, `foodgram_frontend`, `foodgram_gateway`.
Сервер скачивает публичные образы без docker login. Для приватных репозиториев понадобится отдельно настроить на сервере docker login с read-only токеном; workflow этого не делает.

Workflow `.github/workflows/main.yml` хранится в ветке `main`. Первый инфраструктурный коммит помечен `[skip ci]`, чтобы не запускать деплой до настройки секретов. После настройки секретов сделайте push в `main` либо Actions → Foodgram CI/CD → Run workflow → main.

Pull request запускает только проверки. Push в main / ручной запуск main: проверки → сборка трёх образов на GitHub → публикация с тегом SHA коммита → загрузка Compose и скриптов → резервная копия → миграции → статика → обновление Foodgram → проверка HTTPS API.

Telegram-секреты больше не требуются. Секреты Django и PostgreSQL остаются в `/opt/foodgram/.env` с правами 600, workflow их не перезаписывает. Для первого ручного запуска образы передаются с компьютера по SSH; при первом CI-деплое namespace и tag автоматически переключаются на Docker Hub.

## Управление на сервере

```bash
cd /opt/foodgram
docker compose -p foodgram --env-file .env --env-file .release.env -f docker-compose.production.yml ps
docker compose -p foodgram --env-file .env --env-file .release.env -f docker-compose.production.yml logs --tail 100 backend gateway
```

Вход в админку: https://foodgram.srv-node.com/admin/ ; email `admin@foodgram.srv-node.com`. Загружены 13 демонстрационных рецептов из проекта, теги и ингредиенты.

Пароль администратора хранится в `.env` как ADMIN_PASSWORD. Посмотреть его можно самостоятельно в SSH-сессии; в репозиторий и вывод агента он не попадает.

## Резервные копии

Перед миграциями deploy.sh сохраняет PostgreSQL и media в `/opt/foodgram/backups`. Таймер `foodgram-backup.timer` запускается ежедневно около 05:15 по Москве. Ежедневный backup.sh использует ту же блокировку, чтобы не пересекаться с деплоем. Локальные копии хранятся 14 дней. Они защищают от ошибок обновления, но для защиты от потери сервера нужна внешняя копия. База и media снимаются последовательно, без остановки записи: это не единый атомарный снимок.

Снимок исходной конфигурации Nginx: `/opt/foodgram/backups/nginx-before-foodgram.tar.gz`.

## Откат

При неудачном деплое скрипт сообщает об ошибке и сохраняет бэкап. Автоматического отката схемы базы нет. Если миграции совместимы со старым кодом, используйте `bash /opt/foodgram/deploy.sh DOCKER_USERNAME PREVIOUS_COMMIT_SHA`. Для первого локального выпуска: `bash /opt/foodgram/deploy.sh local deploy-20260915 --loaded`.

Если схема несовместима, сначала остановите только backend/gateway Foodgram, сохраните текущее состояние и восстановите согласованные версии базы/media/образов из нужного бэкапа. Это может потерять записи после момента бэкапа; восстановление не запускается автоматически.

Чтобы убрать сайт из Nginx, отключите только ссылку `/etc/nginx/sites-enabled/foodgram.conf`, затем `sudo nginx -t && sudo systemctl reload nginx`. Остальные конфиги не менять. Для остановки Foodgram использовать только `docker compose -p foodgram ... stop` с указанными выше env-file и compose-файлом. Не применять глобальные docker prune и не удалять тома.
