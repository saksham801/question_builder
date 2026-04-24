import json
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views import View
from .forms import PDFUploadForm, SaveParsedQuestionsForm, TestCreateForm
from .models import PDFUpload, Subject, Topic, Question, QuestionOption, Test
from .services.storage import upload_pdf_file
from .tasks import process_pdf_upload_task


def get_user_email(request):
    user_email = getattr(request, 'user_email', '')
    if not user_email:
        if settings.DEBUG:
            # In development, use a default email for testing
            return 'test@example.com'
        raise PermissionDenied('Authentication required to perform this action.')
    return user_email


class DashboardView(View):
    def get(self, request):
        uploads = PDFUpload.objects.order_by('-created_at')[:8]
        questions = Question.objects.order_by('-created_at')[:8]
        tests = Test.objects.order_by('-created_at')[:8]
        context = {
            'uploads': uploads,
            'questions': questions,
            'tests': tests,
        }
        return render(request, 'mcq/dashboard.html', context)


class PDFUploadCreateView(View):
    def get(self, request):
        form = PDFUploadForm()
        return render(request, 'mcq/upload.html', {'form': form})

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'mcq/upload.html', {'form': form})

        pdf_file = form.cleaned_data['pdf_file']
        subject = form.cleaned_data['subject'].strip()
        topic = form.cleaned_data['topic'].strip()
        user_email = get_user_email(request)

        try:
            storage_key, public_url = upload_pdf_file(pdf_file)
        except Exception as exc:
            messages.error(request, f'Unable to upload PDF: {exc}')
            return render(request, 'mcq/upload.html', {'form': form})

        upload = PDFUpload.objects.create(
            file_name=pdf_file.name,
            source_url=public_url,
            storage_bucket=settings.SUPABASE_STORAGE_PDF_BUCKET,
            storage_key=storage_key,
            subject=subject,
            topic=topic,
            created_by_email=user_email,
            status='pending',
        )
        process_pdf_upload_task.delay(upload.id)
        messages.success(request, 'PDF uploaded successfully. Processing has started in the background.')
        return redirect(reverse('pdf-upload-detail', kwargs={'pk': upload.id}))


class PDFUploadDetailView(View):
    def get(self, request, pk):
        upload = get_object_or_404(PDFUpload, pk=pk)
        form = SaveParsedQuestionsForm(initial={'parsed_json': json.dumps(upload.parsed_json)})
        context = {
            'upload': upload,
            'form': form,
        }
        return render(request, 'mcq/preview.html', context)


class SaveParsedQuestionsView(View):
    def post(self, request, pk):
        upload = get_object_or_404(PDFUpload, pk=pk)
        form = SaveParsedQuestionsForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Unable to save the parsed questions. Please try again.')
            return redirect(reverse('pdf-upload-detail', kwargs={'pk': upload.pk}))

        parsed_questions = form.cleaned_data['parsed_json']
        user_email = get_user_email(request)
        subject_name = upload.subject or 'General'
        topic_name = upload.topic or 'General'

        subject, _ = Subject.objects.get_or_create(
            name=subject_name,
            defaults={'slug': slugify(subject_name) or 'subject'},
        )
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            name=topic_name,
            defaults={'slug': slugify(topic_name) or 'topic'},
        )

        created_count = 0
        for item in parsed_questions:
            answer = item.get('answer', '').strip().upper()
            options = item.get('options', {})
            if not answer or answer not in ['A', 'B', 'C', 'D'] or len(options) != 4:
                continue

            question = Question.objects.create(
                topic=topic,
                text=item.get('question', '').strip(),
                answer_key=answer,
                page_number=item.get('page_number'),
                image_url=item.get('image_url', ''),
                raw_data=item,
                created_by_email=user_email,
            )
            for label in ['A', 'B', 'C', 'D']:
                QuestionOption.objects.create(
                    question=question,
                    label=label,
                    text=options.get(label, '').strip(),
                    is_correct=(label == answer),
                )
            created_count += 1

        messages.success(request, f'Saved {created_count} questions to the database under {subject_name} / {topic_name}.')
        return redirect(reverse('question-list'))


class QuestionListView(View):
    def get(self, request):
        questions = Question.objects.order_by('-created_at')[:100]
        return render(request, 'mcq/question_list.html', {'questions': questions})


class TestCreateView(View):
    def get(self, request):
        questions = Question.objects.order_by('-created_at')[:200]
        form = TestCreateForm(questions=questions)
        return render(request, 'mcq/test_builder.html', {'form': form, 'questions': questions})

    def post(self, request):
        questions = Question.objects.order_by('-created_at')[:200]
        form = TestCreateForm(request.POST, questions=questions)
        if not form.is_valid():
            return render(request, 'mcq/test_builder.html', {'form': form, 'questions': questions})

        test = Test.objects.create(
            title=form.cleaned_data['title'].strip(),
            description=form.cleaned_data['description'].strip(),
            duration_minutes=form.cleaned_data['duration_minutes'],
            total_marks=form.cleaned_data['total_marks'],
            created_by_email=get_user_email(request),
        )
        test.questions.set(form.cleaned_data['question_ids'])
        messages.success(request, f'Test "{test.title}" created successfully with {test.questions.count()} questions.')
        return redirect(reverse('test-create'))
