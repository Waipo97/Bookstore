# Bookstore

Coursework: a bookstore with a **Django + Django REST Framework** backend and a **Vue 3** frontend.

## Models (5, with foreign keys)

| Model | Fields | Relations |
|-------|--------|-----------|
| `Genre` | name, description | – |
| `Author` | name, country, birth_year, **photo** | – |
| `Book` | title, price, pages, published_year, in_stock, **cover** | FK → `Author`, FK → `Genre` |
| `BookPhoto` | image, caption (the photo album of a book) | FK → `Book` |
| `Order` | customer_name, quantity, status, created_at | FK → `Book` |

Every model also has a `user` foreign key – the user who created the row.

## What is implemented

* Admin panel for all models (`/admin/`).
* DRF `ModelViewSet` + serializer for every model, registered in `books/urls.py` (`/api/...`).
* Images on `Author` (photo), `Book` (cover) and `BookPhoto`; upload and change from the front end,
  click a picture to open it in a modal window; photo album for every book.
* Data is linked to the user who created it; users see only their own data,
  superusers see everything and have a **user filter**.
* `generate_data` management command (Faker) – 1000+ rows in the main tables.
* `stats` action on every viewset (aggregate queries), shown above every table.
* Filters for every column (django-filter) and sorting, pagination.
* Login / register page, Pinia store with the current user.
* `export` action on every viewset: the Excel (`.xlsx`) file is built on the backend and downloaded by the front end.
* Button that opens the admin panel from the front end.
* pytest tests for all CRUD operations of all viewsets.

## API

| URL | |
|-----|---|
| `/api/genres/`, `/api/authors/`, `/api/books/`, `/api/book-photos/`, `/api/orders/` | list / create / retrieve / update / delete |
| `/api/<model>/stats/` | statistics (respects the active filters) |
| `/api/<model>/export/` | Excel export (respects the active filters) |
| `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/register/`, `/api/auth/me/` | authorisation |
| `/api/users/` | user list (superusers only) |

## Run it

Backend:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py generate_data   # optional: 1000+ random records for your superuser
python manage.py runserver       # http://localhost:8000
```

Frontend (second terminal; Node.js 22+):

```bash
cd client
npm install
npm run dev                      # http://localhost:5173
```

Vite proxies `/api`, `/media`, `/admin` and `/static` to Django, so start both servers.
Open http://localhost:5173 and sign in with the superuser you created (or register a new user).

`generate_data` options: `--user <username>`, `--authors`, `--books`, `--orders`, `--photos`, `--covers`.

## Tests

```bash
pytest
```
