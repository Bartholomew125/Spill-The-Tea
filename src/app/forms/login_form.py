from wtforms import Form
from wtforms import EmailField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired


class LogInForm(Form):
    email = EmailField(
        label = "Email",
        validators = [InputRequired(message="Please enter your email")],
    )

    password = PasswordField(
        label = "Password",
        validators = [InputRequired(message="Please enter your password")],
    )

    remember_me = BooleanField(label="Remember me")

    submit = SubmitField(label="Login")