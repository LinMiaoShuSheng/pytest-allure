from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('allure/<personal_dir>', csrf_exempt(views.get_allure))
]
