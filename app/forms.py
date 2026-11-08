from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length

from .constants import CATEGORIES


class ServiceRequestForm(FlaskForm):
    customer_name = StringField("Your name", validators=[DataRequired(), Length(max=120)])
    customer_email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=254)])
    customer_phone = StringField("Phone number", validators=[DataRequired(), Length(max=40)])
    category = SelectField("Service needed", choices=CATEGORIES, validators=[DataRequired()])
    requested_date = DateField("Preferred date", format="%Y-%m-%d", validators=[DataRequired()])
    service_area = StringField("Area", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Describe the work", validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField("Send request")


class LookupForm(FlaskForm):
    reference = StringField("Request reference", validators=[DataRequired(), Length(max=16)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=254)])
    submit = SubmitField("Check status")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Sign in")


class LogoutForm(FlaskForm):
    submit = SubmitField("Sign out")


class AssignProviderForm(FlaskForm):
    provider_id = SelectField("Assign provider", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Save assignment")


class UpdateStatusForm(FlaskForm):
    new_status = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Update status")


class NoteForm(FlaskForm):
    body = TextAreaField(
        "Internal note",
        validators=[
            DataRequired(message="Note cannot be empty."),
            Length(max=500, message="Note must be 500 characters or fewer."),
        ],
    )
    is_customer_visible = BooleanField("Show this note to the customer")
    submit = SubmitField("Add note")

