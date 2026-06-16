from django.db import models 

from datetime import date


# Create your models here.

# This model represents a professional cycling team in the Tour de France
# Each team has a name, nationality, and the brand of the bike they ride.

class Team(models.Model):

    # The full official name of the team
    # e.g "Team Visma | Lease a Bike"
    name = models.CharField(max_length=100)

    # The country the team is registered in
    country = models.CharField(max_length=50)

    #The brand of bike the team uses
    bike_brand = models.CharField(max_length=50)

    #This controls how the team object displays
    #when printed or shownin the admin panel
    def __str__(self):
        return self.name
    
#******************************
# SPECIALTY MODEL
# Represents a riding specialty or role.
# Stored separately so riders can have
# multiple specialties (ManyToMany).
#******************************
class Specialty(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Specialties" # Fixes Django admin showing "Specialties"


 #*******************
 # RIDER MODEL
 # Represents a professional cyclist
 # Linked to oen Team via ForeignKey.
 # Linked to many Specialties via ManyToMany.
 # ******************
   
class Rider(models.Model):
    # ── Relationships ──────────────────────
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,       # If team is deleted, all its riders are deleted too
        related_name='riders'           # Lets us call team.riders.all() in templates
    )
    specialties = models.ManyToManyField(
        Specialty,
        blank=True,                     # A rider can have zero specialties (optional)
        related_name='riders'           # Lets us call specialty.riders.all() later
    )

    # ── Personal Info ───────────────────────
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    nationality = models.CharField(max_length=50)
    date_of_birth = models.DateField()              # We compute age from this, never store age directly

    # ── Physical Stats ──────────────────────
    height = models.DecimalField(max_digits=4, decimal_places=2)   # In metres e.g. 1.78
    weight = models.DecimalField(max_digits=5, decimal_places=2)   # In kg e.g. 73.50

    is_active = models.BooleanField(default=True)

    # ── Computed Properties ─────────────────
    @property
    def full_name(self):
        # Combines first and last name for display everywhere in templates
        return f"{self.first_name} {self.last_name}"


    
    @property
    def age(self):
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    @property
    def bmi(self):
        # Body Mass Index - useful later for ML weight-to-power ratio analysis
        if self.height:
            return round(float(self.weight) / (float(self.height) ** 2), 1)
        return None
    
    def __str__(self):
        return self.full_name
    

#**************************
# RIDER PROFILE MODEL
# Numerical attributes used by the simulation engine.
# OneToOne → Rider (one profile per rider, always)
#**************************
class RiderProfile(models.Model):
    rider = models.OneToOneField(
        Rider,
        on_delete=models.CASCADE,
        related_name='profile' # lets us call rider.profile.sprint in templates
    )

    # Skill scores - all 0 to 100
    sprint = models.IntegerField(default=0) # flat sprint finish ability
    climbing = models.IntegerField(default=0) # mountain climbing ability
    hills = models.IntegerField(default= 0)
    one_day_races = models.IntegerField(default=0)
    time_trial = models.IntegerField(default=0)
    cobbles = models.IntegerField(default=0) # 0-100, cobbled classics specialist abilites
    ftp = models.IntegerField(null=True, blank=True) # watts
    endurance = models.IntegerField(default=70) # 0-100, how well rider sustains pace over distance

    def __str__(self):
        return f"{self.rider.full_name} - Profile"
    
    @property
    def watts_per_kg(self):
        if self.ftp and self.rider.weight:
            return round(self.ftp / float(self.rider.weight), 2)
        return None
  


#**************************
# RACE MODEL
# *************************
class Race(models.Model):
    RACE_TYPE_CHOICES = [
        ('GT', 'Grand Tour'),
        ('MON', 'Monument'),
        ('OW', 'One Week Race'),
    ]  

    TERRAIN_TYPE_CHOICES = [
        ('FL', 'Flat'),
        ('HI', 'Hilly'),
        ('MT', 'Mountain'),
    ]

    MONUMENT_CHOICES = [
        ('PR', 'Paris-Roubaix'),
        ('RVV', 'Ronde van Vlaanderen'),
        ('LBL', 'Liège-Bastogne-Liège'),
        ('MSR', 'Milan-San Remo'),
        ('LOM', 'Il Lombardia')
    ]

    GRAND_TOUR_CHOICES = [
        ('TDF', 'Tour de France'),
        ('GIR', 'Giro d\'Italia'),
        ('VUE', 'La Vuelta'),
    ]

    name = models.CharField(max_length=100, null=True, blank=True)
    year = models.IntegerField()
    country = models.CharField(max_length=50)
    race_type = models.CharField(max_length=10, choices=RACE_TYPE_CHOICES)
    monument_name = models.CharField(
        max_length=10,
        choices=MONUMENT_CHOICES,
        null=True,
        blank=True
    )
    grand_tour_name = models.CharField(
        max_length=10,
        choices=GRAND_TOUR_CHOICES,
        null=True,
        blank=True
    )
    
    total_stages = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Parcours profile = mainly for Monuments
    terrain_type = models.CharField(
        max_length=10,
        choices=TERRAIN_TYPE_CHOICES,
        null=True,
        blank=True
    )
    has_cobbles = models.BooleanField(default=False)
    has_steep_climbs = models.BooleanField(default=False)
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True
    )

    WEATHER_CHOICES = [
        ('dry', 'Dry'),
        ('rain', 'Rain'),
        ('wind', 'Wind'),
        ('heat', 'Heat'),
        ('cold', 'Cold'),
    ]

    RACE_STYLE_CHOICES = [
        ('bunch_sprint', 'Bunch Sprint'),
        ('breakaway', 'Solo Breakaway'),
        ('gc_battle', 'GC Battle'),
    ]

    weather = models.CharField(
        max_length = 10,
        choices = WEATHER_CHOICES,
        default = 'dry'
    )

    race_style = models.CharField(
        max_length = 20,
        choices = RACE_STYLE_CHOICES,
        default = 'breakaway'
    )



    def __str__(self):
        if self.race_type == 'MON' and self.monument_name:
            return f"{self.get_monument_name_display()} {self.year}"
        elif self.race_type == 'GT' and self.grand_tour_name:
            return f"{self.get_grand_tour_name_display()} {self.year}"
        return f"{self.name} {self.year}"
    
    class Meta:
        ordering = ['-year', 'name']


#**************************
# STAGE MODEL
# *************************
class Stage(models.Model):
    STAGE_TYPE_CHOICES = [
        ('FL', 'Flat'),
        ('HI', 'Hilly'),
        ('MT', 'Mountain'),
        ('IT', 'Individual Time Trial'),
        ('TT', 'Team Time Trial'),
    ]

    STAGE_STATUS_CHOICES = [
        ('NR', 'Normal'),
        ('CA', 'Cancelled'),
        ('SH', 'Shortened'),
    ]

    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='stages'
    )

    stage_number = models.IntegerField()
    name = models.CharField(max_length=100)
    distance_km = models.DecimalField(max_digits=6, decimal_places=1)
    stage_type = models.CharField(max_length=10, choices=STAGE_TYPE_CHOICES)
    stage_status = models.CharField(
        max_length=10,
        choices=STAGE_STATUS_CHOICES,
        default='NR'
    )
    departure = models.CharField(max_length=100)
    arrival = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.race} - Stage {self.stage_number}: {self.name}"
    
    class Meta:
        ordering = ['race', 'stage_number']

#**************************
# STAGE RESULT MODEL
# *************************
class StageResult(models.Model):
    FINISH_STATUS_CHOICES = [
        ('FIN', 'Finished'),
        ('DNF', 'Did Not Finished'),
        ('DNS', 'Did Not Start'),
        ('DSQ', 'Disqualified'),
    ]

    stage = models.ForeignKey(
        Stage,
        on_delete = models.CASCADE,
        related_name='results'
    )
    rider = models.ForeignKey(
        Rider,
        on_delete=models.CASCADE,
        related_name='stage_results'
    )
    finishing_position = models.IntegerField(null=True, blank=True)
    finish_status = models.CharField(
        max_length=10,
        choices=FINISH_STATUS_CHOICES,
        default='FIN'
    )
    time_in_seconds = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.rider} - {self.stage} - {self.finish_status}"
    
    @property
    def formatted_time(self):
        if self.time_in_seconds is None:
            return None
        hours = self.time_in_seconds // 3600
        minutes = (self.time_in_seconds % 3600) // 60
        seconds = self.time_in_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    class Meta:
        ordering = ['stage', 'finishing_position']
        unique_together = ['stage', 'rider']

#**************************
# RACE RESULT MODEL (Monuments)
# *************************
class RaceResult(models.Model):

    FINISH_STATUS_CHOICES = [
        ('FIN', 'Finished'),
        ('DNF', 'Did Not Finished'),
        ('DNS', 'Did Not Start'),
        ('DSQ', 'Disqualified'),
    ]

    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='results'

    )
    rider = models.ForeignKey(
        Rider,
        on_delete=models.CASCADE,
        related_name='race_results'
    )
    finishing_position = models.IntegerField(null=True, blank=True)
    finish_status = models.CharField(
        max_length=10,
        choices=FINISH_STATUS_CHOICES,
        default='FIN'
    )
    time_in_seconds = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.rider} - {self.race} - P{self.finishing_position}"
    
    @property
    def formatted_time(self):
        if self.time_in_seconds is None:
            return None
        hours = self.time_in_seconds // 3600
        minutes = (self.time_in_seconds % 3600) // 60
        seconds = self.time_in_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def time_gap(self):
        if self.time_in_seconds is None:
            return None
        winner = RaceResult.objects.filter(
            race=self.race,
            finishing_position=1
        ).first()
        if winner is None or winner.time_in_seconds is None:
            return None
        gap = self.time_in_seconds - winner.time_in_seconds
        if gap == 0:
            return "Winner" if self.finishing_position == 1 else "s.t."
        minutes = gap // 60
        seconds = gap % 60
        return f"+{minutes:02d}:{seconds:02d}"
    
    class Meta:
        ordering = ['race', 'finishing_position']
        unique_together = ['race', 'rider']


#**************************
# SIMULATION CONFIG MODEL
# Lookup table for simulator.py.
# One row per terrain type.
# Lets us tune simulation from admin
# instead of hardcoding values in the script.
#**************************
class SimulationConfig(models.Model):
    TERRAIN_TYPE_CHOICES = [
        ('FL', 'Flat'),
        ('HI', 'Hilly'),
        ('MT', 'Mountain'),
        ('TT', 'Time Trial'),
    ]

    terrain_type = models.CharField(
        max_length = 10,
        choices = TERRAIN_TYPE_CHOICES,
        unique = True # one config row per terrain type
    )

    base_speed_kmh = models.FloatField() # avg race speed for this terrain
    seconds_per_score_point = models.IntegerField(default=4)
    endurance_weight = models.FloatField(default=0.3)
    cobble_weight = models.FloatField(default=0.3)

    def __str__(self):
        return f"SimConfig: {self.get_terrain_type_display()} - {self.base_speed_kmh} km/h"