import io
import json
import re
import pdfplumber
import pytesseract
import fitz
from django.conf import settings
from .openrouter import call_openrouter
from ..services.storage import upload_image_data


def extract_json_array(raw_text):
    if not raw_text:
        raise ValueError('Empty AI response')

    start = raw_text.find('[')
    end = raw_text.rfind(']')
    if start == -1 or end == -1:
        raise ValueError('AI response does not contain JSON array')

    candidate = raw_text[start:end + 1]
    return json.loads(candidate)


def normalize_option_label(label):
    normalized = str(label).strip().upper()
    if normalized in ['A', 'B', 'C', 'D']:
        return normalized
    if normalized.startswith('1'):
        return 'A'
    if normalized.startswith('2'):
        return 'B'
    if normalized.startswith('3'):
        return 'C'
    if normalized.startswith('4'):
        return 'D'
    return normalized[:1]


def build_prompt(chunk_text):
    return (
        'Extract all MCQs from the text below and return only valid JSON. '
        'The output must be a JSON array with objects that contain exactly these fields: '
        '{"question":"", "options":{"A":"", "B":"", "C":"", "D":""}, "answer":""}. '
        'Do not include explanations or any surrounding text. Normalize answers to A/B/C/D. '
        'If an item is incomplete, omit it. Text:\n'
        + chunk_text
    )


def validate_question_item(item):
    if not isinstance(item, dict):
        return None
    question = str(item.get('question', '')).strip()
    options = item.get('options', {})
    answer = str(item.get('answer', '')).strip().upper()
    if not question or not isinstance(options, dict) or answer not in ['A', 'B', 'C', 'D']:
        return None

    normalized = {'question': question, 'options': {}, 'answer': answer}
    for label in ['A', 'B', 'C', 'D']:
        text = options.get(label) or options.get(label.lower()) or options.get(label.upper())
        if not text:
            return None
        normalized['options'][label] = str(text).strip()

    return normalized


def split_text_chunks(page_texts, max_length=2000):
    chunks = []
    current_text = ''
    current_pages = []

    for page in page_texts:
        page_text = page['text'].strip()
        if not page_text:
            continue

        if len(current_text) + len(page_text) + 2 <= max_length:
            current_text = current_text + '\n\n' + page_text if current_text else page_text
            current_pages.append(page['page'])
        else:
            if current_text:
                chunks.append({'text': current_text, 'pages': current_pages})
            if len(page_text) <= max_length:
                current_text = page_text
                current_pages = [page['page']]
            else:
                paragraphs = re.split(r'\n{2,}', page_text)
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue
                    if len(current_text) + len(paragraph) + 2 <= max_length:
                        current_text = current_text + '\n\n' + paragraph if current_text else paragraph
                        current_pages.append(page['page'])
                    else:
                        if current_text:
                            chunks.append({'text': current_text, 'pages': current_pages})
                        current_text = paragraph
                        current_pages = [page['page']]
    if current_text:
        chunks.append({'text': current_text, 'pages': current_pages})
    return chunks


def extract_page_texts(file_bytes):
    page_texts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ''
            if not text.strip():
                image = page.to_image(resolution=200).original
                text = pytesseract.image_to_string(image)
            page_texts.append({'page': index, 'text': text})
    return page_texts


def extract_images(file_bytes):
    images = []
    document = fitz.open(stream=file_bytes, filetype='pdf')
    for page in document:
        page_number = page.number + 1
        for image_number, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            image_info = document.extract_image(xref)
            image_bytes = image_info.get('image')
            if not image_bytes:
                continue
            extension = image_info.get('ext', 'png')
            filename = f'page-{page_number}-{image_number}.{extension}'
            public_url = upload_image_data(image_bytes, filename)
            images.append({'page': page_number, 'url': public_url})
            break
    return images


def parse_pdf_bytes(file_bytes, subject='', topic=''):
    page_texts = extract_page_texts(file_bytes)
    chunks = split_text_chunks(page_texts)
    images = extract_images(file_bytes)
    parsed_questions = []

    for chunk in chunks:
        prompt = build_prompt(chunk['text'])
        raw_response = call_openrouter(prompt)
        try:
            items = extract_json_array(raw_response)
        except ValueError:
            continue
        if not isinstance(items, list):
            continue

        for item in items:
            valid = validate_question_item(item)
            if not valid:
                continue
            valid['page_number'] = chunk['pages'][0] if chunk['pages'] else None
            valid['subject'] = subject
            valid['topic'] = topic
            valid['image_url'] = ''
            parsed_questions.append(valid)

    if images:
        for question in parsed_questions:
            page_number = question.get('page_number') or 1
            nearest = min(images, key=lambda image: abs(image['page'] - page_number))
            question['image_url'] = nearest['url']

    return parsed_questions
