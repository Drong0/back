from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Course, Lesson, Question, TrueFalseQuestion, MultipleChoiceQuestion, Answer
from .serializers import CourseSerializer, LessonSerializer, QuestionSerializer, TrueFalseQuestionSerializer, MultipleChoiceQuestionSerializer, AnswerSerializer
from django.views.generic import TemplateView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import ObjectDoesNotExist

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()

    @swagger_auto_schema(
        method='post',
        request_body=LessonSerializer,
        responses={201: LessonSerializer()}
    )
    @action(detail=True, methods=['post'])
    def add_lesson(self, request, pk=None):
        """
        Add a new lesson to the course.
        """
        course = self.get_object()
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        lesson = self.get_object()
        if lesson.type != 'practice':
            return Response({"error": "Questions can only be added to practice lessons"}, status=status.HTTP_400_BAD_REQUEST)

        question_type = request.data.get('type')
        question_data = request.data.copy()

        if question_type == 'multiple_choice':
            serializer = MultipleChoiceQuestionSerializer(data=question_data)
        elif question_type == 'true_false':
            if isinstance(question_data.get('correct_answer'), bool):
                question_data['correct_answer'] = str(question_data['correct_answer']).lower()
            serializer = TrueFalseQuestionSerializer(data=question_data)
        else:
            return Response({"error": "Invalid question type"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            question = serializer.save(lesson=lesson)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().select_subclasses()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.AllowAny]

class CreateCourseView(TemplateView):
    template_name = 'courses/create_course.html'
