import uuid
import os
from django.conf import settings
from supabase import create_client


def get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        if settings.DEBUG:
            # In development mode, raise a more helpful error
            raise RuntimeError('Supabase URL and service key are required for storage operations. '
                             'Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file, '
                             'or set up a Supabase project at https://supabase.com')
        raise RuntimeError('Supabase URL and service key are required for storage operations.')
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_pdf_file(file_obj, bucket=None):
    # In development mode without Supabase, use local file storage
    if settings.DEBUG and (not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY):
        return _upload_pdf_file_local(file_obj)

    client = get_supabase_client()
    bucket_name = bucket or settings.SUPABASE_STORAGE_PDF_BUCKET
    file_content = file_obj.read()
    storage_key = f'{uuid.uuid4()}/{file_obj.name}'
    response = client.storage.from_(bucket_name).upload(storage_key, file_content)
    status_code = getattr(response, 'status_code', None)
    if status_code and status_code not in (200, 201, 204):
        raise RuntimeError(f'PDF upload failed: {getattr(response, "text", response)}')
    public = client.storage.from_(bucket_name).get_public_url(storage_key)
    return storage_key, public


def _upload_pdf_file_local(file_obj):
    """Local file storage for development when Supabase is not configured."""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    # Create a unique filename
    storage_key = f'{uuid.uuid4()}/{file_obj.name}'

    # Save file locally
    file_content = file_obj.read()
    file_path = default_storage.save(storage_key, ContentFile(file_content))

    # Generate a local URL (this won't work for production but is fine for dev)
    from django.urls import reverse
    try:
        # Try to get the media URL if configured
        public_url = default_storage.url(file_path)
    except:
        # Fallback to a placeholder URL
        public_url = f'/media/{file_path}'

    return storage_key, public_url


def _upload_image_data_local(image_bytes, filename):
    """Local file storage for development when Supabase is not configured."""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    # Create a unique filename
    storage_key = f'{uuid.uuid4()}/{filename}'

    # Save file locally
    file_path = default_storage.save(storage_key, ContentFile(image_bytes))

    # Generate a local URL
    try:
        public_url = default_storage.url(file_path)
    except:
        public_url = f'/media/{file_path}'

    return public_url


def upload_image_data(image_bytes, filename, bucket=None):
    # In development mode without Supabase, use local file storage
    if settings.DEBUG and (not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY):
        return _upload_image_data_local(image_bytes, filename)

    client = get_supabase_client()
    bucket_name = bucket or settings.SUPABASE_STORAGE_IMAGE_BUCKET
    storage_key = f'{uuid.uuid4()}/{filename}'
    response = client.storage.from_(bucket_name).upload(storage_key, image_bytes)
    status_code = getattr(response, 'status_code', None)
    if status_code and status_code not in (200, 201, 204):
        raise RuntimeError(f'Image upload failed: {getattr(response, "text", response)}')
    public = client.storage.from_(bucket_name).get_public_url(storage_key)
    return public


def download_file(bucket, storage_key):
    # In development mode without Supabase, try local storage first
    if settings.DEBUG and (not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY):
        return _download_file_local(storage_key)

    client = get_supabase_client()
    response = client.storage.from_(bucket).download(storage_key)
    if hasattr(response, 'content'):
        return response.content
    if isinstance(response, bytes):
        return response
    raise RuntimeError('Unable to download file from Supabase storage.')


def _download_file_local(storage_key):
    """Download file from local storage for development."""
    from django.core.files.storage import default_storage
    try:
        with default_storage.open(storage_key, 'rb') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f'Unable to download file from local storage: {e}')
