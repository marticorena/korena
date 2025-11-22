# Korena EDU — Installation & Setup

---

## 1. Requirements

- Python 3.12+
- Docker + Docker Compose
- PostgreSQL
- Redis
- Git
- pip and pip-tools

---

## 2. Clone the repository

```bash
git clone https://github.com/korena/korena-edu.git
```
---

## 4. Environment variables

Create the `.env` file and update the values:

```bash
cp env.example .env
```

---

## 5. Install dependencies

```bash
pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt
```

---

## 6. Database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 7. Create superuser

```bash
python manage.py createsuperuser
```

---

## 8. Run local server

```bash
python manage.py runserver
```

---

## 9. Celery workers

Start worker:

```bash
celery -A config worker -l info
```

Start beat (scheduled tasks):

```bash
celery -A config beat -l info
```

---

## 10. Run with Docker

```bash
docker-compose up -d --build
```

Check logs:

```bash
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis
```

---

## 11. Run migrations inside Docker

```bash
docker-compose exec web python manage.py migrate
```

---

## 12. Pre-commit hooks

Install hooks:

```bash
pre-commit install
```

Run hooks:

```bash
pre-commit run --all-files
```

---

## 13. Main endpoints

```
/admin/          → Django admin (internal)
/graphql/        → GraphQL API
/api/            → File uploads (REST)
/health/        → Liveness probe
/ready/         → Readiness probe
```

---

## 14. Tests

```bash
pytest
```

---

## 15. Production deployment (summary)

Deployment is performed via CI/CD using GitHub Actions and environment-specific `.env` files.
