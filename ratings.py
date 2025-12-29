from models import Player, Game, Chemistry, Preference
from app import db
import random
import itertools
import datetime

# ----------------------------
# Team Generator & Simulation
# ----------------------------
def generate_teams(selected_ids, avoid_last_week=False):
    """
    Generiert zwei Teams aus den ausgewählten Spieler-IDs.
    - avoid_last_week: Wenn True, versucht gleiche Teams wie letzte Woche zu vermeiden
    """
    players = Player.query.filter(Player.id.in_(selected_ids)).all()
    random.shuffle(players)

    mid = len(players)//2
    team1 = players[:mid]
    team2 = players[mid:]

    # Optionale Logik: vermeide gleiche Teams wie letzte Woche
    if avoid_last_week:
        last_game = Game.query.order_by(Game.id.desc()).first()
        if last_game:
            # einfache Heuristik: shuffle, wenn gleiche Teams wie letzte Woche
            random.shuffle(players)
            team1 = players[:mid]
            team2 = players[mid:]

    return team1, team2

def simulate_fairness(team1, team2):
    """
    Berechnet eine einfache Fairness-Bewertung 0-100%
    Basierend auf Ratings, Chemie und Präferenzen
    """
    r1 = sum(p.rating for p in team1)
    r2 = sum(p.rating for p in team2)
    rating_diff = abs(r1 - r2)

    # Chemie
    chem1 = sum(get_chemistry(a, b) for a,b in itertools.combinations(team1,2))
    chem2 = sum(get_chemistry(a, b) for a,b in itertools.combinations(team2,2))
    chem_score = abs(chem1 - chem2)

    # Präferenzen
    pref_score = 0
    for p1 in team1:
        for p2 in team2:
            pref_score += get_preference(p1, p2)

    # Einfaches Fairnessmodell (0=schlecht, 100=perfekt)
    fairness = max(0, 100 - rating_diff/50 - chem_score/10 - pref_score*10)
    return round(fairness,1)

# ----------------------------
# Chemie & Präferenzen
# ----------------------------
def get_chemistry(player_a, player_b):
    chem = Chemistry.query.filter(
        ((Chemistry.player_a==player_a.id) & (Chemistry.player_b==player_b.id)) |
        ((Chemistry.player_a==player_b.id) & (Chemistry.player_b==player_a.id))
    ).first()
    if chem:
        return chem.value
    return 0  # neutral

def get_preference(player_a, player_b):
    pref = Preference.query.filter(
        ((Preference.player_a==player_a.id) & (Preference.player_b==player_b.id))
    ).first()
    if pref:
        return pref.weight
    return 0  # neutral

# ----------------------------
# Ergebnis eingeben & Rating aktualisieren
# ----------------------------
def update_ratings(team1, team2, score_team1, score_team2):
    """
    Aktualisiert Ratings und Unsicherheiten nach Spiel
    Einfaches Modell inspiriert von TrueSkill
    """
    expected1 = sum(p.rating for p in team1)/(sum(p.rating for p in team1+team2))
    actual1 = score_team1 / (score_team1 + score_team2)

    for p in team1+team2:
        k = 32 * (1 + p.uncertainty/100)  # Unsicherheitsfaktor
        if p in team1:
            p.rating += k*(actual1-expected1)
        else:
            p.rating += k*((1-actual1)-(1-expected1))
        # Unsicherheit leicht anpassen
        p.uncertainty = max(10, p.uncertainty*0.95)

    db.session.commit()

# ----------------------------
# Erklärung „Warum dieses Team?“
# ----------------------------
def explain_teams(team1, team2):
    """
    Gibt eine kurze textliche Erklärung, warum die Teams so gebildet wurden
    """
    chem1 = sum(get_chemistry(a,b) for a,b in itertools.combinations(team1,2))
    chem2 = sum(get_chemistry(a,b) for a,b in itertools.combinations(team2,2))
    return f"Team1 Chemie: {chem1}, Team2 Chemie: {chem2}. Teams ausgewogen basierend auf Ratings und Chemie."

# ----------------------------
# Dashboard Daten
# ----------------------------
def get_dashboard_data():
    """
    Liefert Zeitreihen-Daten für Fairness und Chemie
    """
    games = Game.query.order_by(Game.id.asc()).all()
    fairness_over_time = []
    chemistry_over_time = []

    for g in games:
        # Vereinfachung: wir nehmen Teams aus dem Game
        team1 = g.team1 if hasattr(g,'team1') else []
        team2 = g.team2 if hasattr(g,'team2') else []
        if team1 and team2:
            fairness_over_time.append(simulate_fairness(team1, team2))
            chem1 = sum(get_chemistry(a,b) for a,b in itertools.combinations(team1,2))
            chem2 = sum(get_chemistry(a,b) for a,b in itertools.combinations(team2,2))
            chemistry_over_time.append(chem1+chem2)
    return {
        "fairness_over_time": fairness_over_time,
        "chemistry_over_time": chemistry_over_time
    }

# ----------------------------
# Simulation „Wie fair wäre dieses Spiel?“
# ----------------------------
def simulate_game(selected_ids):
    team1, team2 = generate_teams(selected_ids)
    fairness = simulate_fairness(team1, team2)
    explanation = explain_teams(team1, team2)
    return team1, team2, fairness, explanation
