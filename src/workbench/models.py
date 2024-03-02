from django.db import models

# Create your models here.

class Substance(models.Model):

    name = models.CharField(blank=True, max_length=250)
    image = models.ImageField(default='default.png', upload_to='substances')
    formula = models.CharField(blank=True, max_length=250)
    volume = models.IntegerField(blank=True, null=True)
    phValue = models.IntegerField(blank=True, null=True)
    molarity = models.FloatField(blank=True, null=True)
    thermal_properties = models.TextField(max_length=256, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name
    
    def __str__(self):
        return f"{self.name}"


class Apparatus(models.Model):

    class Category(models.TextChoices):
        GLASSWARE = "GLASSWARE", "Glassware"
        TOOL = "TOOL", "Tool"

    
    class Material(models.TextChoices):
        WOOD = "WOOD", "Wood"
        METAL = "METAL", "Metal"
        GLASS = "GLASS", "Glass"
        PLASTIC = "PLASTIC", "Plastic"
    
    name = models.CharField(blank=True, max_length=250)
    image = models.ImageField(default='default.png', upload_to='apparatus')
    type = models.CharField(blank=True, max_length=250)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.GLASSWARE)
    material = models.CharField(max_length=50, choices=Material.choices, default=Material.GLASS)
    volume = models.IntegerField(blank=True, null=True)
    thermal_properties = models.TextField(max_length=256, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name
    
    def __str__(self):
        return f"{self.name}"