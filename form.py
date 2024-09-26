from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length, DataRequired, ValidationError
from models import Users

class RegistrationForm(FlaskForm):
  username = StringField(label="Username", validators=[DataRequired(message="Username field is required")])
  phone_number = StringField(label="Phone Number", validators=[Length(min=10, max=10, message="Phone Number must "), DataRequired(message="Phonenumber field is required")])
  referral_code = StringField(label="Referral Code (Optional)")

  def validate_username(self, username_to_validate):
    if Users.query.filter_by(username=username_to_validate.data).first():
      raise ValidationError("Username already exists, Please try another one")

  def validate_phone_number(self, phone_number_to_validate):
    phone_number = phone_number_to_validate.data
    if phone_number[0] != str(0):
      raise ValidationError("Invalid phone number. Phone number must begin with 0")
    elif phone_number[1] != str(7) and phone_number[1] != str(1):
      raise ValidationError("Invalid phone number. Phone number must begin with 0 followed by 7 or 1")
    elif Users.query.filter_by(phone_number=phone_number).first():
      raise ValidationError("Phone Number already exists, Please try another one")

class LoginForm(FlaskForm):
  username = StringField(label="Username", validators=[DataRequired(message="Username field is required")])

class WalletForm(FlaskForm):
  amount = StringField(label="Deposit Amount", validators=[DataRequired(message="Deposit amount field is required")])
  phone_number = StringField(label="Phone Number", validators=[DataRequired(message="Phone number field is required")])
