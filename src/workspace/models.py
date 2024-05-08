import os
from django.db import models
from django.contrib.postgres.fields import ArrayField
from src.users.models import User
from src.workbench.models import Apparatus, Substance
from django.core.exceptions import ValidationError


# Create your models here.
def validate_svg(file):
    # Check if the content type of the file is SVG
    if not file.content_type == 'image/svg+xml':
        raise ValidationError('Unsupported file type. Only SVG files are allowed.')
    
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path & filename
    valid_extensions = ['.svg'] # populate with the extensions that you allow / want
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

# Create your models here.
class Lesson(models.Model):

    title = models.CharField(blank=True, max_length=250)
    image = models.FileField(default='default.png', upload_to='lessons', validators=[validate_file_extension])
    description = models.TextField()
    instructor = models.ForeignKey(User,  blank=True, null=True, on_delete=models.CASCADE)
    video_file = models.FileField(upload_to='videos/') 
    # student = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    instructions = models.TextField(blank=True, max_length=5000)
    tools = models.ManyToManyField(Apparatus)
    substances = models.ManyToManyField(Substance)
    parameters = models.CharField(blank=True, max_length=250)
    procedure = models.JSONField(null=True, default=dict)

    def __unicode__(self):
        return u'%s' % self.title
    
    def __str__(self):
        return f"{self.title}"

class LessonSession(models.Model):
    id = models.UUIDField(primary_key=True, verbose_name='session_id')
    lesson = models.ForeignKey('Lesson', related_name='sessions', on_delete=models.CASCADE)
    student = models.ForeignKey(User, related_name='student',on_delete=models.CASCADE)

    def __unicode__(self):
        return u'%s' % self.title
    
    def __str__(self):
        return f"{self.title}"
    

class Reaction(models.Model):
    substance = models.JSONField()
    volume = models.JSONField()

    def __str__(self):
        return f"{self.substance} - {self.volume} mL"
    

class TitrationExperiment(models.Model):
    initial_solution_volume = models.FloatField()
    titrant_concentration = models.FloatField()
    initial_solution_concentration = models.FloatField()
    total_titrant_volume = models.FloatField(null=True, blank=True)
    final_solution_volume = models.FloatField(null=True, blank=True)
    final_solution_concentration = models.FloatField(null=True, blank=True)

class Exercise(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='exercises', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"Exercise: {self.title}"

class Question(models.Model):
    exercise = models.ForeignKey(Exercise, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=50)  # e.g., 'multiple_choice', 'fill_in_the_blank'
    correct_answer = models.TextField(blank=True, null=True)  # Use for fill-in-the-blank or other open-ended questions

    def __str__(self):
        return f"Question: {self.text[:50]}..."

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Option: {self.text}"

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    submission_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'exercise')

class Answer(models.Model):
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, blank=True, null=True)  # For multiple-choice
    text_answer = models.TextField(blank=True, null=True)  # For open-ended questions

    def __str__(self):
        if self.selected_option:
            return f"Selected Option: {self.selected_option.text}"
        return f"Answer: {self.text_answer}"
