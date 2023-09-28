from django.contrib import admin
from src.workspace.models import *

# Register your models here.

class ProcedureTabularInline(admin.TabularInline):
    model = Procedure
    extra = 0
class LessonAdmin(admin.ModelAdmin):
    inlines = [
        ProcedureTabularInline
    ]


admin.site.register(Lesson, LessonAdmin)