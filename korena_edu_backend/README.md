# Korena EDU — Installation & Setup

---

## 1. Requirements

- Docker + Docker Compose

---

## 2. Clone the repository

```bash
  git clone https://github.com/korena/korena-edu.git
```
---

## 3. Environment variables

Create the `.env` file and update the values:

```bash
  cp env.example .env
```
---

## 4. Run with Docker

```bash
  docker-compose up -d --build
```

---

## 5. Run commands inside Docker

```bash
  docker-compose exec django-app python manage.py createsuperuser
```

```bash
  docker-compose exec django-app python manage.py makemigrations
```

```bash
  docker-compose exec django-app python manage.py migrate
```
```bash
  docker-compose exec django-app python manage.py collectstatic --noinput
```

---

## 6. How to code

Create and configure a localhost virtualenv
.
```bash
  pip install pip-tools
```

```bash
  pip-compile requirements.in
```

```bash
  pip install -r requirements.txt
```

Install pre-commit hooks:

```bash
  pre-commit install
```

---

## 7. Tests

```bash
  docker compose exec django-app pytest
```
```bash
  docker compose exec django-app pytest --cov=. --cov-report=html
```

---

## 8. Helpers

Clean migrations:

```bash
  Get-ChildItem -Path .\apps -Recurse -Filter "*.py" | Where-Object { $_.Directory.Name -eq "migrations" -and $_.Name -ne "__init__.py" } | Remove-Item -Force
```
```bash
  docker compose exec postgres psql -U korena -d postgres -v ON_ERROR_STOP=1 -c "\set AUTOCOMMIT on" -c "REVOKE CONNECT ON DATABASE korena FROM public;" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='korena' AND pid <> pg_backend_pid();" -c "DROP DATABASE IF EXISTS korena;"
```
```bash
  docker compose exec postgres psql -U korena -d postgres -c "CREATE DATABASE korena;"
```

---

## 9. Production deployment (summary)

Deployment is performed via CI/CD using GitHub Actions and environment-specific `.env` files.
