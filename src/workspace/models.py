from django.db import models

from src.users.models import User
from src.workbench.models import Apparatus, Substance

# Create your models here.
class Lesson(models.Model):

    title = models.CharField(blank=True, max_length=250)
    instructor = models.ForeignKey(User,  blank=True, null=True, on_delete=models.CASCADE)
    # student = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    tools = models.ManyToManyField(Apparatus)
    substances = models.ManyToManyField(Substance)

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