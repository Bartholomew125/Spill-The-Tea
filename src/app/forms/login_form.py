from wtforms import Form
from wtforms import EmailField, PasswordField, SubmitField, BooleanField
from wtforms.validators import input_required


class LogInForm(Form):
    email = EmailField(
        label = "Email",
        validators = [input_required(message="Please enter your email")],
    )

    password = PasswordField(
        label = "Password",
        validators = [input_required(message="Please enter your password")],
    )

    remember_me = BooleanField(label="Remember me")

    submit = SubmitField(label="Login")