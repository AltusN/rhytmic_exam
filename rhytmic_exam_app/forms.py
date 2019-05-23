from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length

from rhytmic_exam_app.models import User

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")

    submit = SubmitField("Sign In")

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    sagf_id = StringField("SAGF ID", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=5)])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])

    submit = SubmitField("Request Login")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        
        if user:
            raise ValidationError("Please try a different username")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()

        if user:
            raise ValidationError("Please use a different email address")

class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    submit = SubmitField("Request Reset")

class ResetPasswordForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    password2 = StringField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset Password")

class AddExamQuestionsForm(FlaskForm):
    question = StringField("Question", validators=[DataRequired()])
    question_type = SelectField("Question Type", choices=[
        ("1", "Type 1"),
        ("2", "Type 2"),
        ("3", "Type 3"),
        ("4", "Type 4"),
        ("5", "Type 5")
        ])
    question_images = StringField("Question Images")
    option_a = StringField("Option A", validators=[DataRequired()])
    option_b = StringField("Option B", validators=[DataRequired()])
    option_c = StringField("Option C", validators=[DataRequired()])
    option_d = StringField("Option D", validators=[DataRequired()])
    answer = SelectField("Answer", choices=[
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ])
    submit = SubmitField()