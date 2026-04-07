from django.urls import path
from . import views

urlpatterns = [
    # Проекты
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project-create'),
    
    # Задачи
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('task/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('task/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task-update'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('project/<int:pk>/add-member/', views.add_member, name='add-member'),
    path('task/<int:task_pk>/add-comment/', views.add_comment, name='add-comment'),
    path('project/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('project/<int:pk>/close/', views.close_project, name='project-close'),
]