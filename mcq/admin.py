from django.contrib import admin
from .models import Subject, Topic, Question, QuestionOption, Test, TestQuestion, PDFUpload, Attempt, Answer


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'answer_key', 'page_number')
    search_fields = ('text',)
    inlines = [QuestionOptionInline]


class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name', 'subject__name')


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 0


class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration_minutes', 'total_marks', 'created_at')
    inlines = [TestQuestionInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct')


class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'test', 'status', 'score', 'start_time')
    list_filter = ('status', 'test')
    search_fields = ('user_email',)
    readonly_fields = ('score', 'correct_count', 'incorrect_count', 'unattempted_count', 'accuracy_percentage')
    inlines = [AnswerInline]


@admin.register(Subject)
class RegisteredSubjectAdmin(SubjectAdmin):
    pass


@admin.register(Topic)
class RegisteredTopicAdmin(TopicAdmin):
    pass


@admin.register(Question)
class RegisteredQuestionAdmin(QuestionAdmin):
    pass


@admin.register(Test)
class RegisteredTestAdmin(TestAdmin):
    pass


@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'status', 'subject', 'topic', 'created_at')
    readonly_fields = ('parsed_json', 'error_message')


@admin.register(Attempt)
class RegisteredAttemptAdmin(AttemptAdmin):
    pass


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct')
    search_fields = ('attempt__user_email',)
