from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from flask_wtf.csrf import CSRFProtect
from wtforms.validators import Length, EqualTo, DataRequired, ValidationError
from models import Users

csrf = CSRFProtect()

class RegistrationForm(FlaskForm):
  username = StringField(label="Username", validators=[DataRequired(message="Username field is required")])
  phone_number = StringField(label="Phone Number", validators=[Length(min=10, max=10, message="Invalid Phone Number"), DataRequired(message="Phonenumber field is required")])
  password = PasswordField(label="Password", validators=[Length(min=5, message="Password must be more than 5 characters"), DataRequired(message="Password field is required")])
  password1 = PasswordField(label="Confirm Password", validators=[EqualTo("password", message="Passwords do not match"), DataRequired(message="Confirm password field is required")])

  def validate_password(form, field):
    special_characters = "!@#$%^&*()_+"
    password = field.data
    if not any(char in special_characters for char in password):
      raise ValidationError("Password must contain at least one special character")

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
  password = PasswordField(label="Password", validators=[DataRequired(message="Password field is required")])

class ResetPasswordForm(FlaskForm):
  username = StringField(label="Username", validators=[DataRequired(message="Username field is required")])
  new_password = PasswordField(label="New Password", validators=[DataRequired(message="Password field is required")])
  confirm_password = PasswordField(label="Confirm Password", validators=[EqualTo("new_password", message="Passwords do not match"), DataRequired(message="Confirm password field is required")])

  def validate_new_password(form, field):
    special_characters = "!@#$%^&*()_+"
    new_password = field.data
    if not any(char in special_characters for char in new_password):
      raise ValidationError("Password must contain at least one special character")
