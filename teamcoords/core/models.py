from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('completed', 'Завершен'),
        ('frozen', 'Заморожен'),
    ]

    title = models.CharField("Название проекта", max_length=200)
    description = models.TextField("Описание", blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    members = models.ManyToManyField(User, related_name='project_members', blank=True, verbose_name="Участники")

    @property
    def is_closed(self):
        return self.status == 'completed'

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"


class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('review', 'На проверке'),
        ('done', 'Выполнено'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField("Название задачи", max_length=200)
    description = models.TextField("Описание", blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    deadline = models.DateField("Срок выполнения", null=True, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField("Комментарий", blank=True)
    file = models.FileField("Файл", upload_to='task_files/', blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Комментарий от {self.author} к {self.task}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

class ActionLog(models.Model):
    ACTION_TYPES = [
        ('project_create', 'Проект создан'),
        ('project_update', 'Проект обновлен'),
        ('project_close', 'Проект закрыт'),
        ('task_create', 'Задача создана'),
        ('task_update', 'Задача обновлена'),
        ('task_status', 'Статус задачи изменен'),
        ('comment_add', 'Комментарий добавлен'),
        ('member_add', 'Участник добавлен'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField("Тип действия", max_length=50, choices=ACTION_TYPES)
    description = models.TextField("Описание")
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Запись истории"
        verbose_name_plural = "История изменений"

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.created_at.strftime('%d.%m %H:%M')}"