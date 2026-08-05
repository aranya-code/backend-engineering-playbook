import os,platform
from django.shortcuts import render
def home(request):
 return render(request,"home/index.html",{"app_name":os.getenv("APP_NAME","Docker Example"),"hostname":platform.node(),"python_version":platform.python_version(),"database":os.getenv("POSTGRES_DB")})
