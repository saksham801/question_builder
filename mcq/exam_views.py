import json
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Test, Attempt, Answer, Question
from .services.evaluator import evaluate_attempt, save_answer
from .services.pdf_generator import generate_attempt_pdf
from .services.email_sender import send_attempt_report_email
from .views import get_user_email


class StartExamView(View):
    def get(self, request, test_id):
        test = get_object_or_404(Test, pk=test_id)
        user_email = get_user_email(request)

        attempt = Attempt.objects.create(
            test=test,
            user_email=user_email,
            status='in_progress',
        )

        return redirect(reverse('exam-attempt', kwargs={'attempt_id': attempt.id}))


class ExamAttemptView(View):
    def get(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, pk=attempt_id)
        user_email = get_user_email(request)

        if attempt.user_email != user_email:
            raise PermissionDenied('You do not have access to this attempt.')

        if attempt.status != 'in_progress':
            return redirect(reverse('exam-result', kwargs={'attempt_id': attempt.id}))

        questions = attempt.test.questions.all()
        answers = {a.question_id: a for a in attempt.answers.all()}

        context = {
            'attempt': attempt,
            'test': attempt.test,
            'questions': questions,
            'answers': answers,
            'duration_minutes': attempt.test.duration_minutes,
        }
        return render(request, 'mcq/exam.html', context)


@require_http_methods(['POST'])
@csrf_exempt
def save_answer_endpoint(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    attempt_id = data.get('attempt_id')
    question_id = data.get('question_id')
    selected_option = data.get('selected_option', '').strip().upper()
    marked_for_review = data.get('marked_for_review', False)

    attempt = get_object_or_404(Attempt, pk=attempt_id)
    user_email = request.headers.get('X-User-Email', getattr(request, 'user_email', ''))

    if attempt.user_email != user_email:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    question = get_object_or_404(Question, pk=question_id)
    answer = save_answer(attempt, question, selected_option, marked_for_review)

    return JsonResponse({
        'success': True,
        'answer_id': answer.id,
        'is_correct': answer.is_correct,
    })


@require_http_methods(['POST'])
@csrf_exempt
def tab_switch_endpoint(request):
    attempt_id = request.POST.get('attempt_id')
    attempt = get_object_or_404(Attempt, pk=attempt_id)
    user_email = request.headers.get('X-User-Email', getattr(request, 'user_email', ''))

    if attempt.user_email != user_email:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt.tab_switch_count += 1
    attempt.save(update_fields=['tab_switch_count'])

    return JsonResponse({
        'success': True,
        'tab_switch_count': attempt.tab_switch_count,
    })


class SubmitExamView(View):
    def post(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, pk=attempt_id)
        user_email = get_user_email(request)

        if attempt.user_email != user_email:
            raise PermissionDenied('You do not have access to this attempt.')

        if attempt.status != 'in_progress':
            return JsonResponse({'error': 'Attempt already submitted'}, status=400)

        attempt.end_time = timezone.now()
        attempt.save(update_fields=['end_time'])

        evaluate_attempt(attempt)

        try:
            questions_with_answers = []
            for question in attempt.test.questions.all():
                answer = attempt.answers.filter(question=question).first()
                questions_with_answers.append((question, answer))

            pdf_bytes = generate_attempt_pdf(attempt, questions_with_answers)
            send_attempt_report_email(attempt, pdf_bytes)
        except Exception as exc:
            pass

        return redirect(reverse('exam-result', kwargs={'attempt_id': attempt.id}))


class ExamResultView(View):
    def get(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, pk=attempt_id)
        user_email = get_user_email(request)

        if attempt.user_email != user_email:
            raise PermissionDenied('You do not have access to this result.')

        answers = attempt.answers.select_related('question').all()
        question_review = []

        for answer in answers:
            question_review.append({
                'question': answer.question,
                'selected': answer.selected_option or '—',
                'correct': answer.question.answer_key,
                'is_correct': answer.is_correct,
                'marked_for_review': answer.marked_for_review,
            })

        context = {
            'attempt': attempt,
            'question_review': question_review,
        }
        return render(request, 'mcq/exam_result.html', context)
