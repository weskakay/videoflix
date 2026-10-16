# Videoflix API

REST backend for Videoflix, a small video streaming platform. Built with
Django and Django REST Framework, running in Docker with PostgreSQL, Redis
and Django RQ.

Uploaded videos are converted in the background with FFmpeg into HLS
streams in 480p, 720p and 1080p. Users register with their email address,
activate the account through a link in an email and log in with JWT tokens
stored in HttpOnly cookies.

The frontend is not part of this repository.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), started
- git

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/weskakay/videoflix.git
```

**2. Enter the project folder**

```bash
cd videoflix
```

**3. Create your .env file**

macOS and Linux:

```bash
cp .env.template .env
```

Windows:

```bash
copy .env.template .env
```

The values in `.env.template` work locally as they are. Before you use the
project for anything else, set your own `SECRET_KEY` and
`DJANGO_SUPERUSER_PASSWORD`.

**4. Build and start the containers**

```bash
docker compose up --build
```

On older Docker versions:

```bash
docker-compose up --build
```

The first start takes a few minutes. The container waits for PostgreSQL,
runs the migrations, creates the superuser from the `.env` and starts the
RQ worker. The API is ready when the log shows `Listening at:
http://0.0.0.0:8000`.

**5. Open the admin**

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/), log in with
`DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` from your `.env`.

## Configuration

All settings come from the `.env` file. Variables added to the template:

| Variable | Purpose | Value in the template |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Origins allowed to call the API with cookies | `localhost` and `127.0.0.1`, ports 5500 and 5501 |
| `FRONTEND_URL` | Base URL for the links in activation and reset mails | `http://127.0.0.1:5500` |

`CSRF_TRUSTED_ORIGINS` also allows port 5501.

## Design decisions

- `STATICFILES_STORAGE` was removed in Django 5.1. The same WhiteNoise
  storage is set through `STORAGES`.
- `backend.entrypoint.sh` is committed as executable. The project folder is
  mounted into the container, so on macOS and Linux the file mode from the
  host counts. The content is unchanged.
- The access token lives 60 minutes. The frontend refreshes it every 20
  minutes on the video list only, so it has to outlast a whole video in the
  player.
