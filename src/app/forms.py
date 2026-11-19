from wtforms import BooleanField, Form, EmailField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length

class RegisterForm(Form):
    email = EmailField(
        label="Email",
        validators=[
            InputRequired(message="Please enter your email"),
            Email(message="Please Enter a valid Email address"),
        ],
    )

    password = PasswordField(
        label="Password",
        validators=[
            InputRequired(message="Please enter your password"),
            Length(min=12, message="Password must at least contain 12 characters")
        ],
    )

    submit = SubmitField(label="Register")


class LoginForm(Form):
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
