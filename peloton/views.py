from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Team, Rider, Race, RaceResult

def index(request):
    team_count = Team.objects.count()
    rider_count = Rider.objects.count()
    return render(request, 'peloton/index.html', {
        'team_count': team_count,
        'rider_count': rider_count,
    })

# This view handles the GET request when a user visits /teams/
# It fetches all teams from the database and sends them to the template

# ALL TEAMS
def all_teams(request):

    # Go to the database and get ALL team records
    teams = Team.objects.all()

    # Send the teams data to the template to be displayed
    return render(request, 'peloton/teams.html', {'teams': teams})

# This view handles when a user clicks ona specific team
# It fetches ONE team from the database using its id

# TEAM DETAILS
def team_detail(request, pk):
    team = get_object_or_404(
        Team.objects.prefetch_related('riders'), pk=pk)
    return render(request, 'peloton/team_detail.html', {'team': team})
   

# This view handles the GET request when a user visits/riders/
# It fetches all riders orderd by team then last name

# ALL RIDERS
def all_riders(request):
    riders = Rider.objects.select_related('team').prefetch_related('specialties').order_by('team__name', 'last_name')
    return render(request, 'peloton/riders.html', {'riders': riders})

# This view handles when a user clicks on a specific rider
# It fetches ONE rider from the database using its id

# RIDER DETAILS
def rider_detail(request, pk):
    rider = get_object_or_404(
        Rider.objects.select_related('team').prefetch_related('specialties'), pk=pk)
    return render(request, 'peloton/rider_detail.html', {'rider': rider})



#***********************
# RACE PODIUM
#***********************
def race_results(request, pk):
    race = get_object_or_404(Race, pk=pk)

    results = RaceResult.objects.filter(
        race=race,
        

    ).select_related(
        'rider',
        'rider__team',
    ).order_by('finishing_position')

    return render(request, 'peloton/race_results.html', {
        'race': race,
        'results': results,
    })

# ALL RACES
def all_races(request):
    races = Race.objects.all()
    return render(request, 'peloton/races.html', {'races': races,})