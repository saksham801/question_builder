import json
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from .forms import PDFUploadForm
from .middleware import SupabaseJWTMiddleware
from .views import get_user_email
from .utils.parser import build_prompt, extract_json_array, validate_question_item
import jwt


class ParserUtilsTests(TestCase):
    def test_build_prompt_includes_chunk_text(self):
        chunk = 'Sample question text with choices and answers.'
        prompt = build_prompt(chunk)
        self.assertIn(chunk, prompt)
        self.assertIn('Extract all MCQs', prompt)

    def test_extract_json_array_parses_wrapped_json(self):
        raw = 'Here is the output:\n[{"question":"Q?","options":{"A":"a","B":"b","C":"c","D":"d"},"answer":"A"}]\nThank you.'
        parsed = extract_json_array(raw)
        self.assertEqual(parsed[0]['question'], 'Q?')
        self.assertEqual(parsed[0]['answer'], 'A')

    def test_extract_json_array_invalid_response_raises(self):
        with self.assertRaises(ValueError):
            extract_json_array('No valid JSON here')

    def test_validate_question_item_returns_normalized_item(self):
        item = {
            'question': 'What is 2+2?',
            'options': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
            'answer': 'B',
        }
        normalized = validate_question_item(item)
        self.assertEqual(normalized['answer'], 'B')
        self.assertEqual(normalized['options']['B'], '4')

    def test_validate_question_item_rejects_incomplete_item(self):
        item = {'question': 'Missing options', 'options': {'A': '1'}, 'answer': 'A'}
        self.assertIsNone(validate_question_item(item))


class PDFUploadFormTests(TestCase):
    def test_pdf_upload_form_rejects_non_pdf(self):
        upload = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        form = PDFUploadForm(data={'subject': 'Math', 'topic': 'Algebra'}, files={'pdf_file': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)

    def test_pdf_upload_form_accepts_pdf_file(self):
        upload = SimpleUploadedFile('test.pdf', b'%PDF-1.4 content', content_type='application/pdf')
        form = PDFUploadForm(data={'subject': 'Science', 'topic': 'Physics'}, files={'pdf_file': upload})
        self.assertTrue(form.is_valid())


@override_settings(SUPABASE_JWT_SECRET='test-secret')
class SupabaseJWTMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SupabaseJWTMiddleware()

    def _get_token(self, email):
        token = jwt.encode({'email': email}, 'test-secret', algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token

    def test_process_request_reads_jwt_cookie(self):
        token = self._get_token('user@example.com')
        request = self.factory.get('/')
        request.COOKIES['sb:token'] = token
        self.middleware.process_request(request)
        self.assertEqual(request.user_email, 'user@example.com')

    def test_get_user_email_requires_authenticated_request(self):
        request = self.factory.get('/')
        request.user_email = ''
        # In DEBUG mode, should return default email
        if settings.DEBUG:
            self.assertEqual(get_user_email(request), 'test@example.com')
        else:
            with self.assertRaises(PermissionDenied):
                get_user_email(request)
