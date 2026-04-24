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

## Database Migrations

After adding new models, run:

```bash
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
