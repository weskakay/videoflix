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

### Email

Activation and password reset mails are sent by the RQ worker in the
background. As long as `EMAIL_HOST` is empty, Django prints every mail to the
container log instead of sending it, so you can copy the link from there:

```bash
docker compose logs web
```

To send real mails, fill in the SMTP values of your provider, for example
Gmail with an [app password](https://myaccount.google.com/apppasswords):

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your.address@gmail.com
EMAIL_HOST_PASSWORD=your app password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=Videoflix <your.address@gmail.com>
```

The RQ worker reads the settings and the code only when the container
starts. After changing the `.env` or a background task, restart it:

```bash
docker compose restart web
```

## Authentication

Users log in with email and password. The backend answers with two HttpOnly
cookies, `access_token` (60 minutes) and `refresh_token` (1 day). Every
protected request needs the access cookie, the frontend sends it with
`credentials: 'include'`. Tokens never appear in a response body, except the
new access token of the refresh endpoint, as the API documentation shows it.

A new account stays inactive until the link from the activation mail is
opened.

Open the frontend on `127.0.0.1` as well, not on `localhost`. The API runs on
`127.0.0.1:8000`, and browsers do not send `SameSite=Lax` cookies from
`localhost` to `127.0.0.1`.

Set `JWT_COOKIE_SECURE=True` in the `.env` as soon as the API runs on HTTPS,
the cookies are then only sent over encrypted connections.

## Endpoints

Every error answers with a JSON body `{"detail": "..."}`.

### Authentication

| Method | Path | Who | Codes |
|---|---|---|---|
| POST | `/api/register/` | anyone | 201, 400 |
| GET | `/api/activate/<uidb64>/<token>/` | anyone | 200, 400 |
| POST | `/api/login/` | anyone | 200, 400 |
| POST | `/api/logout/` | refresh cookie | 200, 400 |
| POST | `/api/token/refresh/` | refresh cookie | 200, 400, 401 |
| POST | `/api/password_reset/` | anyone | 200, 400 |
| POST | `/api/password_confirm/<uidb64>/<token>/` | anyone | 200, 400 |

## Design decisions

- `STATICFILES_STORAGE` was removed in Django 5.1. The same WhiteNoise
  storage is set through `STORAGES`.
- `backend.entrypoint.sh` is committed as executable. The project folder is
  mounted into the container, so on macOS and Linux the file mode from the
  host counts. The content is unchanged.
- The access token lives 60 minutes. The frontend refreshes it every 20
  minutes on the video list only, so it has to outlast a whole video in the
  player.
- The register response contains the activation token, as the API
  documentation asks for it. With the token and the user id anyone could
  build the activation link, so in production it should only travel by mail.
- `EMAIL_HOST` is empty in `.env.template`, so a fresh setup prints the mails
  to the log instead of failing to send them.
- Activation and reset links are valid for 24 hours, as the reset mail
  promises (`PASSWORD_RESET_TIMEOUT`). Opening an activation link twice
  answers 200 again, after the first login it stops working. A reset link
  works once, the new password makes it invalid. Accounts that are not
  activated yet cannot reset their password.
- `password_reset` answers 200 with the same text for every valid email
  address, also for unknown and inactive accounts. Only active accounts get
  a mail. A malformed address answers 400.
- Wrong input on register, activate, login, password reset and password
  confirm always answers 400 with the same message,
  `Please check your input and try again.`. A wrong password,
  an unknown email and an inactive account get the same answer.
- Logout only needs the refresh cookie, so an expired access cookie cannot
  stop a user from logging out. Without the refresh cookie it answers 400.
  The refresh token goes on the blacklist and both cookies are deleted. An
  access token copied before stays valid until it expires, JWTs cannot be
  revoked one by one.
- The refresh endpoint answers 400 when the cookie is missing and 401 when
  the token is broken, expired or blacklisted.
- There is no CSRF check on the API, the frontend does not send a CSRF
  token. The cookies use `SameSite=Lax`, so browsers do not send them with
  POST requests from other sites, and CORS only allows the frontend origins.
