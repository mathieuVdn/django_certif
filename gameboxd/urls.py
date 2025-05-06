from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('search-games/', views.search_games, name='search-games'),
    path("games/<int:game_id>/", views.game_detail, name="game-detail"),

]
