from django.db import models

from src.users.models import User
from src.workbench.models import Apparatus, Substance

# Create your models here.
class Lesson(models.Model):

    title = models.CharField(blank=True, max_length=250)
    instructor = models.ForeignKey(User,  blank=True, null=True, on_delete=models.CASCADE)
    # student = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    instructions = models.TextField(blank=True, max_length=5000)
    tools = models.ManyToManyField(Apparatus)
    substances = models.ManyToManyField(Substance)
    parameters = models.CharField(blank=True, max_length=250)
    
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


# class Apparatus(models.Model):

    
#     name = models.CharField(blank=True, max_length=250)
#     type = models.CharField(blank=True, max_length=250)
#     category = models.CharField(max_length=50, choices=Category.choices, default=Category.GLASSWARE)
#     material = models.CharField(max_length=50, choices=Material.choices, default=Material.GLASS)
#     volume = models.IntegerField(max_length=1000, blank=True, null=True)
#     thermal_properties = models.TextField(max_length=256, blank=True, null=True)



class Procedure(models.Model):
    step_id = models.PositiveSmallIntegerField(blank=False, null=True)
    instruction = models.TextField(max_length=100, blank=False, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, related_name='Steps')