from decimal import Decimal
from django.utils import timezone
from .models import Attempt, Answer


def evaluate_attempt(attempt):
    """
    Evaluate an attempt and calculate scores.
    JEE scoring: +4 for correct, -1 for incorrect, 0 for unattempted.
    """
    answers = attempt.answers.select_related('question').all()
    total_q = attempt.test.questions.count()
    correct = 0
    incorrect = 0
    unattempted = 0
    total_score = Decimal('0')

    for answer in answers:
        if not answer.selected_option:
            unattempted += 1
        elif answer.is_correct:
            correct += 1
            total_score += Decimal('4')
        else:
            incorrect += 1
            total_score -= Decimal('1')

    if total_q > correct + incorrect:
        unattempted = total_q - (correct + incorrect)

    accuracy = Decimal('0')
    if correct + incorrect > 0:
        accuracy = (Decimal(correct) / Decimal(correct + incorrect)) * Decimal('100')

    attempt.score = total_score
    attempt.correct_count = correct
    attempt.incorrect_count = incorrect
    attempt.unattempted_count = unattempted
    attempt.accuracy_percentage = accuracy
    attempt.total_questions = total_q
    if attempt.end_time and attempt.start_time:
        attempt.time_taken_minutes = int((attempt.end_time - attempt.start_time).total_seconds() / 60)
    attempt.status = 'submitted'
    attempt.save(update_fields=[
        'score', 'correct_count', 'incorrect_count', 'unattempted_count',
        'accuracy_percentage', 'total_questions', 'time_taken_minutes', 'status'
    ])

    return attempt


def save_answer(attempt, question, selected_option, marked_for_review=False):
    """
    Save or update an answer during the exam.
    """
    is_correct = selected_option == question.answer_key if selected_option else False
    answer, created = Answer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'selected_option': selected_option,
            'is_correct': is_correct,
            'marked_for_review': marked_for_review,
        }
    )
    return answer
