from celery import shared_task
from django.db import transaction
from .models import PDFUpload
from .utils.parser import parse_pdf_bytes
from .services.storage import download_file


@shared_task(bind=True)
def process_pdf_upload_task(self, upload_id):
    upload = PDFUpload.objects.filter(pk=upload_id).first()
    if not upload:
        return

    upload.status = 'processing'
    upload.save(update_fields=['status'])

    try:
        file_bytes = download_file(upload.storage_bucket, upload.storage_key)
        parsed = parse_pdf_bytes(file_bytes, upload.subject, upload.topic)
        upload.parsed_json = parsed
        upload.status = 'ready'
        upload.error_message = ''
        upload.save(update_fields=['parsed_json', 'status', 'error_message'])
    except Exception as exc:
        upload.status = 'failed'
        upload.error_message = str(exc)
        upload.save(update_fields=['status', 'error_message'])
        raise
