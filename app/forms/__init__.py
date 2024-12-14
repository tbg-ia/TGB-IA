"""
Initialize the forms package.
Contains all the forms used in the application.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo
