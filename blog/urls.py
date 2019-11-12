from django.urls import path
from . import views
urlpatterns = [
        path('', views.post_detail, name='index'),
        path('index.html', views.post_detail, name='index'),
        path('<str:acao>/fronteira_eficiente', views.carrega_dados, name='carrega_dados'),
]
