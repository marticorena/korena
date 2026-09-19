# Korena EDU Backend

Korena EDU Backend is the server-side application for Korena's education platform. It provides user and school management, JWT-based authentication, email-driven account activation, and versioned document management for educational content.

The API is built with Django and Strawberry GraphQL. A small REST endpoint handles document-version uploads, while Celery and Redis process background jobs such as email delivery.

## Main features

- Email-based accounts with teacher, school administrator, and super administrator roles
- JWT login, refresh, verification, profile management, and account activation
- Schools and school-user relationships
- Educational document categories at state, school, teacher, and classroom levels
- PDF and DOCX uploads with document version history
- Background email processing and delivery logs
- Liveness and readiness checks through GraphQL
- Django admin for operational management

## Technology

- Python 3.12 and Django
- Strawberry GraphQL and Django REST Framework
- PostgreSQL
- Redis, Celery worker, and Celery Beat
- Nginx
- Docker Compose
- Pytest

## Project structure

```text
apps/
  accounts/       Users, authentication, and account workflows
  core/           Shared permissions, messages, tasks, and health checks
  documents/      Document categories, documents, versions, and uploads
  notifications/  Email delivery tasks and logs
  schools/        School data
config/           Django settings, URLs, ASGI/WSGI, Celery, and GraphQL schema
nginx/            Local reverse-proxy configuration
tests/            Automated test suite
```

## Run locally with Docker

### Requirements

- Docker
- Docker Compose

Clone the repository and enter it:

```bash
git clone https://github.com/marticorena/korena.git
cd korena
```

Create the local environment file:

```bash
cp .env.example .env
```

Review the values in `.env`, then build and start the services:

```bash
docker compose up -d --build
```

Apply the database migrations and create an administrator:

```bash
docker compose exec django-app python manage.py migrate
docker compose exec django-app python manage.py createsuperuser
```

The application is then available at:

- GraphQL API and interactive IDE: `http://localhost:8000/graphql/`
- Django admin: `http://localhost:8000/admin/`
- Document-version upload: `POST /api/documents/<document_id>/versions/`

Authenticated requests use an access token in the `Authorization: Bearer <token>` header.

## Development

Install the Python tooling and project dependencies for local editor support:

```bash
python -m venv .venv
pip install pip-tools
pip install -r requirements.txt
pre-commit install
```

When dependencies in `requirements.in` change, regenerate the locked requirements:

```bash
pip-compile requirements.in
```

Useful Django commands can be run in the application container:

```bash
docker compose exec django-app python manage.py makemigrations
docker compose exec django-app python manage.py migrate
docker compose exec django-app python manage.py collectstatic --noinput
```

## Tests

Run the test suite:

```bash
docker compose exec django-app pytest
```

Run it with an HTML coverage report:

```bash
docker compose exec django-app pytest --cov=. --cov-report=html
```

## Configuration

Development defaults are documented in `.env.example`. Before deploying, provide environment-specific values for Django secrets and hosts, PostgreSQL, Redis/Celery, frontend origins, and SMTP credentials. Do not commit a populated `.env` file.

Production deployment is expected to be handled by CI/CD with environment-specific secrets and configuration.
