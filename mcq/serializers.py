from rest_framework import serializers
from .models import PDFUpload, Question, QuestionOption, Subject, Topic, Test


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('label', 'text', 'is_correct')


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)
    topic = serializers.CharField(source='topic.name', read_only=True)
    subject = serializers.CharField(source='topic.subject.name', read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'answer_key', 'explanation', 'page_number', 'image_url', 'subject', 'topic', 'options')


class PDFUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFUpload
        fields = ('id', 'file_name', 'source_url', 'subject', 'topic', 'status', 'parsed_json', 'error_message', 'created_at', 'updated_at')
        read_only_fields = ('status', 'parsed_json', 'error_message', 'created_at', 'updated_at')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'slug')


class TopicSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = ('id', 'name', 'slug', 'subject')


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ('id', 'title', 'description', 'duration_minutes', 'total_marks')
