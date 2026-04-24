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

## Setup

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your credentials.

3. Run migrations:

```bash
python manage.py migrate
```

4. Start Redis, Celery, and Django:

```bash
redis-server
celery -A project worker -l info
python manage.py runserver
```
## Run tests

```bash
python manage.py test mcq
```
## Environment Variables

Required:

- `DJANGO_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `OPENROUTER_API_KEY`
- `REDIS_URL`

Optional:

- `DATABASE_URL`
- `SUPABASE_STORAGE_PDF_BUCKET`
- `SUPABASE_STORAGE_IMAGE_BUCKET`

## Usage

- Visit `/upload/` to upload a PDF and begin parsing.
- Visit `/` for the dashboard and recent uploads.
- Visit `/questions/` to review saved questions.
- Visit `/tests/` to build a new exam set.

## Notes

- AI results are cached in Redis and rate-limited for OpenRouter.
- The preview page allows editing questions before final save.
- The system supports subject/topic organization and diagram mapping.
