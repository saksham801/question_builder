from django.conf import settings
from resend import Resend
from .storage import upload_image_data


def send_attempt_report_email(attempt, pdf_bytes):
    """
    Send exam report via email using Resend.
    Uploads PDF to Supabase Storage and emails link.
    """
    if not settings.RESEND_API_KEY:
        raise RuntimeError('RESEND_API_KEY is not configured.')

    pdf_filename = f'exam-report-{attempt.id}.pdf'
    try:
        pdf_url = _upload_pdf_to_storage(pdf_bytes, pdf_filename)
    except Exception as exc:
        raise RuntimeError(f'Failed to upload PDF: {exc}')

    client = Resend(api_key=settings.RESEND_API_KEY)
    email_body = f"""
<h2>Your Exam Report - {attempt.test.title}</h2>
<p>Hi {attempt.user_email},</p>
<p>Your exam report is ready! Download it below:</p>
<p>
  <strong>Score:</strong> {attempt.score}<br/>
  <strong>Accuracy:</strong> {attempt.accuracy_percentage}%<br/>
  <strong>Status:</strong> {attempt.status.title()}<br/>
</p>
<p><a href="{pdf_url}">📥 Download Full Report (PDF)</a></p>
<p>Best regards,<br/>MockTest AI Team</p>
"""

    try:
        response = client.emails.send({
            'from': 'MockTest AI <noreply@resend.dev>',
            'to': attempt.user_email,
            'subject': f'Exam Report: {attempt.test.title}',
            'html': email_body,
        })
        if response.get('id'):
            attempt.email_sent = True
            attempt.pdf_url = pdf_url
            attempt.pdf_generated = True
            attempt.save(update_fields=['email_sent', 'pdf_url', 'pdf_generated'])
            return response
        else:
            raise RuntimeError(f'Resend API error: {response}')
    except Exception as exc:
        raise RuntimeError(f'Email send failed: {exc}')


def _upload_pdf_to_storage(pdf_bytes, filename, bucket='reports'):
    """Helper to upload PDF to Supabase Storage."""
    from .storage import upload_image_data
    import os
    from django.conf import settings
    from supabase import create_client

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    import uuid
    storage_key = f'{uuid.uuid4()}/{filename}'
    response = client.storage.from_(bucket).upload(storage_key, pdf_bytes, content_type='application/pdf')
    status_code = getattr(response, 'status_code', None)
    if status_code and status_code not in (200, 201, 204):
        raise RuntimeError(f'PDF upload failed: {getattr(response, "text", response)}')
    public = client.storage.from_(bucket).get_public_url(storage_key)
    return public.get('publicURL', '')
