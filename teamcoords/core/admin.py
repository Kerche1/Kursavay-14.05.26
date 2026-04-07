from django.contrib import admin
from .models import Project, Task

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at')
    inlines = [TaskInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'assigned_to', 'deadline')
    list_filter = ('status', 'project')
    search_fields = ('title', 'description')