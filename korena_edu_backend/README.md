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
  docker-compose exec web python manage.py createsuperuser
```

```bash
  docker-compose exec web python manage.py makemigrations
```

```bash
  docker-compose exec web python manage.py migrate
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
  pytest
```

---

## 9. Production deployment (summary)

Deployment is performed via CI/CD using GitHub Actions and environment-specific `.env` files.
