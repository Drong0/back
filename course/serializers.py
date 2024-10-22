from rest_framework import serializers
from .models import Course, Lesson, Question, TrueFalseQuestion, MultipleChoiceQuestion, Answer
from model_utils.managers import InheritanceManager

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']

class TrueFalseQuestionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = TrueFalseQuestion
        fields = ['id', 'text', 'type', 'correct_answer']

    def get_type(self, obj):
        return 'true_false'

class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    options = serializers.ListField(source='_options')

    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'text', 'type', 'options', 'correct_answer']

    def get_type(self, obj):
        return 'multiple_choice'


class QuestionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'type', 'options', 'correct_answer']

    def get_type(self, obj):
        if isinstance(obj, TrueFalseQuestion):
            return 'true_false'
        elif isinstance(obj, MultipleChoiceQuestion):
            return 'multiple_choice'
        return 'unknown'

    def get_options(self, obj):
        if isinstance(obj, MultipleChoiceQuestion):
            return obj._options
        return None

    def get_correct_answer(self, obj):
        if isinstance(obj, TrueFalseQuestion):
            return obj.correct_answer
        elif isinstance(obj, MultipleChoiceQuestion):
            return obj.correct_answer
        return None

class LessonSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'type', 'content', 'video_url', 'questions']

    def get_questions(self, obj):
        questions = obj.questions.select_subclasses()
        return QuestionSerializer(questions, many=True).data

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'author', 'lessons']

class GenerateQuestionsSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    lesson_id = serializers.IntegerField()
    student_interests = serializers.ListField(child=serializers.CharField())
    lesson_topic = serializers.CharField()
    num_questions = serializers.IntegerField(min_value=1, max_value=10, default=1)

class GenerateReadingContentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    lesson_id = serializers.IntegerField()
    student_interests = serializers.ListField(child=serializers.CharField())
    lesson_topic = serializers.CharField()
