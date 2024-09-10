from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from models import Session, Rounds
from datetime import datetime

# Custom decorator function
def check_rounds(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    todays_date = int(datetime.now().strftime("%d"))
    sessions = Session.query.filter_by(user=current_user.id).all()
    if sessions:
      last_session = sessions[-1]
      last_session_date = int(last_session.date_started.strftime("%d"))
      if last_session_date == todays_date:
        session_rounds = Rounds.query.filter_by(session=last_session.id, is_active=False).count()
        if session_rounds == 3:
          flash("You have reached the daily limit of 3 rounds. Come back tomorrow", category="info")
          return redirect(url_for('home'))
    return f(*args, **kwargs)
  return decorated_function