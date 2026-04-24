import uuid
from django.conf import settings
from supabase import create_client


def get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError('Supabase URL and service key are required for storage operations.')
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_pdf_file(file_obj, bucket=None):
    client = get_supabase_client()
    bucket_name = bucket or settings.SUPABASE_STORAGE_PDF_BUCKET
    file_content = file_obj.read()
    storage_key = f'{uuid.uuid4()}/{file_obj.name}'
    response = client.storage.from_(bucket_name).upload(storage_key, file_content, content_type='application/pdf')
    status_code = getattr(response, 'status_code', None)
    if status_code and status_code not in (200, 201, 204):
        raise RuntimeError(f'PDF upload failed: {getattr(response, "text", response)}')
    public = client.storage.from_(bucket_name).get_public_url(storage_key)
    return storage_key, public.get('publicURL', '')


def upload_image_data(image_bytes, filename, bucket=None):
    client = get_supabase_client()
    bucket_name = bucket or settings.SUPABASE_STORAGE_IMAGE_BUCKET
    storage_key = f'{uuid.uuid4()}/{filename}'
    response = client.storage.from_(bucket_name).upload(storage_key, image_bytes, content_type='image/png')
    status_code = getattr(response, 'status_code', None)
    if status_code and status_code not in (200, 201, 204):
        raise RuntimeError(f'Image upload failed: {getattr(response, "text", response)}')
    public = client.storage.from_(bucket_name).get_public_url(storage_key)
    return public.get('publicURL', '')


def download_file(bucket, storage_key):
    client = get_supabase_client()
    response = client.storage.from_(bucket).download(storage_key)
    if hasattr(response, 'content'):
        return response.content
    if isinstance(response, bytes):
        return response
    raise RuntimeError('Unable to download file from Supabase storage.')
