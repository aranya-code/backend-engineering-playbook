from django.urls import path
from .views import home,run_task
urlpatterns=[path("",home),path("run-task/",run_task)]
