from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow 
from flask_cors import CORS
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")

#CLASSES

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    stats = db.relationship('Stats', backref='User', cascade='all, delete, delete-orphan')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Stats(db.Model):
    stats_id = db.Column(db.Integer, primary_key=True)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __init__(self, wins, losses, user_id):
        self.wins = wins
        self.losses = losses
        self.user_id = user_id


# SCHEMAS

class StatsSchema(ma.Schema):
    class Meta: 
        fields = ('stats_id', 'wins', 'losses')

stats_schema = StatsSchema()
multiple_stats_schema = StatsSchema(many=True)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password', 'stats')
    stats = ma.Nested(multiple_stats_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)


# ENDPOINTS

@app.route('/user/add', methods=['POST'])
def add_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    username_duplicate = db.session.query(User).filter(User.username == username).first()

    if username_duplicate is not None:
        return jsonify("Error: The username is already registered.")

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username, encrypted_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify(user_schema.dump(new_user))


@app.route('/user/verify', methods=['POST'])
def verify_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify("User NOT verified")

    if bcrypt.check_password_hash(user.password, password) == False:
        return jsonify("User NOT verified")

    return jsonify(user_schema.dump(user))


@app.route('/user/get', methods=['GET'])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))


@app.route('/user/get/<id>', methods=["GET"])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))


@app.route('/user/delete/<id>', methods=['DELETE'])
def delete_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(user)
    db.session.commit()

    return jsonify("The user has been deleted")


@app.route('/stats/add', methods=['POST'])
def add_stats():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    wins = post_data.get('wins')
    losses = post_data.get('losses')
    user_id = post_data.get('user_id')

    new_stats = Stats(wins, losses, user_id)

    db.session.add(new_stats)
    db.session.commit()

    return jsonify(stats_schema.dump(new_stats))


@app.route('/stats/delete/<id>', methods=['DELETE'])
def delete_stats_by_id(id):
    stats = db.session.query(Stats).filter(Stats.stats_id == id).first()
    db.session.delete(stats)
    db.session.commit()

    return jsonify("The stats have been deleted")


@app.route('/stats/update/<id>', methods=["PUT", "PATCH"])
def update_stats_by_id(id):
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    wins = post_data.get('wins')
    losses = post_data.get('losses')
    user_id = post_data.get('user_id')

    stats = db.session.query(Stats).filter(Stats.stats_id == id).first()

    if wins != None:
        stats.wins = wins
    if losses != None:
        stats.losses = losses
    if user_id != None:
        stats.user_id = user_id
    

    db.session.commit()
    return jsonify("Stats have been updated")


@app.route('/stats/get/<id>', methods=["GET"])
def get_stats_by_id(id):
    stats = db.session.query(Stats).filter(Stats.stats_id == id)
    return jsonify(multiple_stats_schema.dump(stats))


if __name__ == "__main__":
    app.run(debug=True)