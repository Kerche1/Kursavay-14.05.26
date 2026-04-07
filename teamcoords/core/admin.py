from django.contrib import admin
from .models import Project, Task, Comment, ActionLog

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    # Опционально: можно скрыть часть полей во встроенной форме, чтобы она была компактнее
    # fields = ('title', 'status', 'assigned_to', 'deadline')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at')
    list_filter = ('status',)
    inlines = [TaskInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'assigned_to', 'deadline')
    list_filter = ('status', 'project')
    search_fields = ('title', 'description')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at', 'text_short')
    list_filter = ('created_at',)
    search_fields = ('text',)

    # Вспомогательный метод, чтобы длинный текст не ломал верстку админки
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Текст комментария'

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'action_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    # Делаем поля только для чтения, так как историю нельзя редактировать вручную
    readonly_fields = ('project', 'task', 'user', 'action_type', 'description', 'created_at')

    def has_add_permission(self, request):
        return False # Запрещаем создавать логи вручную через админку

    def has_delete_permission(self, request, obj=None):
        return False # Запрещаем удалять логи
