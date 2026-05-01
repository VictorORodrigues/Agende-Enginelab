from django.urls import path
from . import views

urlpatterns = [
    # Account activation
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
]