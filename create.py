from flask import Flask
from models import *
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def create_tables():
  db.create_all()
  print("Tables created")

def drop_tables():
  db.drop_all()
  print("Tables dropped")

def add_games():
  game = Games(
    name = "Burudani"
  )
  db.session.add(game)
  db.session.commit()
  game = Games(
    name = "Siasa"
  )
  db.session.add(game)
  db.session.commit()
  game = Games(
    name = "Historia"
  )
  db.session.add(game)
  db.session.commit()
  game = Games(
    name = "Mchezo"
  )
  db.session.add(game)
  db.session.commit()
  print("Games Added")

if __name__ == '__main__':
  with app.app_context():
    drop_tables()
    create_tables()
    add_games()
