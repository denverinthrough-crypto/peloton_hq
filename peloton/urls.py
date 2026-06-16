from django.urls import path
from . import views


urlpatterns = [

    path('', views.index, name='index'),

    # when user visits /teams/ -> call teams_view
    path('teams/', views.all_teams, name='all_teams'),

    #<pk> captures the team id from the URL e.g. /teams/1/
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),

    # Rider URLs
    path('riders/', views.all_riders, name='all_riders'),

    path('riders/<int:pk>/', views.rider_detail, name='rider_detail'),

    path('races/<int:pk>/results/', views.race_results, name='race_results'),

    path('races/', views.all_races, name='all_races'),
]