from django.db import models

from src.users.models import User
from src.workbench.models import Apparatus, Substance

# Create your models here.
class Lesson(models.Model):

    title = models.CharField(blank=True, max_length=250)
    description = models.TextField()
    instructor = models.ForeignKey(User,  blank=True, null=True, on_delete=models.CASCADE)
    video_file = models.FileField(upload_to='videos/') 
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


# class Apparatus(models.Model):

    
#     name = models.CharField(blank=True, max_length=250)
#     type = models.CharField(blank=True, max_length=250)
#     category = models.CharField(max_length=50, choices=Category.choices, default=Category.GLASSWARE)
#     material = models.CharField(max_length=50, choices=Material.choices, default=Material.GLASS)
#     volume = models.IntegerField(max_length=1000, blank=True, null=True)
#     thermal_properties = models.TextField(max_length=256, blank=True, null=True)