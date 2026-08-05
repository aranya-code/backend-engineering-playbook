from django.shortcuts import render,redirect
from .tasks import long_running_task
def home(request):
    return render(request,"home/index.html")
def run_task(request):
    long_running_task.delay()
    return redirect("/")
