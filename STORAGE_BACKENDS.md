# Storage Backend Configuration

This application supports multiple storage backends via `django-storages`. 

You can configure which storage backend to use through environment variables.

## Supported Storage Backends

- **local** - Local filesystem storage (default)
- **s3** - Amazon S3 or S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
- **azure** - Microsoft Azure Blob Storage
- **gcs** - Google Cloud Storage
- **sftp** - SFTP/SSH Storage
- **dropbox** - Dropbox Storage
- **ftp** - FTP Storage


> [!WARNING]
> Only the `local` and `s3` storage backends were tested and confirmed to be working.
> 
> Other backends should work but are subject to a proper `django-storages` configuration.

## Configuration

Set the `STORAGE_BACKEND` environment variable to the desired backend. If not set, it defaults to `local`.

---

## Local Storage (Default)

No additional configuration needed. Files are stored in the `media/` directory.

```bash
STORAGE_BACKEND=local
```

---

## Amazon S3 / S3-Compatible Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

### Optional Environment Variables:
```bash
AWS_S3_REGION_NAME=us-east-1              # Default: us-east-1
AWS_S3_CUSTOM_DOMAIN=cdn.example.com      # For CloudFront or custom CDN
AWS_S3_ENDPOINT_URL=https://minio.example.com  # For S3-compatible services
AWS_DEFAULT_ACL=private                    # Default: private
AWS_QUERYSTRING_AUTH=True                  # Use signed URLs (default: True)
AWS_S3_FILE_OVERWRITE=False                # Overwrite files with same name (default: False)
AWS_LOCATION=media                         # Folder within bucket (default: media)
```

### Example for MinIO:
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=memelord
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_REGION_NAME=us-east-1
```

### Example for DigitalOcean Spaces:
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your_do_spaces_key
AWS_SECRET_ACCESS_KEY=your_do_spaces_secret
AWS_STORAGE_BUCKET_NAME=your_space_name
AWS_S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
AWS_S3_REGION_NAME=nyc3
```

---

## Microsoft Azure Blob Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=your_account_name
AZURE_ACCOUNT_KEY=your_account_key
```

### Optional Environment Variables:
```bash
AZURE_CONTAINER=media                      # Default: media
AZURE_SSL=True                             # Use SSL (default: True)
AZURE_UPLOAD_MAX_CONN=2                    # Max connections (default: 2)
AZURE_CONNECTION_TIMEOUT_SECS=20           # Connection timeout (default: 20)
AZURE_BLOB_MAX_MEMORY_SIZE=2MB             # Max memory size (default: 2MB)
AZURE_URL_EXPIRATION_SECS=3600             # URL expiration (default: 3600)
AZURE_OVERWRITE_FILES=False                # Overwrite files (default: False)
AZURE_LOCATION=                            # Optional prefix path
AZURE_CUSTOM_DOMAIN=cdn.example.com        # Optional CDN domain
```

### Example:
```bash
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=mymemelordaccount
AZURE_ACCOUNT_KEY=your_azure_key_here
AZURE_CONTAINER=media
```

---

## Google Cloud Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=gcs
GS_BUCKET_NAME=your_bucket_name
GS_PROJECT_ID=your_project_id
GS_CREDENTIALS=/path/to/credentials.json
```

### Optional Environment Variables:
```bash
GS_DEFAULT_ACL=private                     # Default: private
GS_FILE_OVERWRITE=False                    # Overwrite files (default: False)
GS_LOCATION=media                          # Folder within bucket (default: media)
GS_CUSTOM_ENDPOINT=https://cdn.example.com # Custom domain
GS_QUERYSTRING_AUTH=True                   # Use signed URLs (default: True)
```

### Example:
```bash
STORAGE_BACKEND=gcs
GS_BUCKET_NAME=memelord-bucket
GS_PROJECT_ID=memelord-project
GS_CREDENTIALS=/app/gcs-credentials.json
GS_LOCATION=media
```

---

## SFTP Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=sftp
SFTP_STORAGE_HOST=sftp.example.com
SFTP_STORAGE_USERNAME=your_username
```

### Authentication (choose one):
```bash
# Password authentication:
SFTP_STORAGE_PASSWORD=your_password

# OR Private key authentication:
SFTP_STORAGE_PRIVATE_KEY=/path/to/private_key
```

### Optional Environment Variables:
```bash
SFTP_STORAGE_PORT=22                       # Default: 22
SFTP_STORAGE_ROOT=/media/                  # Root path (default: /media/)
SFTP_STORAGE_INTERACTIVE=False             # Interactive mode (default: False)
SFTP_STORAGE_FILE_MODE=0644                # File permissions
SFTP_STORAGE_DIR_MODE=0755                 # Directory permissions
SFTP_STORAGE_UID=1000                      # User ID
SFTP_STORAGE_GID=1000                      # Group ID
SFTP_KNOWN_HOST_FILE=/path/to/known_hosts  # Known hosts file
```

### Example:
```bash
STORAGE_BACKEND=sftp
SFTP_STORAGE_HOST=sftp.example.com
SFTP_STORAGE_PORT=22
SFTP_STORAGE_USERNAME=memelord
SFTP_STORAGE_PASSWORD=secure_password
SFTP_STORAGE_ROOT=/var/www/media/
```

---

## Dropbox Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=dropbox
DROPBOX_OAUTH2_TOKEN=your_oauth2_token
```

### Optional Environment Variables:
```bash
DROPBOX_ROOT_PATH=/media                   # Root path (default: /media)
DROPBOX_TIMEOUT=100                        # Timeout in seconds (default: 100)
DROPBOX_WRITE_MODE=add                     # 'add' or 'overwrite' (default: add)
```

### Example:
```bash
STORAGE_BACKEND=dropbox
DROPBOX_OAUTH2_TOKEN=your_long_oauth2_token_here
DROPBOX_ROOT_PATH=/Apps/MemeLord/media
```

### Getting Dropbox OAuth2 Token:
1. Create an app at https://www.dropbox.com/developers/apps
2. Generate an access token in the app settings
3. Use that token as `DROPBOX_OAUTH2_TOKEN`

---

## FTP Storage

### Required Environment Variables:
```bash
STORAGE_BACKEND=ftp
FTP_STORAGE_LOCATION=ftp://username:password@host:port/path
```

### Example:
```bash
STORAGE_BACKEND=ftp
FTP_STORAGE_LOCATION=ftp://memelord:secure_pass@ftp.example.com:21/media
```

---

## Testing Your Configuration

A Django management command is available to test and debug your storage backend configuration:

```bash
python manage.py test_storage
```

This command will:
- Display your current storage backend configuration
- Show all relevant environment variables
- Test file upload, retrieval, and deletion
- Verify the storage backend is working correctly
- Display any errors with detailed tracebacks

### Example Output:
```
=== Storage Backend Test ===

Storage Backend: s3
Storage Class: S3Boto3Storage
Media URL: https://my-bucket.s3.amazonaws.com/media/

--- S3 Configuration ---
AWS_ACCESS_KEY_ID: SET
AWS_SECRET_ACCESS_KEY: SET
AWS_STORAGE_BUCKET_NAME: my-bucket
AWS_S3_REGION_NAME: us-east-1
AWS_S3_ENDPOINT_URL: DEFAULT (AWS)
AWS_LOCATION: media
AWS_DEFAULT_ACL: private
AWS_QUERYSTRING_AUTH: True
AWS_S3_FILE_OVERWRITE: False

--- Testing File Upload ---
Attempting to save test file: memes/user_test/test_storage_file.txt
✓ File saved successfully: media/memes/user_test/test_storage_file.txt
✓ File exists in storage
✓ File URL: https://my-bucket.s3.amazonaws.com/media/memes/user_test/test_storage_file.txt
✓ File size: 54 bytes
✓ File content verified

=== Test Complete ===
```

---

## Debugging and Logging

### Enable Debug Logging

Set the following environment variables to enable detailed logging:

```bash
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
```

This will enable detailed logging for:
- Django framework operations
- Storage backend operations (django-storages)
- AWS SDK operations (boto3/botocore for S3)
- Azure SDK operations
- Google Cloud SDK operations

### View Logs

Logs are written to both console and file:
- **Console**: Real-time output when running Django
- **File**: `logs/django.log` (with automatic rotation, max 15MB per file)

### Check Logs for Storage Issues

```bash
# Tail the log file
tail -f logs/django.log

# Search for storage-related errors
grep -i "storage\|s3\|boto" logs/django.log

# Search for file upload operations
grep -i "saving media file\|upload" logs/django.log
```

### Common Log Messages

**Successful Upload:**
```
INFO Saving media file: memes/user_1/example.jpg using storage backend: s3
DEBUG Storage class: S3Boto3Storage
DEBUG File size: 524288 bytes
DEBUG S3 Bucket: my-bucket
DEBUG S3 Region: us-east-1
INFO Media file saved successfully: media/memes/user_1/example.jpg
DEBUG File URL: https://my-bucket.s3.amazonaws.com/media/memes/user_1/example.jpg?...
```

**Upload Error:**
```
ERROR Error during storage test: An error occurred (NoSuchBucket) when calling the PutObject operation
```

---

## Migration Notes

### Moving from Local to Cloud Storage:

1. **Set up your cloud storage bucket/container** with appropriate permissions
2. **Configure environment variables** for your chosen backend
3. **Upload existing media files** to the new storage backend (manual migration required)
4. **Update your environment** and restart the application

### Example migration script (S3):
```bash
# Using AWS CLI to sync local media to S3
aws s3 sync ./media/ s3://your-bucket-name/media/ --acl private
```

---

## Troubleshooting

---

## Redis Cache & Sessions (Cloud-Native)

For cloud-native deployments with horizontal scaling, you can configure Redis for session storage and general caching. This ensures sessions work across all application instances.

### Why Use Redis for Sessions?

**Benefits:**
- ✅ **Horizontal Scaling** - Sessions work across multiple app instances/containers
- ✅ **Fast Performance** - Redis is in-memory, much faster than database queries
- ✅ **Load Balancer Friendly** - Users stay logged in when routed to different servers
- ✅ **Automatic Expiration** - Redis handles session cleanup automatically
- ✅ **Cloud Native** - Works perfectly with Kubernetes, Docker Swarm, ECS, etc.

### Configuration

#### Required Environment Variables:
```bash
REDIS_HOST=redis.example.com        # Redis server hostname
```

#### Optional Environment Variables:
```bash
REDIS_PORT=6379                      # Default: 6379
REDIS_DB=0                           # Default: 0
REDIS_PASSWORD=your_password         # Optional: Redis password
```

### Example Configurations

#### Development (Local Redis):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

#### Production (AWS ElastiCache):
```bash
REDIS_HOST=memelord.abc123.0001.use1.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

#### Production (Azure Cache for Redis):
```bash
REDIS_HOST=memelord.redis.cache.windows.net
REDIS_PORT=6380
REDIS_DB=0
REDIS_PASSWORD=your_access_key
```

#### Production (Google Cloud Memorystore):
```bash
REDIS_HOST=10.0.0.3
REDIS_PORT=6379
REDIS_DB=0
```

#### Docker Compose Example:
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  web:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0

volumes:
  redis_data:
```

### Behavior

**When `REDIS_HOST` is set:**
- Sessions are stored in Redis
- Fast session lookups (in-memory)
- Sessions persist across app restarts (if Redis persistence enabled)
- General caching uses Redis (with 5-minute default timeout)

**When `REDIS_HOST` is not set (default):**
- Sessions are stored in the database (backward compatible)
- No Redis connection required
- Works for single-instance deployments

### Testing Redis Connection

```bash
# Test Redis connectivity
redis-cli -h <REDIS_HOST> -p <REDIS_PORT> ping

# Should return: PONG

# View Redis session keys
redis-cli -h <REDIS_HOST> -p <REDIS_PORT>
> KEYS memelord:*
```

### Cache Configuration Details

The Redis cache is configured with:
- **Key Prefix**: `memelord` - Prevents key collisions with other apps
- **Timeout**: 300 seconds (5 minutes) default
- **Compression**: zlib compression for data efficiency
- **Connection Pool**: Max 50 connections, with retry on timeout
- **Graceful Degradation**: `IGNORE_EXCEPTIONS=True` - App continues if Redis is down

### Performance Tips

1. **Use Redis for Sessions in Production** - Database sessions don't scale well
2. **Enable Redis Persistence** - Use AOF or RDB to prevent session loss on Redis restart
3. **Monitor Redis Memory** - Set `maxmemory` and `maxmemory-policy` in Redis config
4. **Use Connection Pooling** - Already configured (50 max connections)
5. **Consider Redis Cluster** - For very high-traffic deployments

### Troubleshooting Redis Sessions

**Problem:** Users getting logged out randomly

**Causes:**
- Redis server restarted without persistence
- Redis memory full (evicting keys)
- Network connectivity issues

**Solutions:**
- Enable Redis AOF persistence: `redis-server --appendonly yes`
- Set appropriate `maxmemory-policy`: `allkeys-lru` or `volatile-lru`
- Monitor Redis with CloudWatch/Prometheus

**Problem:** Sessions not working after deployment

**Check:**
1. Redis host is accessible from app containers
2. Firewall rules allow Redis port (6379)
3. Redis password is correct (if set)
4. Test connection: `redis-cli -h $REDIS_HOST ping`

---

## Troubleshooting

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** or secret management services
3. **Use private ACLs** for sensitive content
4. **Enable HTTPS** for all cloud storage endpoints
5. **Rotate access keys** regularly
6. **Use IAM roles** instead of access keys when running on cloud platforms
7. **Enable versioning** on your cloud storage buckets
8. **Set up proper CORS policies** if accessing files from browsers

---

## Additional Resources

- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)

---

## Content Security Policy (CSP) Configuration

When using cloud storage backends, you need to ensure your Content Security Policy allows images from the storage provider's domain. The application automatically configures CSP based on your storage backend, but you should be aware of the URL formats used.

### Automatic CSP Configuration

The application automatically adds the appropriate domains to the CSP `img-src` directive based on your `STORAGE_BACKEND` setting:

**S3 Storage:**
- `https://bucket-name.s3.amazonaws.com` (global endpoint)
- `https://bucket-name.s3.region.amazonaws.com` (region-specific endpoint)

**Azure Storage:**
- `https://account-name.blob.core.windows.net`

**Google Cloud Storage:**
- `https://storage.googleapis.com`
- `https://storage.cloud.google.com`
- `https://bucket-name.storage.googleapis.com`

### Important Notes on URL Formats

#### S3 Virtual-Hosted-Style vs Path-Style URLs

AWS S3 supports two URL formats:

1. **Virtual-hosted-style** (recommended): `https://bucket-name.s3.region.amazonaws.com/path/to/file`
2. **Path-style** (legacy): `https://s3.region.amazonaws.com/bucket-name/path/to/file`

The application uses **virtual-hosted-style URLs** by default (via `AWS_S3_ADDRESSING_STYLE = 'virtual'`). This is important because:
- Virtual-hosted-style URLs work with the automatic CSP configuration
- Path-style URLs are being deprecated by AWS
- Signed URLs must use the same format as the endpoint configuration

#### Azure Blob Storage URLs

Azure uses the format: `https://account-name.blob.core.windows.net/container-name/path/to/file`

#### Google Cloud Storage URLs

GCS supports multiple URL formats:
- Canonical: `https://storage.googleapis.com/bucket-name/path/to/file`
- XML API: `https://bucket-name.storage.googleapis.com/path/to/file`

### Common CSP Issues

**Problem:** Images not loading, browser console shows CSP violation

**Solution:** Check that:
1. Your storage backend environment variables are set correctly
2. The URL format in the CSP error matches your storage configuration
3. Restart Django after changing storage backend settings

**Example CSP Error:**
```
Content-Security-Policy: The page's settings blocked the loading of a resource (img-src) 
at https://example.s3.amazonaws.com/... because it violates the following directive: "img-src 'self'..."
```

This means the storage URL is not in the CSP allowlist. Verify your `STORAGE_BACKEND` environment variable is set and restart Django.

---

## Signed URLs and Authentication

When using private storage (`AWS_DEFAULT_ACL=private`, `GS_DEFAULT_ACL=private`, etc.), the storage backends generate signed URLs with temporary access credentials.

### S3 Signed URLs

S3 signed URLs include query parameters for authentication:
```
https://bucket.s3.region.amazonaws.com/path/file.jpg?
  X-Amz-Algorithm=AWS4-HMAC-SHA256&
  X-Amz-Credential=AKIAIOSFODNN7EXAMPLE/20251209/us-east-1/s3/aws4_request&
  X-Amz-Date=20251209T120000Z&
  X-Amz-Expires=3600&
  X-Amz-SignedHeaders=host&
  X-Amz-Signature=...
```

**Important:** The signature is region-specific. If you get 403 Forbidden errors:
- Ensure `AWS_S3_REGION_NAME` matches your bucket's region
- Don't manually set `AWS_S3_ENDPOINT_URL` for standard AWS S3 (only for S3-compatible services)
- Use Signature Version 4 (`AWS_S3_SIGNATURE_VERSION = 's3v4'`) - this is configured automatically

### Azure Shared Access Signatures (SAS)

Azure generates SAS tokens for private blob access:
```
https://account.blob.core.windows.net/container/path/file.jpg?
  sv=2020-08-04&
  st=2025-12-09T12:00:00Z&
  se=2025-12-09T13:00:00Z&
  sr=b&
  sp=r&
  sig=...
```

### GCS Signed URLs

Google Cloud Storage signed URLs use similar authentication:
```
https://storage.googleapis.com/bucket/path/file.jpg?
  X-Goog-Algorithm=GOOG4-RSA-SHA256&
  X-Goog-Credential=...&
  X-Goog-Date=20251209T120000Z&
  X-Goog-Expires=3600&
  X-Goog-SignedHeaders=host&
  X-Goog-Signature=...
```

### URL Expiration

Signed URLs expire after a certain time (default 1 hour for S3). Configure expiration times:

- **S3**: Not directly configurable via django-storages (uses 3600 seconds)
- **Azure**: `AZURE_URL_EXPIRATION_SECS=3600`
- **GCS**: Not directly configurable via django-storages (uses 3600 seconds)

For longer expiration times or public access, consider setting ACLs to public:
- S3: `AWS_DEFAULT_ACL=public-read`
- GCS: `GS_DEFAULT_ACL=publicRead`
- Azure: Use public containers or connection strings