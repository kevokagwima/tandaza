from flask import Flask, render_template,  jsonify, redirect, url_for, flash, request
from flask_login import LoginManager, login_manager, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_sslify import SSLify
from models import *
from form import *
from config import Config
from modules import check_rounds
from datetime import datetime
from questions import game_questions
from credentials import LipanaMpesaPpassword
from requests.auth import HTTPBasicAuth
import requests, random, json, threading, pytz, uuid

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
  except Exception as e:
    flash(f"{repr(e)}", category="info")

@app.route("/signup", methods=["POST", "GET"])
def signup():
  try:
    form = RegistrationForm()
    if form.validate_on_submit():
      if form.referral_code.data:
        if verify_referral_code(form.referral_code.data):
          new_user = Users(
            username = form.username.data,
            phone_number = form.phone_number.data,
            referral_code = str(uuid.uuid4()).replace('-', '')[:10],
          )
          db.session.add(new_user)
          db.session.commit()
          flash("Account created successfully", category="success")
          return redirect(url_for('signin'))
        else:
          flash("Invalid referral code", category="danger")
          return redirect(url_for('signup'))
      else:
        new_user = Users(
          username = form.username.data,
          phone_number = form.phone_number.data,
          referral_code = str(uuid.uuid4()).replace('-', '')[:10],
        )
        db.session.add(new_user)
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
    return redirect(url_for('signup'))

def verify_referral_code(code):
  user = Users.query.filter_by(referral_code=code).first()
  if not user:
    return False
  else:
    return True

@app.route("/signin", methods=["POST", "GET"])
def signin():
  try:
    form = LoginForm()
    if form.validate_on_submit():
      user = Users.query.filter_by(username=form.username.data).first()
      if not user:
        flash("No user with that username", category="danger")
      else:
        login_user(user, remember=True)
        user.last_login = datetime.now()
        db.session.commit()
        next = request.args.get("next")
        flash("Login successfull", category="success")
        return redirect(next or url_for('home'))
      return redirect(url_for('signin'))
      
    if form.errors != {}:
      for err_msg in form.errors.values():
        flash(f"{err_msg}", category="danger")
        return redirect(url_for('signin'))

    return render_template("signin.html", form=form)
  except Exception as e:
    flash(f"{repr(e)}", category="danger")
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
  payments = Deposit.query.all()
  deposits = Deposit.query.all()
  withdrawals = Withdrawal.query.all()
  return render_template("wallet.html", deposits=deposits, withdrawals=withdrawals, payments=payments)

@app.route("/deposit")
@login_required
def deposit():
  form = WalletForm()
  heading = "Deposit"
  return render_template("payment.html", heading=heading, form=form)

@app.route("/withdraw")
@login_required
def withdraw():
  form = WalletForm()
  heading = "Withdraw"
  return render_template("payment.html", heading=heading, form=form)

def getAccessToken(api_URL, consumer_key, consumer_secret):
  try:
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    mpesa_access_token = r.json()
    validated_mpesa_access_token = mpesa_access_token['access_token']
    print(mpesa_access_token)
    return validated_mpesa_access_token
  except json.decoder.JSONDecodeError:
    jsonify({'error': 'Failed to decode JSON response from Safaricom API'})

def process_stk_push(access_token, amount, phone_number):
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
    "PartyA": f"254{phone_number}",
    "PartyB": LipanaMpesaPpassword.Business_short_code,
    "PhoneNumber": f"254796897011",
    "checkout_url": "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    "CallBackURL": "https://tandaza-d792c1108bcd.herokuapp.com/confirm-payment/",
    "AccountReference": "Tandaza",
    "TransactionDesc": "Testing stk push"
  }
  
  response = requests.post(api_url, json=request, headers=headers)

  return response

@app.route("/process-payment/send-stk-push", methods=["POST"])
def stk_push():
  form = WalletForm()
  consumer_key = 'M0scBRv7OQJAehMiEVFylazm2SvfqqTvKuGbh3fwTfPtCjO6'
  consumer_secret = 'ZBpJnS4vRo6rYIztbpsVVgHMEtdY2dHpA4LQ7NRNXKe57TsmHIAjjqiRPGfbfBgL'
  api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

  access_token = getAccessToken(api_URL, consumer_key, consumer_secret)
  phone_number = form.phone_number.data
  amount = form.amount.data
  try:
    response = process_stk_push(access_token, amount, phone_number)
    print(response)
    if response.status_code != 200:
      flash("Could not complete payment. Try again", category="danger")
      return redirect(url_for('wallet'))
    else:
      flash("An stk push has been sent to your phone. Enter your pin to complete the payment", category="success")
      return redirect(url_for('wallet'))
  except Exception as e:
    flash(f"{repr(e)}", category="danger")
    return redirect(url_for('wallet'))

@app.route("/confirm-payment/", methods=["POST"])
def confirm_payment():
  json_data = request.get_json()
    
  # Extract necessary information from the JSON data
  stk_callback = json_data['Body']['stkCallback']
  result_code = stk_callback['ResultCode']

  print(json_data)
  print(stk_callback)
  print(result_code)

  # Process the data (e.g., save to database, log, etc.)
  if result_code != 0:
    response = {
      "ResultCode": stk_callback['ResultCode'],
      "ResultDesc": stk_callback['ResultDesc']
    }
  else:
    merchant_request_id = stk_callback['MerchantRequestID']
    checkout_request_id = stk_callback['CheckoutRequestID']
    metadata = {item['Name']: item['Value'] for item in stk_callback['CallbackMetadata']['Item'] if 'Value' in item}
    mpesa_receipt_number = metadata.get('MpesaReceiptNumber')
    transaction_date = metadata.get('TransactionDate')
    amount = metadata.get('Amount')
    phone_number = metadata.get('PhoneNumber')

    new_payment = Payment(
      MerchantRequestID = merchant_request_id,
      CheckoutRequestID = checkout_request_id,
      MpesaReceiptNumber = mpesa_receipt_number,
      transactionDate = datetime.now(),
      amount = amount,
      phone_number = phone_number,
      user = current_user.id
    )
    db.session.add(new_payment)
    db.session.commit()

    # Respond to M-Pesa
    response = {
      "ResultCode": stk_callback['ResultCode'],
      "ResultDesc": stk_callback['ResultDesc']
    }
  return jsonify(response)

@app.route("/payment-complete")
def payment_complete():
  current_user.status = True
  db.session.commit()
  return redirect(url_for('home'))

@app.route("/start-game/<string:game_id>")
@login_required
# @check_rounds
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
# @check_rounds
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
        session = session.id,
        game = session.game
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
# @check_rounds
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
  if session_round.score == 5:
    current_user.wallet = current_user.wallet + 1000
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
@login_required
def history():
  sessions = Session.query.filter_by(user=current_user.id).all()
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
