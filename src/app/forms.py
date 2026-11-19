from wtforms import (
  Form,
  BooleanField,
  SearchField,
  SelectField,
  EmailField,
  PasswordField,
  SubmitField,
  StringField,
  MultipleFileField,
)
from wtforms.validators import InputRequired, Email, Length


# https://stackoverflow.com/questions/58105688/how-to-put-description-of-the-field-in-the-form-field
class SearchForm(Form):
    search_bar = SearchField(render_kw={"placeholder": "Search"}, 
        validators = [InputRequired("A search query is required to search")]
    )
    type_select = SelectField(choices=[("posts", "Posts"), ("users", "Users")])


class PostForm(Form):
    title = StringField(
        label = "Title",
        validators = [
            InputRequired(message="Please add a title to the post"),
            Length(max=32, message="Please choose a shorter title"),
        ]
    )

    images = MultipleFileField(
        label = "Images",
        validators = [
            InputRequired(message="Please add at least one image to the post"),
        ]
    )

    description = StringField(
        label = "Description",
        validators = [
            InputRequired(message="Please add a description to the post"),
            Length(max=1024, message="Please shorten the description"),
        ]
    )

    submit = SubmitField(label="Upload post")


class RegisterForm(Form):
    email = EmailField(
        label = "Email",
        validators = [
            InputRequired(message="Please enter your email"),
            Email(message="Please Enter a valid Email address"),
        ],
    )

    password = PasswordField(
        label = "Password",
        validators = [
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