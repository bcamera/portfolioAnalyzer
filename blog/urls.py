# from django.urls import path
# from . import views
# urlpatterns = [
#         path('', views.post_detail, name='index'),
#         path('index.html', views.post_detail, name='index'),
#         path('<str:acao>/fronteira_eficiente', views.carrega_dados, name='carrega_dados'),
# ]


# blog/urls.py (configuração corrigida)
# from django.urls import path
# from . import views

# urlpatterns = [
#     # A URL vazia deve apontar para a lista de posts
#     path('', views.post_list, name='post_list'),
#     # A URL de detalhes deve incluir o PK
#     path('post/<int:pk>/', views.post_detail, name='post_detail'),
#     path('<str:acao>/fronteira_eficiente', views.carrega_dados, name='carrega_dados'),
# ]

# blog/urls.py (configuração corrigida)
from django.urls import path
from . import views

urlpatterns = [
    # A URL vazia agora aponta para a nova view 'home'
    path('', views.home, name='home'),
    # As outras URLs permanecem as mesmas
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('index.html', views.home, name='index'),
    path('<str:acao>/fronteira_eficiente', views.carrega_dados, name='carrega_dados'),
]