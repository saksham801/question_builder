# MockTest AI — Question Builder

A production-grade Django application for extracting MCQs from large PDFs and saving structured questions into Supabase.

## Features

- Upload PDF files and extract subject/topic-based MCQ collections.
- Background processing with Celery and Redis.
- OpenRouter AI integration with rate limiting, retries, and Redis caching.
- Supabase Storage for PDFs and image assets.
- Preview and inline edit parsed questions before saving.
- Build tests from validated question sets.
- LaTeX rendering support using MathJax.
- Complete JEE-style exam engine with tab detection, auto-save, scoring, and PDF reports.
- Email delivery with Resend integration.

## Quick Start (Development)

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure for development:

```bash
cp .env.example .env
# Edit .env with your API keys (optional for basic testing)
```

3. Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

The app will work with local file storage for development. Upload PDFs at `http://localhost:8000/upload/`.

## Production Deployment

### Environment Configuration

Set the following environment variables in your `.env` file:

```bash
# Django
DJANGO_SECRET_KEY=your-50-character-random-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (Supabase or PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database
# OR configure individual Supabase variables:
SUPABASE_DB=your-database-name
SUPABASE_USER=your-db-user
SUPABASE_PASSWORD=your-db-password
SUPABASE_HOST=your-db-host
SUPABASE_PORT=5432

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_STORAGE_PDF_BUCKET=pdfs
SUPABASE_STORAGE_IMAGE_BUCKET=images

# Authentication
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_ANON_KEY=your-anon-key

# AI Service
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=mistralai/mistral-7b-instruct

# Email
RESEND_API_KEY=your-resend-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery (optional)
CELERY_TASK_ALWAYS_EAGER=False
```

### Security Settings

The application includes production-ready security settings that are automatically enabled when `DEBUG=False`:

- SSL/HTTPS enforcement
- HTTP Strict Transport Security (HSTS)
- Secure cookies (session, CSRF)
- Content Security Policy headers
- XSS protection
- Clickjacking protection

### Deployment Steps

1. **Set up your server** (Ubuntu/Debian recommended):

```bash
sudo apt update
sudo apt install python3 python3-pip postgresql redis-server nginx
```

2. **Configure PostgreSQL** (if not using Supabase):

```bash
sudo -u postgres createdb mocktest_db
sudo -u postgres createuser mocktest_user
sudo -u postgres psql -c "ALTER USER mocktest_user PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mocktest_db TO mocktest_user;"
```

3. **Deploy the application**:

```bash
# Clone and setup
git clone <your-repo>
cd question_builder
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Run migrations
python manage.py migrate
python manage.py collectstatic

# Start services
redis-server &
celery -A project worker -l info &
gunicorn project.wsgi:application --bind 0.0.0.0:8000 &
```

4. **Configure Nginx** (example config):

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /path/to/your/static/files/;
    }

    location /media/ {
        alias /path/to/your/media/files/;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Storage | Local files | Supabase Storage |
| Database | SQLite | PostgreSQL/Supabase |
| Authentication | Optional (test@example.com) | JWT required |
| Security | Basic | Full HTTPS/security |
| Caching | Redis (optional) | Redis required |
| Email | Disabled | Resend enabled |

## API Endpoints

- `GET /` - Dashboard
- `GET /upload/` - PDF upload form
- `POST /upload/` - Upload PDF for processing
- `GET /test/<id>/` - View test details
- `GET /exam/<attempt_id>/` - Take exam
- `POST /exam/<attempt_id>/submit/` - Submit exam
- `GET /exam/<attempt_id>/result/` - View results

## Troubleshooting

### Common Issues Fixed

1. **"Supabase URL and service key are required"** - Fixed with local storage fallback
2. **"'str' object has no attribute 'get'"** - Fixed Supabase client API usage
3. **Redis URL parsing errors** - Fixed lazy Redis client initialization
4. **Import errors** - Fixed relative import paths
5. **Authentication issues** - Added development authentication bypass

### Logs

Check `/logs/django.log` for application logs in production.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python manage.py test`
5. Submit a pull request

## License

MIT License
python manage.py makemigrations
python manage.py migrate
```

## Features

### PDF Upload & Processing
- Upload large PDFs (10k+ questions)
- AI-powered MCQ extraction via OpenRouter
- Redis-based rate limiting and caching
- Subject/Topic organization

### Question Management
- Preview and edit parsed questions
- Inline LaTeX rendering
- Diagram/image mapping from PDF

### Exam Engine (JEE-Style) **NEW**
- Full-screen test mode with countdown timer
- Question palette with status indicators (attempted, marked for review, unattempted)
- **Tab switch detection** with warning notifications
- **Auto-save** of answers via AJAX
- Security features: disable right-click, copy/paste during exam
- **JEE scoring**: +4 correct, -1 incorrect, 0 unattempted

### Results & Analysis **NEW**
- Detailed score summary and performance metrics
- Question-wise review with correct/incorrect tracking
- Accuracy percentage and time taken
- **PDF report generation** via reportlab
- **Email delivery** using Resend
- Analysis dashboard with visual performance breakdown

### Test Builder
- Select questions to create custom test sets
- Configure duration and total marks
- Many-to-many question management

## Environment Variables

Required:

- `DJANGO_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `OPENROUTER_API_KEY`
- `RESEND_API_KEY`
- `REDIS_URL`

Optional:

- `DATABASE_URL`
- `SUPABASE_STORAGE_PDF_BUCKET`
- `SUPABASE_STORAGE_IMAGE_BUCKET`

## Usage

### Dashboard & PDF Upload
- Visit `/` for the dashboard and recent uploads.
- Visit `/upload/` to upload a PDF and begin parsing.

### Question Management
- Visit `/questions/` to review saved questions.
- Visit `/upload/<id>/` to preview and edit parsed questions before final save.

### Test Builder & Exam
- Visit `/tests/` to create a new test from saved questions.
- Visit `/exam/start/<test_id>/` to begin an exam attempt.
- During exam:
  - Use question palette to navigate
  - Mark questions for review
  - Timer counts down
  - Tab switches are tracked
  - Answers auto-save
- After submission, view results and download PDF report.

## Notes

- AI results are cached in Redis and rate-limited for OpenRouter.
- The preview page allows editing questions before final save.
- The system supports subject/topic organization and diagram mapping.
- Exam mode uses Supabase JWT authentication via cookies or headers.
- PDF reports and email delivery require Resend API key configuration.
- All exam data is stored in PostgreSQL for persistence and analytics.
