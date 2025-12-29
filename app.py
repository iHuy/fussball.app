import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///football.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Modelle importieren
from models import Player, Game, Chemistry, Preference
import rating

# ----------------------------
# Startseite: Spieler-Auswahl
# ----------------------------
@app.route("/")
def index():
    players = Player.query.all()
    return render_template("index.html", players=players)

# ----------------------------
# Teams generieren & simulieren
# ----------------------------
@app.route("/teams/simulate", methods=["POST"])
def simulate_teams():
    selected_ids = request.form.getlist("players")
    team1, team2, fairness, explanation = rating.simulate_game(selected_ids)
    return render_template("teams_simulation.html",
                           team1=team1,
                           team2=team2,
                           fairness=fairness,
                           explanation=explanation)

# ----------------------------
# Ergebnis eingeben
# ----------------------------
@app.route("/submit_result", methods=["POST"])
def submit_result():
    team1_ids = request.form.getlist("team1")
    team2_ids = request.form.getlist("team2")
    score1 = int(request.form.get("score1"))
    score2 = int(request.form.get("score2"))

    team1 = Player.query.filter(Player.id.in_(team1_ids)).all()
    team2 = Player.query.filter(Player.id.in_(team2_ids)).all()

    rating.update_ratings(team1, team2, score1, score2)

    # Spiel in DB speichern
    game = Game(date=datetime.now())
    db.session.add(game)
    db.session.commit()

    return redirect(url_for("dashboard"))

# ----------------------------
# Dashboard
# ----------------------------
@app.route("/dashboard")
def dashboard():
    charts_data = rating.get_dashboard_data()
    players = Player.query.order_by(Player.rating.desc()).all()
    return render_template("dashboard.html", charts_data=charts_data, players=players)

# ----------------------------
# Admin: Spieler hinzufügen
# ----------------------------
@app.route("/add_player", methods=["POST"])
def add_player():
    name = request.form.get("name")
    if name:
        new_player = Player(name=name)
        db.session.add(new_player)
        db.session.commit()
    return redirect(url_for("index"))

# ----------------------------
# App starten
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
