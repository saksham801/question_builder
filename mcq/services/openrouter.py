import hashlib
import json
import time
from django.conf import settings
import redis
import requests

# Redis client will be created lazily
_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

RATE_LIMIT_KEY = 'openrouter:request_count'
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_REQUESTS = 18


def _get_cache_key(prompt: str) -> str:
    return 'openrouter:cache:' + hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def _acquire_slot():
    client = get_redis_client()
    current = client.incr(RATE_LIMIT_KEY)
    if current == 1:
        client.expire(RATE_LIMIT_KEY, RATE_LIMIT_WINDOW_SECONDS)
    if current > RATE_LIMIT_REQUESTS:
        sleep_for = 2
        time.sleep(sleep_for)
        return _acquire_slot()
    return True


def call_openrouter(prompt: str, max_retries: int = 4) -> str:
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is missing')

    client = get_redis_client()
    cached = client.get(_get_cache_key(prompt))
    if cached:
        return cached

    delay = 2
    for attempt in range(1, max_retries + 1):
        _acquire_slot()
        response = requests.post(
            'https://openrouter.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.OPENROUTER_MODEL,
                'messages': [
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
            },
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            client = get_redis_client()
            client.set(_get_cache_key(prompt), content, ex=86400)
            return content

        if response.status_code == 429:
            time.sleep(delay)
            delay *= 2
            continue

        if response.status_code >= 500:
            time.sleep(delay)
            delay *= 2
            continue

        response.raise_for_status()

    raise RuntimeError('OpenRouter request failed after retries')


def normalize_ai_json(raw_text: str) -> dict:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError('AI response is not valid JSON')
