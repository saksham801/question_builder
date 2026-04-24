from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.PDFUploadCreateView.as_view(), name='pdf-upload-create'),
    path('upload/<int:pk>/', views.PDFUploadDetailView.as_view(), name='pdf-upload-detail'),
    path('upload/<int:pk>/save/', views.SaveParsedQuestionsView.as_view(), name='save-parsed-questions'),
    path('questions/', views.QuestionListView.as_view(), name='question-list'),
    path('tests/', views.TestCreateView.as_view(), name='test-create'),
]
