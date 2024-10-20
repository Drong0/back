import json
from django.db import models
from model_utils.managers import InheritanceManager

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    LESSON_TYPES = [
        ('practice', 'Practice'),
        ('reading', 'Reading'),
        ('video', 'Video'),
    ]
    
    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=LESSON_TYPES)
    content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Question(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()

    objects = InheritanceManager()

    def __str__(self):
        return self.text

class TrueFalseQuestion(Question):
    correct_answer = models.BooleanField()

class MultipleChoiceQuestion(Question):
    _options = models.JSONField()
    correct_answer = models.TextField()  # This will store comma-separated correct answers

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        self._options = value

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
