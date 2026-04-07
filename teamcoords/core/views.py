from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from .models import Project, Task, Comment, ActionLog

# --- Проекты ---

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'core/project_list.html'

    def get_queryset(self):
        return Project.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['title', 'description', 'status']
    template_name = 'core/project_form.html'
    success_url = reverse_lazy('project-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Логируем создание
        ActionLog.objects.create(
            project=self.object,
            user=self.request.user,
            action_type='project_create',
            description=f"Создан проект: {self.object.title}"
        )
        return response


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'core/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(project=self.object)
        context['all_users'] = User.objects.exclude(id=self.object.owner.id).exclude(id__in=self.object.members.all())
        # Добавляем историю проекта
        context['history'] = ActionLog.objects.filter(project=self.object).select_related('user')[:20]
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'core/project_confirm_delete.html'
    success_url = reverse_lazy('project-list')

    def test_func(self):
        return self.get_object().owner == self.request.user


def close_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user == project.owner:
        project.status = 'completed'
        project.save()
        ActionLog.objects.create(
            project=project,
            user=request.user,
            action_type='project_close',
            description="Проект закрыт"
        )
    return redirect('project-detail', pk=project.pk)


# --- Задачи ---

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'core/task_list.html'

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user) | Task.objects.filter(project__owner=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['project', 'title', 'description', 'assigned_to', 'status', 'deadline']
    template_name = 'core/task_form.html'
    success_url = reverse_lazy('task-list')

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get('project')
        if project_id:
            initial['project'] = project_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['project'].queryset = Project.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')
        if project_id:
            context['project'] = Project.objects.filter(id=project_id).first()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        ActionLog.objects.create(
            project=self.object.project,
            task=self.object,
            user=self.request.user,
            action_type='task_create',
            description=f"Создана задача: {self.object.title}"
        )
        return response

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'core/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

    def test_func(self):
        task = self.get_object()
        # ЛОГИКА ПРОВЕРКИ:
        # Разрешаем удаление только автору задачи ИЛИ владельцу проекта, к которому относится задача.

        
        # Вариант 2: Если у задачи нет поля 'author', проверяем владельца проекта
        # (удалить задачу может тот, кто владеет проектом)
        return task.project.owner == self.request.user


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    fields = ['title', 'description', 'status', 'assigned_to', 'deadline']
    template_name = 'core/task_form.html'
    success_url = reverse_lazy('task-list')

    def test_func(self):
        task = self.get_object()
        is_member = task.project.members.filter(id=self.request.user.id).exists()
        
        if task.project.is_closed:
            return False
            
        return (task.project.owner == self.request.user or 
                task.assigned_to == self.request.user or 
                is_member)

    def form_valid(self, form):
        old_status = self.get_object().status
        new_status = form.cleaned_data['status']
        
        response = super().form_valid(form)
        
        ActionLog.objects.create(
            project=self.object.project,
            task=self.object,
            user=self.request.user,
            action_type='task_update',
            description=f"Обновлена задача: {self.object.title}"
        )
        
        if old_status != new_status:
            ActionLog.objects.create(
                project=self.object.project,
                task=self.object,
                user=self.request.user,
                action_type='task_status',
                description=f"Статус изменен на: {self.object.get_status_display()}"
            )
            
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comment.objects.filter(task=self.object).order_by('created_at')
        context['project'] = self.object.project
        context['task_history'] = ActionLog.objects.filter(task=self.object).select_related('user')[:10]
        return context


# --- Функции действий ---

def add_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.user == project.owner:
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            project.members.add(user)
            # Лог moved INSIDE the if block
            ActionLog.objects.create(
                project=project,
                user=request.user,
                action_type='member_add',
                description=f"Добавлен участник: {user.username}"
            )
            
    return redirect('project-detail', pk=project.pk)


def add_comment(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    
    is_member = task.project.members.filter(id=request.user.id).exists()
    if request.user == task.project.owner or is_member:
        if request.method == 'POST':
            text = request.POST.get('text')
            file = request.FILES.get('file')
            if text or file:
                Comment.objects.create(
                    task=task,
                    author=request.user,
                    text=text,
                    file=file
                )
                # Лог moved INSIDE the permission and POST check
                ActionLog.objects.create(
                    project=task.project,
                    task=task,
                    user=request.user,
                    action_type='comment_add',
                    description=f"Добавлен комментарий"
                )
                
    return redirect('task-update', pk=task.pk)


# --- Регистрация ---

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('login')
