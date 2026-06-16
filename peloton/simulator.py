import random
from .models import RaceResult, SimulationConfig

WEATHER_MODIFIERS = {
    'dry': 0.0,
    'rain': -1.5,
    'wind': -2.5,
    'heat': -1.0,
    'cold': -0.5,
}

def get_weather_modifier(weather):
    return WEATHER_MODIFIERS.get(weather, 0.0)

def get_rider_score(profile, race):

    score = 0

    if race.terrain_type == 'FL':
        if race.has_cobbles:
            score = (
                (profile.sprint * 0.2) +
                (profile.one_day_races * 0.3) +
                (profile.cobbles * 0.5)
            )
        else:
            score = (
                (profile.sprint * 0.5) +
                (profile.one_day_races * 0.5)
            )

    elif race.terrain_type == 'HI':
        if race.has_cobbles:
            score = (
                (profile.hills * 0.3) +
                (profile.one_day_races * 0.3) +
                (profile.cobbles * 0.4)
            )
        else:
            score = (
                (profile.hills * 0.5) +
                (profile.one_day_races * 0.5)
            )

    elif race.terrain_type == 'MT':
        base = (profile.climbing * 0.6) + (profile.hills * 0.4)
        wpk = profile.watts_per_kg or 0
        wpk_bonus = max(0, (wpk - 5.0) * 10)
        score = base + wpk_bonus

    return round(score, 2)


def get_endurance_modifier(profile, race):

    if not race.distance_km:
        return 1.0

    distance = float(race.distance_km)
    endurance = profile.endurance

    if distance < 200:
        return 1.0

    endurance_factor = 1.0 + ((100 - endurance) / 100) * (distance / 1000)
    return round(endurance_factor, 3)


def apply_race_day_noise(score, race):
    """
    Simulates race day chaos — crashes, punctures, attacks, bad legs.
    Noise scales with race style so finishes feel realistic:
      - breakaway: high variance, anyone can go clear
      - bunch_sprint: low variance, best sprinter usually wins
    """
    if race.race_style == 'bunch_sprint':
        # Tight finish — small noise, sprinters dominate
        noise = random.uniform(-5, 5)

    elif race.race_style == 'breakaway':
        # Solo or small group — big variance, upsets happen
        noise = random.uniform(-15, 15)

    else:
        noise = random.uniform(-8, 8)

    # Weather amplifies chaos — rain and wind cause more surprises
    weather_chaos = {
        'dry': 1.0,
        'heat': 1.1,
        'cold': 1.2,
        'rain': 1.5,  # rain shuffles the deck the most
        'wind': 1.4,
    }
    multiplier = weather_chaos.get(race.weather, 1.0)
    return round(score + (noise * multiplier), 2)


def get_finish_group(scored_riders):
    """
    After sorting, collapses riders within a small score gap
    into the same finishing group (same time).
    Simulates bunch sprint or small group finishes.
    Gap threshold: if score difference to next rider is < 3,
    they finish together (same time as the rider ahead).
    """
    groups = []
    current_group = [scored_riders[0]]

    for i in range(1, len(scored_riders)):
        prev_score = scored_riders[i - 1][2]
        curr_score = scored_riders[i][2]
        gap = prev_score - curr_score

        if gap < 3.0:
            # Close enough — same group, same time
            current_group.append(scored_riders[i])
        else:
            groups.append(current_group)
            current_group = [scored_riders[i]]

    groups.append(current_group)
    return groups


def simulate_race(race, riders):

    try:
        config = SimulationConfig.objects.get(terrain_type=race.terrain_type)
    except SimulationConfig.DoesNotExist:
        print(f"No SimulationConfig found for terrain: {race.terrain_type}. Aborting.")
        return

    if not race.distance_km:
        print(f"Race has no distance_km set. Aborting.")
        return

    weather_mod = get_weather_modifier(race.weather)
    adjusted_speed = config.base_speed_kmh + weather_mod
    base_time = int((float(race.distance_km) / adjusted_speed) * 3600)

    print(f"\n{'='*50}")
    print(f"Simulating: {race}")
    print(f"Distance: {race.distance_km}km | Terrain: {race.terrain_type} | Weather: {race.weather}")
    print(f"Base speed: {config.base_speed_kmh} km/h | Weather mod: {weather_mod:+} km/h | Adjusted: {adjusted_speed} km/h")
    print(f"Base time (winner): {base_time}s = {base_time//3600:02d}:{(base_time%3600)//60:02d}:{base_time%60:02d}")
    print(f"{'='*50}")

    # STEP 1 — SCORE EVERY RIDER + APPLY RACE DAY NOISE
    scored_riders = []
    for rider in riders:
        try:
            profile = rider.profile
        except Exception:
            continue

        base_score = get_rider_score(profile, race)
        noisy_score = apply_race_day_noise(base_score, race)
        scored_riders.append((rider, profile, noisy_score))

    if not scored_riders:
        print("No riders with profiles found. Aborting.")
        return

    # STEP 2 — SORT BY SCORE DESCENDING
    scored_riders.sort(key=lambda x: x[2], reverse=True)
    top_score = scored_riders[0][2]

    # STEP 3 — COLLAPSE INTO FINISH GROUPS
    groups = get_finish_group(scored_riders)

    # STEP 4 — CLEAR EXISTING RESULTS
    RaceResult.objects.filter(race=race).delete()

    # STEP 5 — WRITE RESULTS, RIDERS IN SAME GROUP GET SAME TIME
    position = 1
    for group in groups:
        # Time is based on the first rider in the group (highest score)
        group_leader = group[0]
        _, leader_profile, leader_score = group_leader
        score_gap = top_score - leader_score
        endurance_mod = get_endurance_modifier(leader_profile, race)
        time_penalty = int(score_gap * config.seconds_per_score_point * endurance_mod)
        group_time = base_time + time_penalty

        for rider, profile, score in group:
            RaceResult.objects.create(
                race=race,
                rider=rider,
                finishing_position=position,
                finish_status='FIN',
                time_in_seconds=group_time,
            )

            h = group_time // 3600
            m = (group_time % 3600) // 60
            s = group_time % 60
            group_label = f"(group of {len(group)})" if len(group) > 1 else "(solo)"
            print(f"P{position} | {rider.full_name:<25} | score: {score:>6} | time: {h:02d}:{m:02d}:{s:02d} {group_label}")
            position += 1

    print(f"{'='*50}\nDone. {position - 1} results written.\n")