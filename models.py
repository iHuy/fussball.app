from app import db

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    rating = db.Column(db.Float, default=1000)
    uncertainty = db.Column(db.Float, default=100)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)

class Chemistry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_a = db.Column(db.Integer)
    player_b = db.Column(db.Integer)
    value = db.Column(db.Float)

class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_a = db.Column(db.Integer)
    player_b = db.Column(db.Integer)
    weight = db.Column(db.Float)
