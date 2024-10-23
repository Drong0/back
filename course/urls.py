from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonViewSet, GenerateQuestionsView, GenerateReadingContentView, CoursesMyView, CoursesByIDView 


router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'generate-questions', GenerateQuestionsView, basename='generate-questions')
router.register(r'generate-reading', GenerateReadingContentView, basename='generate-reading')

urlpatterns = [
    path('', include(router.urls)),
    path('course/my/', CoursesMyView.as_view(), name='courses-my'),
    path('course/<int:pk>/', CoursesByIDView.as_view(), name='courses-by-id'),
]
