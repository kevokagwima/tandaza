from flask import Flask, render_template,  jsonify, redirect, url_for, flash, request
from flask_login import LoginManager, login_manager, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_bcrypt import generate_password_hash
from flask_sslify import SSLify
from models import *
from form import *
from config import Config
from modules import check_rounds
from datetime import datetime
from questions import game_questions
from credentials import LipanaMpesaPpassword
from requests.auth import HTTPBasicAuth
import requests, random, json, threading, pytz, os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
SSLify(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.login_view = '/signin'
login_manager.login_message = "Please login to access this page"
login_manager.login_message_category = "warning"
login_manager.init_app(app)
api_lock = threading.Lock()
tz = pytz.timezone("Africa/Nairobi")

@login_manager.user_loader
def load_user(user_id):
  try:
    return Users.query.filter_by(id=user_id).first()
  except:
    return None

@app.before_request
def app_modules():
  check_user_account_expiry()

def check_user_account_expiry():
  today = datetime.now()
  users = Users.query.all()
  for user in users:
    if user.last_login:
      diff = today - user.last_login
      diff_hours = diff.total_seconds() / 3600
      if int(diff_hours) > 24:
        user.status = False
        db.session.commit()

@app.route("/signup", methods=["POST", "GET"])
def signup():
  try:
    form = RegistrationForm()
    if form.validate_on_submit():
      new_user = Users(
        username = form.username.data,
        phone_number = form.phone_number.data,
        passwords = form.password.data
      )
      db.session.add(new_user)
      new_user.status = True
      db.session.commit()
      flash("Account created successfully", category="success")
      return redirect(url_for('signin'))
    
    if form.errors != {}:
      for err_msg in form.errors.values():
        flash(f"{err_msg}", category="danger")
        return redirect(url_for('signup'))
    
    return render_template("signup.html", form=form)
  except Exception as e:
    flash(f"{repr(e)}", category="danger")
    return redirect(url_for('home'))

@app.route("/signin", methods=["POST", "GET"])
def signin():
  try:
    form = LoginForm()
    if form.validate_on_submit():
      user = Users.query.filter_by(username=form.username.data).first()
      if user:
        if user.check_password_correction(attempted_password=form.password.data):
          login_user(user, remember=True)
          if user.status == False:
            flash("Your account is inactive. Complete payment to proceed", category="info")
            return redirect(url_for('payment'))
          else:
            user.last_login = datetime.now()
            db.session.commit()
            next = request.args.get("next")
            flash("Login successfull", category="success")
            return redirect(next or url_for('home'))
        else:
          flash("Invalid credentials", category="danger")
          return redirect(url_for('signin'))
      else:
        flash("No user with that username", category="danger")
        return redirect(url_for('signin'))
      
    if form.errors != {}:
      for err_msg in form.errors.values():
        flash(f"{err_msg}", category="danger")
        return redirect(url_for('signin'))

    return render_template("signin.html", form=form)
  except:
    flash("An error occurred", category="danger")
    return redirect(url_for('home'))

@app.route("/reset-password", methods=["POST", "GET"])
def reset_password():
  try:
    form = ResetPasswordForm()
    if form.validate_on_submit():
      user = Users.query.filter_by(username=form.username.data).first()
      if user:
        user.password = generate_password_hash(form.new_password.data).decode("utf-8")
        db.session.commit()
        flash("Password changed successfully", category="success")
        return redirect(url_for('signin'))
      else:
        flash("No account associated with that email address", category="danger")
        return redirect(url_for('reset_password'))
    
    if form.errors != {}:
      for err_msg in form.errors.values():
        flash(f"{err_msg}", category="danger")
        return redirect(url_for('reset_password'))

    return render_template("reset-password.html", form=form)
  except:
    flash("An error occurred", category="danger")
    return redirect(url_for('home'))

@app.route("/")
@app.route("/home")
@login_required
def home():
  games = Games.query.all()
  return render_template("index.html", games=games)

@app.route("/wallet")
@login_required
def wallet():
  deposits = Deposit.query.all()
  withdrawals = Withdrawal.query.all()
  return render_template("wallet.html", deposits=deposits, withdrawals=withdrawals)

@app.route("/payment")
@login_required
def payment():
  return render_template("payment.html")

def getAccessToken(api_URL, consumer_key, consumer_secret):
  try:
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    mpesa_access_token = r.json()
    validated_mpesa_access_token = mpesa_access_token['access_token']
    print(mpesa_access_token)
    return validated_mpesa_access_token
  except json.decoder.JSONDecodeError:
    jsonify({'error': 'Failed to decode JSON response from Safaricom API'})

def process_stk_push(access_token, amount):
  api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

  headers = {
    "Authorization": "Bearer %s" % access_token
  }

  request = {
    "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
    "Password": LipanaMpesaPpassword.online_password,
    "Timestamp": LipanaMpesaPpassword.lipa_time,
    "TransactionType": "CustomerPayBillOnline",
    "Amount": amount,
    "PartyA": f"254796897011",
    "PartyB": LipanaMpesaPpassword.Business_short_code,
    "PhoneNumber": f"254796897011",
    "checkout_url": "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    "CallBackURL": "https://tandaza-8e9c405ba062.herokuapp.com/confirm-payment",
    "AccountReference": "Tandaza",
    "TransactionDesc": "Testing stk push"
  }
  
  response = requests.post(api_url, json=request, headers=headers)

  return response

@app.route("/process-payment/send-stk-push/<string:pricing>")
def stk_push(pricing):
  consumer_key = 'M0scBRv7OQJAehMiEVFylazm2SvfqqTvKuGbh3fwTfPtCjO6'
  consumer_secret = 'ZBpJnS4vRo6rYIztbpsVVgHMEtdY2dHpA4LQ7NRNXKe57TsmHIAjjqiRPGfbfBgL'
  api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

  access_token = getAccessToken(api_URL, consumer_key, consumer_secret)

  if pricing == "basic":
    amount = 1
  else:
    amount = 1

  try:
    response = process_stk_push(access_token, amount)
    print(response)
    if response.status_code != 200:
      flash("Could not complete payment. Try again", category="danger")
      return redirect(url_for('payment'))
    else:
      flash("An stk push has been sent to your phone. Enter your pin to complete the payment", category="success")
      return redirect(url_for('payment'))
  except Exception as e:
    flash(f"{repr(e)}", category="danger")
    return redirect(url_for('payment'))

@app.route("/confirm-payment/", methods=["POST"])
def confirm_payment():
  json_data = request.get_json()
    
  # Extract necessary information from the JSON data
  result_code = json_data.get("Body", {}).get("stkCallback", {}).get("ResultCode")
  transaction_id = json_data.get("Body", {}).get("stkCallback", {}).get("CallbackMetadata", {}).get("Item", [])[0].get("Value")

  # Process the data (e.g., save to database, log, etc.)
  print(f"Result Code: {result_code}")
  print(f"Transaction ID: {transaction_id}")

  # Respond to M-Pesa
  response = {
      "ResultCode": 0,
      "ResultDesc": "Success"
  }
  return jsonify(response)

@app.route("/payment-complete")
def payment_complete():
  current_user.status = True
  db.session.commit()
  return redirect(url_for('home'))

@app.route("/start-game/<string:game_id>")
@login_required
@check_rounds
def start_game(game_id):
  game = Games.query.filter_by(name=game_id).first()
  existing_session = Session.query.filter_by(user=current_user.id, is_active=True).first()
  if not game:
    flash("Please select a game", category="danger")
    return redirect(url_for('home'))
  if not existing_session:
    new_session = Session(
      unique_id = random.randint(100000,999999),
      date_started = datetime.now(),
      game = game.id,
      user = current_user.id
    )
    db.session.add(new_session)
    db.session.commit()
    return redirect(url_for('play_game', session_id=new_session.unique_id))
  else:
    existing_session.game = game.id
    db.session.commit()
    return redirect(url_for('play_game', session_id=existing_session.unique_id))

@app.route("/play-game/<int:session_id>")
@login_required
@check_rounds
def play_game(session_id):
  session = Session.query.filter_by(unique_id=session_id).first()
  if not session:
    flash("Select a game to continue", category="info")
    return redirect(url_for('home'))
  else:
    existing_round = Rounds.query.filter_by(session=session.id, is_active=True).first()
    if existing_round is None:
      new_round = Rounds(
        unique_id = random.randint(100000,999999),
        date_started = datetime.now(),
        session = session.id
      )
      db.session.add(new_round)
      db.session.commit()
    game = Games.query.filter_by(id=session.game).first()
    if game.name not in game_questions:
      db.session.delete(session)
      db.session.commit()
      flash("Could not load questions", category="danger")
      return redirect(url_for('home'))
    else:
      questions = game_questions[game.name]
      random_questions = random.sample(list(questions.values()), min(5, len(questions)))
      question_ids = {i: q for i, q in enumerate(random_questions)}
    return render_template("game.html", session=session, questions=question_ids)

@app.route('/finish_game/<int:session_id>', methods=['POST'])
@check_rounds
def finish_game(session_id):
  session = Session.query.filter_by(unique_id=session_id).first()
  if not session:
    flash("Could not quit the game", category="danger")
    return redirect(url_for('home'))
  else:
    existing_round = Rounds.query.filter_by(session=session.id, is_active=True).first()
    game = Games.query.filter_by(id=session.game).first()
    selected_answers = request.form.to_dict()
    questions = game_questions.get(game.name, {})

    correct_count = 0
    total_questions = 0

    for question_id, question_data in questions.items():
      selected_answer = selected_answers.get(f'answer_{question_data["id"]}')
      if selected_answer:
        total_questions += 1
        correct_answer = question_data['answer']
        if selected_answer == correct_answer:
          correct_count += 1
          existing_round.score = correct_count
          db.session.commit()
    existing_round.is_active = False
    db.session.commit()
    return redirect(url_for('game_summary', round_id=existing_round.unique_id))

@app.route("/game-summary/<int:round_id>")
@login_required
def game_summary(round_id):
  session_round = Rounds.query.filter_by(unique_id=round_id).first()
  if not session_round:
    flash("Could not load game summary", category="danger")
    return redirect(url_for('home'))
  session = Session.query.filter_by(id=session_round.session).first()
  if not session:
    flash("No session found", category="danger")
    return redirect(url_for('home'))
  existing_rounds = Rounds.query.filter_by(session=session.id, is_active=False).count()
  if existing_rounds > 2:
    session.is_active = False
    db.session.commit()
  return render_template("game-summary.html", session_round=session_round)

@app.route("/quit-game/<int:session_id>")
@login_required
def quit_game(session_id):
  session = Session.query.filter_by(unique_id=session_id).first()
  if not session:
    flash("Could not quit the game", category="danger")
    return redirect(url_for('home'))
  else:
    session.is_active = False
    db.session.commit()
    flash("Game ended", category="success")
    return redirect(url_for('home'))

@app.route("/history")
def history():
  sessions = Session.query.filter_by(user=current_user.id, is_active=False).all()
  rounds = Rounds.query.all()
  return render_template("history.html", sessions=sessions, rounds=rounds)

@app.route("/logout")
@login_required
def logout():
  logout_user()
  flash("Logout successfull", category="success")
  return redirect(url_for('signin'))

if __name__ == "__main__":
  app.run(debug=True)
