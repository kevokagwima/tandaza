from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class Users(db.Model, UserMixin):
  __tablename__ = "users"
  id = db.Column(db.Integer(), primary_key=True)
  username = db.Column(db.String(50), nullable=False)
  phone_number = db.Column(db.Integer(), nullable=False)
  password = db.Column(db.String(100), nullable=False)
  last_login = db.Column(db.DateTime())
  status = db.Column(db.Boolean(), default=False)
  wallet = db.Column(db.Integer, default=0)
  session = db.relationship("Session", backref="owner", lazy=True)
  payment = db.relationship("Payment", backref="user_payment", lazy=True)
  deposit = db.relationship("Deposit", backref="deposits", lazy=True)
  withdraw = db.relationship("Withdrawal", backref="withdrawals", lazy=True)

  @property
  def passwords(self):
    return self.passwords

  @passwords.setter
  def passwords(self, plain_text_password):
    self.password = bcrypt.generate_password_hash(plain_text_password).decode("utf-8")

  def check_password_correction(self, attempted_password):
    return bcrypt.check_password_hash(self.password, attempted_password)

class Session(db.Model):
  __tablename__ = "session"
  id = db.Column(db.Integer(), primary_key=True)
  unique_id = db.Column(db.Integer(), unique=True)
  date_started = db.Column(db.DateTime(), nullable=False)
  game = db.Column(db.Integer(), db.ForeignKey("games.id"))
  user = db.Column(db.Integer(), db.ForeignKey("users.id"))
  is_active = db.Column(db.Boolean(), default=True)
  rounds = db.relationship("Rounds", backref="round", lazy=True)

class Games(db.Model):
  __tablename__ = "games"
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(50), nullable=False)
  session = db.relationship("Session", backref="session_game_name", lazy=True)
  rounds = db.relationship("Rounds", backref="round_game", lazy=True)

class Rounds(db.Model):
  __tablename__ = "rounds"
  id = db.Column(db.Integer(), primary_key=True)
  unique_id = db.Column(db.Integer(), unique=True)
  date_started = db.Column(db.DateTime())
  score = db.Column(db.Integer, default=0)
  session = db.Column(db.Integer(), db.ForeignKey("session.id"))
  game = db.Column(db.Integer(), db.ForeignKey("games.id"))
  is_active = db.Column(db.Boolean(), default=True)

class Payment(db.Model):
  __tablename__ = "payment"
  id = db.Column(db.Integer(), primary_key=True)
  unique_id = db.Column(db.Integer(), unique=True)
  is_pending = db.Column(db.Boolean(), default=True)
  is_confirmed = db.Column(db.Boolean(), default=False)
  user = db.Column(db.Integer(), db.ForeignKey("users.id"))

class Deposit(db.Model):
  __tablename__ = "deposit"
  id = db.Column(db.Integer(), primary_key=True)
  unique_id = db.Column(db.Integer(), unique=True)
  amount = db.Column(db.Integer(), default=0)
  date = db.Column(db.DateTime())
  is_pending = db.Column(db.Boolean(), default=False)
  is_confirmed = db.Column(db.Boolean(), default=True)
  user = db.Column(db.Integer(), db.ForeignKey("users.id"))

class Withdrawal(db.Model):
  __tablename__ = "withdrawals"
  id = db.Column(db.Integer(), primary_key=True)
  unique_id = db.Column(db.Integer(), unique=True)
  amount = db.Column(db.Integer(), default=0)
  date = db.Column(db.DateTime())
  is_pending = db.Column(db.Boolean(), default=False)
  is_confirmed = db.Column(db.Boolean(), default=True)
  user = db.Column(db.Integer(), db.ForeignKey("users.id"))
