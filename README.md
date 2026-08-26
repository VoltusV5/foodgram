# Foodgram

Foodgram — это сервис для публикации кулинарных рецептов.
Пользователь может найти блюда по тегам и ингредиентам, поделиться собственным
рецептом, подписаться на интересных авторов и сформировать список
необходимых продуктов.

## Возможности

- регистрация, токен-аутентификация и управление профилем;
- публикация, редактирование и удаление рецептов;
- загрузка изображений рецептов и аватаров;
- фильтрация рецептов по тегам, автору, избранному и списку покупок;
- поиск ингредиентов по началу названия;
- подписки на авторов и персональная лента;
- добавление рецептов в избранное и список покупок;
- скачивание общего списка ингредиентов;
- генерация коротких ссылок на рецепты;
- интерактивная документация REST API.


## Технологии

- **Backend:** Python 3.13, Django, Django REST Framework, Djoser,
  django-filter, Gunicorn, PostgreSQL.
- **Инфраструктура:** Docker, Docker Compose, Nginx, GitHub Actions,
  Docker Hub.

## Структура проекта

```text
backend/    Django-приложение и REST API
frontend/   React-приложение
infra/      Docker Compose, Nginx
data/       ингредиенты, тестовые данные и изображения
docs/       документация и OpenAPI-схема
```

## Локальный запуск

Для запуска потребуются Git, Docker и Docker Compose.

1. Клонируйте репозиторий и перейдите в каталог проекта:

   ```bash
   git clone https://github.com/VoltusV5/foodgram.git
   cd foodgram
   ```

2. Создайте файл переменных окружения:

   ```bash
   cp infra/.env.example infra/.env
   ```

   Замените демонстрационные значения в `infra/.env`. В частности, задайте
   собственные `SECRET_KEY`, `POSTGRES_PASSWORD`, `ADMIN_PASSWORD` и
   `TEST_USER_PASSWORD`.

3. Соберите Docker-образы:

   ```bash
   docker compose -f infra/docker-compose.yml build
   ```

4. Примените миграции и соберите статику:

   ```bash
   docker compose -f infra/docker-compose.yml run --rm backend python manage.py migrate
   docker compose -f infra/docker-compose.yml run --rm backend python manage.py collectstatic --noinput
   ```

5. Запустите приложение:

   ```bash
   docker compose -f infra/docker-compose.yml up -d
   ```

После запуска доступны:

- приложение — <http://localhost/>;
- REST API — <http://localhost/api/>;
- документация API — <http://localhost/api/docs/>;
- административная панель — <http://localhost/admin/>.

Для наполнения базы демонстрационными данными выполните:

```bash
docker compose -f infra/docker-compose.yml exec backend python manage.py setup_test_data
```

Команда создаёт тестовых пользователей, теги и рецепты, а также импортирует
ингредиенты и изображения из каталога `data/`.

Остановить контейнеры:

```bash
docker compose -f infra/docker-compose.yml down
```

## Примеры запросов

### Получить список рецептов

**GET** `/api/recipes/`

**Пример ответа:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tags": [
        {
          "id": 1,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "chef@example.com",
        "id": 1,
        "username": "chef",
        "first_name": "Максим",
        "last_name": "Терещенко",
        "is_subscribed": false,
        "avatar": null
      },
      "ingredients": [
        {
          "id": 1,
          "name": "Картофель",
          "measurement_unit": "г",
          "amount": 500
        }
      ],
      "is_favorited": false,
      "is_in_shopping_cart": false,
      "name": "Картофельная запеканка",
      "image": "http://localhost/media/recipes_icons/casserole.jpg",
      "text": "Домашняя картофельная запеканка.",
      "cooking_time": 45
    }
  ]
}
```

### Создать рецепт

**POST** `/api/recipes/`

Требуется заголовок `Authorization: Token <ваш_токен>`.

**Тело запроса:**

```json
{
  "ingredients": [
    {
      "id": 1,
      "amount": 500
    },
    {
      "id": 2,
      "amount": 200
    }
  ],
  "tags": [1],
  "image": "data:image/png;base64,iVBORw0KGgo...",
  "name": "Картофельная запеканка",
  "text": "Домашняя картофельная запеканка.",
  "cooking_time": 45
}
```

### Зарегистрировать пользователя

**POST** `/api/users/`

**Тело запроса:**

```json
{
  "email": "user@example.com",
  "username": "user",
  "first_name": "Максим",
  "last_name": "Терещенко",
  "password": "StrongPassword123"
}
```

### Добавить рецепт в избранное

**POST** `/api/recipes/1/favorite/`

Требуется заголовок `Authorization: Token <ваш_токен>`.

**Пример ответа:**

```json
{
  "id": 1,
  "name": "Картофельная запеканка",
  "image": "http://localhost/media/recipes_icons/casserole.jpg",
  "cooking_time": 45
}
```

## CI/CD

Workflow GitHub Actions запускается при push и pull request:

1. проверяет Python-код с помощью Flake8;
2. собирает образы backend, frontend и gateway;
3. публикует образы в Docker Hub;
4. копирует production Compose на сервер;
5. применяет миграции, собирает статику и обновляет контейнеры;
6. отправляет уведомление об успешном деплое в Telegram.

## Автор

**[Терещенко Максим Андреевич](https://github.com/voltusv5)**

Студент курса Python-разработчик Яндекс Практикума.
