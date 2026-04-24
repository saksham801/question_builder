from django.urls import path
from . import views
from . import exam_views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.PDFUploadCreateView.as_view(), name='pdf-upload-create'),
    path('upload/<int:pk>/', views.PDFUploadDetailView.as_view(), name='pdf-upload-detail'),
    path('upload/<int:pk>/save/', views.SaveParsedQuestionsView.as_view(), name='save-parsed-questions'),
    path('questions/', views.QuestionListView.as_view(), name='question-list'),
    path('tests/', views.TestCreateView.as_view(), name='test-create'),
    path('exam/start/<int:test_id>/', exam_views.StartExamView.as_view(), name='start-exam'),
    path('exam/attempt/<int:attempt_id>/', exam_views.ExamAttemptView.as_view(), name='exam-attempt'),
    path('exam/save-answer/', exam_views.save_answer_endpoint, name='save-answer'),
    path('exam/tab-switch/', exam_views.tab_switch_endpoint, name='tab-switch'),
    path('exam/submit/<int:attempt_id>/', exam_views.SubmitExamView.as_view(), name='submit-exam'),
    path('exam/result/<int:attempt_id>/', exam_views.ExamResultView.as_view(), name='exam-result'),
]
