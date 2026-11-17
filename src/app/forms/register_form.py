from wtforms import Form, FormField, EmailField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired


class RegisterForm(Form):
    email = EmailField(
        label="Email",
        validators=[InputRequired(message="Please enter your email")],
    )

    password = PasswordField(
        label="Password",
        validators=[InputRequired(message="Please enter your password")],
    )

    submit = SubmitField(label="Register")
