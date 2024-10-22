from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Course, Lesson, Question, TrueFalseQuestion, MultipleChoiceQuestion, Answer
from .serializers import CourseSerializer, LessonSerializer, QuestionSerializer, TrueFalseQuestionSerializer, MultipleChoiceQuestionSerializer, AnswerSerializer, GenerateQuestionsSerializer, GenerateReadingContentSerializer
from django.views.generic import TemplateView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import ObjectDoesNotExist
import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

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

class GenerateQuestionsView(viewsets.ViewSet):
    @swagger_auto_schema(
        method='post',
        request_body=GenerateQuestionsSerializer,
        responses={201: GenerateQuestionsSerializer()}
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = GenerateQuestionsSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['course_id']
            lesson_id = serializer.validated_data['lesson_id']
            student_interests = serializer.validated_data['student_interests']
            lesson_topic = serializer.validated_data['lesson_topic']
            num_questions = serializer.validated_data['num_questions']

            try:
                course = Course.objects.get(id=course_id)
                lesson = Lesson.objects.get(id=lesson_id, course=course)
            except Course.DoesNotExist:
                return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
            except Lesson.DoesNotExist:
                return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

            # Формируем запрос к OpenAI API
            prompt = f"Create {num_questions} one-choice questions about {lesson_topic} for a {course.title} course. "
            prompt += f"The questions should be related to the following student interests: {', '.join(student_interests)}. "
            prompt += f"For each question, provide the question text, four options, and the correct answer index (0-3). Format the response as a JSON list of {num_questions} question objects."
            prompt += "Provide the response in JSON format. like: [{'question': 'question text', 'options': ['option1', 'option2', 'option3', 'option4'], 'correct_answer_index': 0}, ...]"

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,  # Увеличиваем максимальное количество токенов
                    n=1,
                    stop=None,
                    temperature=0.7,
                )

                # Parse the response from OpenAI
                questions_data = eval(response.choices[0].message['content'].strip())

                created_questions = []
                for question_data in questions_data:
                    question = MultipleChoiceQuestion.objects.create(
                        lesson=lesson,
                        text=question_data['question'],
                        _options=question_data['options'],
                        correct_answer=question_data['options'][question_data['correct_answer_index']]
                    )
                    created_questions.append(question)

                return Response({
                    "message": f"{num_questions} questions successfully generated",
                    "questions": QuestionSerializer(created_questions, many=True).data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GenerateReadingContentView(viewsets.ViewSet):
    @swagger_auto_schema(
        method='post',
        request_body=GenerateReadingContentSerializer,
        responses={201: LessonSerializer()}
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = GenerateReadingContentSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['course_id']
            lesson_id = serializer.validated_data['lesson_id']
            student_interests = serializer.validated_data['student_interests']
            lesson_topic = serializer.validated_data['lesson_topic']

            try:
                course = Course.objects.get(id=course_id)
                lesson = Lesson.objects.get(id=lesson_id, course=course)
            except Course.DoesNotExist:
                return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
            except Lesson.DoesNotExist:
                return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

            if lesson.type != 'reading':
                return Response({"error": "This lesson is not a reading lesson"}, status=status.HTTP_400_BAD_REQUEST)

            # Формируем запрос к OpenAI API
            prompt = f"Create a detailed explanation of the topic '{lesson_topic}' for a {course.title} course. "
            prompt += f"The explanation should be tailored to a student with the following interests: {', '.join(student_interests)}. "
            prompt += "The content should be informative, engaging, and easy to understand. "
            prompt += "Structure the content with appropriate headings and subheadings. "
            prompt += "Provide the response in Markdown format."

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a knowledgeable and engaging teacher."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )

                # Получаем сгенерированный контент
                generated_content = response.choices[0].message['content'].strip()

                # Обновляем урок с новым контентом
                lesson.content = generated_content
                lesson.save()

                return Response({
                    "message": "Reading content successfully generated",
                    "lesson": LessonSerializer(lesson).data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
