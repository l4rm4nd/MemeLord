<div align="center" width="100%">
    <h1>MemeLord</h1>
    <img width="150px" src="myapp/static/assets/img/logo.png">
    <p>A Python Django Meme Image Board</p><p>
    <a target="_blank" href="https://github.com/l4rm4nd"><img src="https://img.shields.io/badge/maintainer-LRVT-orange" /></a>
    <a target="_blank" href="https://GitHub.com/l4rm4nd/MemeLord/graphs/contributors/"><img src="https://img.shields.io/github/contributors/l4rm4nd/MemeLord.svg" /></a>
    <a target="_blank" href="https://github.com/PyCQA/bandit"><img src="https://img.shields.io/badge/security-bandit-yellow.svg"/></a><br>
    <a target="_blank" href="https://GitHub.com/l4rm4nd/MemeLord/commits/"><img src="https://img.shields.io/github/last-commit/l4rm4nd/MemeLord.svg" /></a>
    <a target="_blank" href="https://GitHub.com/l4rm4nd/MemeLord/issues/"><img src="https://img.shields.io/github/issues/l4rm4nd/MemeLord.svg" /></a>
    <a target="_blank" href="https://github.com/l4rm4nd/MemeLord/issues?q=is%3Aissue+is%3Aclosed"><img src="https://img.shields.io/github/issues-closed/l4rm4nd/MemeLord.svg" /></a><br>
        <a target="_blank" href="https://github.com/l4rm4nd/MemeLord/stargazers"><img src="https://img.shields.io/github/stars/l4rm4nd/MemeLord.svg?style=social&label=Star" /></a>
    <a target="_blank" href="https://github.com/l4rm4nd/MemeLord/network/members"><img src="https://img.shields.io/github/forks/l4rm4nd/MemeLord.svg?style=social&label=Fork" /></a>
    <a target="_blank" href="https://github.com/l4rm4nd/MemeLord/watchers"><img src="https://img.shields.io/github/watchers/l4rm4nd/MemeLord.svg?style=social&label=Watch" /></a><br>
    <a href="https://www.buymeacoffee.com/LRVT" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</div>

<img width="1007" height="554" alt="image" src="https://github.com/user-attachments/assets/09be2221-b947-402f-8b09-21ff400ab30a" />

## ⭐ Features

- Web-based meme board for images, GIFs and videos
- Tagging with suggestions and tag-based filtering
- Commenting system with per-user delete permissions
- Local authentication and OIDC Single Sign-On (SSO)
- Light and dark mode with responsive Bootstrap 5 UI
- Drag & drop and clipboard paste for uploads
- Media files stored on disk for easy backup and direct access
- Infinite scroll feed with pagination fallback
- Admin view with thumbnails, uploader info and tags
- Support for SQLite3 and PostgreSQL

## 🔥 Installation

````bash
# create volume dirs for persistence
mkdir -p ./volume-data/database ./volume-data/media 

# adjust volume ownership to www-data (33)
sudo chown -R 33:33 volume-data/*

# spawn the stack
docker compose -f docker/docker-compose.yml up -d

# retrieve login credentials from container logs
docker compose -f docker/docker-compose.yml logs -f
````

> [!TIP]
> An official Unraid app exists in the store. See [wiki](https://github.com/l4rm4nd/MemeLord/wiki/01-%E2%80%90-Installation#unraid-installation).

## 🌏 Environment Variables

MemeLord takes various environment variables to configure `settings.py`:

| Variable                         | Description                                                                                                     | Default                    | Optional/Mandatory  |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------|----------------------------|---------------------|
| `DOMAIN`                         | Your Fully Qualified Domain Name (FQDN) or IP address. Used to define `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the Django framework. May define multiple ones by using a comma as delimiter. | `localhost` | Mandatory           |
| `DEBUG`                          | Set to `True` to enable Django debug mode. Should be `False` in production environments.                       | `False`                    | Optional            |
| `DJANGO_LOG_LEVEL`               | Django logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.                                | `INFO`                     | Optional            |
| `SECURE_COOKIES`                 | Set to `True` if you use a reverse proxy with TLS. Enables the `secure` cookie flag and `HSTS` HTTP response header, which will only work for SSL/TLS encrypted communication channels (HTTPS). | `False`                    | Optional            |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE`| Set to `False` if you want to keep sessions valid after browser close.                                          | `True`                    | Optional            |
| `SESSION_COOKIE_AGE`             | Define the maximum cookie age in minutes.                                                                       | `30`                       | Optional            |
| `SECRET_KEY`                     | Defines a fixed secret key for the Django framework. If missing, a secure secret is auto-generated on the server-side each time the container starts. | `<auto-generated>`         | Optional            |
| `PORT`                           | Defines a custom port. Used to set `CSRF_TRUSTED_ORIGINS` in conjunction with the `DOMAIN` environment variable for the Django framework. Only necessary, if VoucherVault is operated on a different port than `8000`, `80` or `443`. | `8000`                     | Optional            |
| `TZ`                           | Defines the `TIME_ZONE` variable in Django's settings.py. | `Europe/Berlin`                     | Optional            |
| `OIDC_ENABLED`                   | Set to `True` to enable OIDC authentication.                                                                    | `False`                    | Optional            |
| `OIDC_AUTOLOGIN`                 | Set to `True` if you want to automatically trigger OIDC flow on login page                                      | `False`                    | Optional            |
| `OIDC_CREATE_USER`               | Set to `True` to allow the creation of new users through OIDC.                                                  | `True`                     | Optional            |
| `OIDC_RP_SIGN_ALGO`              | The signing algorithm used by the OIDC provider (e.g., RS256, HS256).                                           | `HS256`                    | Optional            |
| `OIDC_RP_IDP_SIGN_KEY`           | The signing key used by the OIDC provider. If RS256 signing algo is used, either this or `OIDC_OP_JWKS_ENDPOINT` must be defined.                                                   | `None`                     | Optional            |
| `OIDC_OP_JWKS_ENDPOINT`          | URL of the JWKS endpoint for the OIDC provider. If RS256 signing algo is used, either this or `OIDC_RP_IDP_SIGN_KEY` must be defined.                                                                | `None`                     | Optional            |
| `OIDC_RP_CLIENT_ID`              | Client ID for your OIDC RP.                                                                                     | `None`                     | Optional            |
| `OIDC_RP_CLIENT_SECRET`          | Client secret for your OIDC RP.                                                                                 | `None`                     | Optional            |
| `OIDC_OP_AUTHORIZATION_ENDPOINT` | Authorization endpoint URL of the OIDC provider.                                                                | `None`                     | Optional            |
| `OIDC_OP_TOKEN_ENDPOINT`         | Token endpoint URL of the OIDC provider.                                                                        | `None`                     | Optional            |
| `OIDC_OP_USER_ENDPOINT`          | User info endpoint URL of the OIDC provider.                                                                    | `None`                     | Optional            |
| `OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS` | The length of time it takes for an id token to expire in seconds.                                           | 900                        | Optional            |
| `DB_ENGINE`                      | Database engine to use (e.g., `postgres` for PostgreSQL or `sqlite3` for SQLite3).                              | `sqlite3`                  | Optional            |
| `POSTGRES_HOST`                  | Hostname for the PostgreSQL database.                                                                           | `db`                       | Optional            |
| `POSTGRES_PORT`                  | Port number for the PostgreSQL database.                                                                        | `5432`                     | Optional            |
| `POSTGRES_USER`                  | PostgreSQL database user.                                                                                       | `memelord`                 | Optional            |
| `POSTGRES_PASSWORD`              | PostgreSQL database password.                                                                                   | `memelord`                 | Optional            |
| `POSTGRES_DB`                    | PostgreSQL database name.                                                                                       | `memelord`                 | Optional            |
| `MAX_UPLOAD_SIZE_MB`             | Maximum file upload size in megabytes.                                                                          | `10`                       | Optional            |
| `STORAGE_BACKEND`                | Storage backend to use. Options: `local`, `s3`, `azure`, `gcs`, `sftp`, `dropbox`, `ftp`. See [STORAGE_BACKENDS.md](STORAGE_BACKENDS.md) for detailed configuration. | `local`                    | Optional            |
| `AWS_ACCESS_KEY_ID`              | AWS/S3 access key ID (required when `STORAGE_BACKEND=s3`).                                                     | `None`                     | Optional            |
| `AWS_SECRET_ACCESS_KEY`          | AWS/S3 secret access key (required when `STORAGE_BACKEND=s3`).                                                 | `None`                     | Optional            |
| `AWS_STORAGE_BUCKET_NAME`        | S3 bucket name (required when `STORAGE_BACKEND=s3`).                                                           | `None`                     | Optional            |
| `AWS_S3_REGION_NAME`             | S3 region name.                                                                                                 | `us-east-1`                | Optional            |
| `AWS_S3_ENDPOINT_URL`            | Custom S3 endpoint URL for S3-compatible services (MinIO, DigitalOcean Spaces, etc.).                         | `None`                     | Optional            |
| `AZURE_ACCOUNT_NAME`             | Azure storage account name (required when `STORAGE_BACKEND=azure`).                                            | `None`                     | Optional            |
| `AZURE_ACCOUNT_KEY`              | Azure storage account key (required when `STORAGE_BACKEND=azure`).                                             | `None`                     | Optional            |
| `AZURE_CONTAINER`                | Azure blob storage container name.                                                                              | `media`                    | Optional            |
| `GS_BUCKET_NAME`                 | Google Cloud Storage bucket name (required when `STORAGE_BACKEND=gcs`).                                        | `None`                     | Optional            |
| `GS_PROJECT_ID`                  | Google Cloud project ID (required when `STORAGE_BACKEND=gcs`).                                                 | `None`                     | Optional            |
| `GS_CREDENTIALS`                 | Path to Google Cloud credentials JSON file (required when `STORAGE_BACKEND=gcs`).                              | `None`                     | Optional            |
| `SFTP_STORAGE_HOST`              | SFTP server hostname (required when `STORAGE_BACKEND=sftp`).                                                   | `None`                     | Optional            |
| `SFTP_STORAGE_USERNAME`          | SFTP username (required when `STORAGE_BACKEND=sftp`).                                                          | `None`                     | Optional            |
| `SFTP_STORAGE_PASSWORD`          | SFTP password (required when `STORAGE_BACKEND=sftp`).                                                          | `None`                     | Optional            |
| `DROPBOX_OAUTH2_TOKEN`           | Dropbox OAuth2 token (required when `STORAGE_BACKEND=dropbox`).                                                | `None`                     | Optional            |
| `FTP_STORAGE_LOCATION`           | FTP storage location URL (required when `STORAGE_BACKEND=ftp`).                                                | `None`                     | Optional            |
| `REDIS_HOST`                     | Redis server hostname for session storage and caching. When set, enables cloud-native Redis sessions. See [STORAGE_BACKENDS.md](STORAGE_BACKENDS.md) for details. | `None`                     | Optional            |
| `REDIS_PORT`                     | Redis server port.                                                                                              | `6379`                     | Optional            |
| `REDIS_DB`                       | Redis database number.                                                                                          | `0`                        | Optional            |
| `REDIS_PASSWORD`                 | Redis server password (if authentication is enabled).                                                           | `None`                     | Optional            |

> [!NOTE]
> For detailed storage backend configuration including all available options for S3, Azure, GCS, SFTP, Dropbox, and FTP, see [STORAGE_BACKENDS.md](STORAGE_BACKENDS.md).

> [!TIP]
> **Cloud-Native Deployments:** For horizontally scaled deployments (Kubernetes, Docker Swarm, ECS, etc.), configure Redis sessions by setting `REDIS_HOST` to enable shared session storage across all application instances. See [STORAGE_BACKENDS.md](STORAGE_BACKENDS.md) for Redis configuration examples.
