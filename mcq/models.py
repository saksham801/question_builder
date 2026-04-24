from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=180, unique=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190)

    class Meta:
        unique_together = ('subject', 'slug')

    def __str__(self):
        return f'{self.subject.name} / {self.name}'


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    answer_key = models.CharField(max_length=2)
    explanation = models.TextField(blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    image_url = models.URLField(blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_by_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Q{self.pk} [{self.topic}]'


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=1)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('question', 'label')
        ordering = ['label']

    def __str__(self):
        return f'{self.question} {self.label}'


class Test(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    total_marks = models.PositiveIntegerField(default=100)
    created_by_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    questions = models.ManyToManyField(Question, through='TestQuestion', related_name='tests')

    def __str__(self):
        return self.title


class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('test', 'question')


class PDFUpload(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    file_name = models.CharField(max_length=255)
    source_url = models.URLField(blank=True)
    storage_bucket = models.CharField(max_length=180, blank=True)
    storage_key = models.CharField(max_length=512, blank=True)
    subject = models.CharField(max_length=180, blank=True)
    topic = models.CharField(max_length=190, blank=True)
    created_by_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parsed_json = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.file_name} ({self.status})'
