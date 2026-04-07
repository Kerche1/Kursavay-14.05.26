from django import forms
from .models import Project, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # Мы перечисляем только те поля, которые нужно видеть на экране.
        # Поле 'status' сюда НЕ добавляем, чтобы оно использовало default='active' из models.py автоматически.
        fields = ['title', 'description', 'members']
        
        # Можно добавить виджеты для красоты (опционально)
        widgets = {
            'members': forms.CheckboxSelectMultiple(),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'status', 'assigned_to', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }
