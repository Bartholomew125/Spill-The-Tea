import os
from typing import Literal

from flask import Flask, redirect ,render_template, request, session
from sqlalchemy import CheckConstraint, ForeignKey, PrimaryKeyConstraint, String, insert, select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from app.forms import RegisterForm, LoginForm, SearchForm, DeleteAccForm

from werkzeug.security import generate_password_hash, check_password_hash


class Base(DeclarativeBase): ...


app = Flask(__name__)

# Encryption
app.config["SECRET_KEY"] = "flask-secret-key"

# Session cookie parameters
# app.config['SESSION_COOKIE_SECURE'] = True
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = 'Strict' # CSRF mitigation

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db = SQLAlchemy(app, model_class=Base)


class User(db.Model):
    __tablename__ = "users"

    id:            Mapped[int] = mapped_column(primary_key=True)
    username:      Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128)) # Depends on hashing algorithm.
    display_name:  Mapped[str] = mapped_column(String(32))
    biography:     Mapped[str] = mapped_column(String(1024))


class UserFollows(db.Model):
    __tablename__ = "user_follows"
    __table_args__ = (
        CheckConstraint("following_user <> follower_user"),
        PrimaryKeyConstraint("following_user", "follower_user")
    )

    following_user: Mapped[int] = mapped_column(ForeignKey(User.id))
    follower_user:  Mapped[int] = mapped_column(ForeignKey(User.id))


class Post(db.Model):
    __tablename__ = "posts"

    id:          Mapped[int] = mapped_column(primary_key=True)
    user_id:     Mapped[int] = mapped_column(ForeignKey(User.id))
    title:       Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(1024))
    upvotes:     Mapped[int] = mapped_column(default=0)
    downvotes:   Mapped[int] = mapped_column(default=0)


class Comment(db.Model):
    __tablename__ = "comments"

    id:      Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    post_id: Mapped[int] = mapped_column(ForeignKey(Post.id))
    text:    Mapped[str] = mapped_column(String(128))


class Collection(db.Model):
    __tablename__ = "collections"

    id:      Mapped[int] = mapped_column(primary_key=True)
    title:   Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))


class CollectionPost(db.Model):
    __tablename__ = "collection_posts"
    __table_args__ = (
        PrimaryKeyConstraint("collection_id", "post_id"),
    )

    collection_id: Mapped[int] = mapped_column(ForeignKey(Collection.id))
    post_id:       Mapped[int] = mapped_column(ForeignKey(Post.id))


with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm(request.form)
    res = []
    if request.method == "POST" and form.validate():
        selected_type: Literal["users", "posts"] = form.type_select.data
        query = form.search_bar.data
        assert query is not None

        match selected_type:
            case "posts":
                rows = db.session.execute(
                    select(Post).where(Post.title.like(f"%{query}%"))
                ).all()
                res = [row[0].title for row in rows]
            case "users":
                rows = db.session.execute(
                    select(User).where(User.display_name.like(f"%{query}%"))
                ).all()
                res = [row[0].display_name for row in rows]
            case _:
                return {"error": "Unknown search type selected"}, 400

    return render_template("search.html", form=form, res=res)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    title = "Create account"
    errors = []

    if request.method == "POST" and form.validate():
        email = form.email.data
        password = form.password.data

        assert password is not None
        password_hash = generate_password_hash(password)

        row = db.session.execute(
            select(User).where(User.username == email)
        ).one_or_none()

        if row is None:
            row = db.session.execute(
                insert(User).values({
                    "username": email,
                    "password_hash": password_hash,
                    "display_name": "",
                    "biography": ""
                })
            )
            db.session.commit()

            return redirect("/login")

        else:
            errors.append("User already exists")

    return render_template("register.html", form=form, title=title, errors=errors)


@app.route("/login", methods= ["GET", "POST"])
def login():
    form = LoginForm(request.form)
    title = "Login"
    errors = []

    if request.method == "POST" and form.validate():
        email = form.email.data
        entered_password = form.password.data
        assert entered_password is not None

        user = db.session.execute(
            select(User).where(User.username == email)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, entered_password):
            session.clear()
            # User id is preferred over username (email)
            # Since the id is fixed but username might change over time
            session["user_id"] = user.id

            #TODO: Redirect to e.g. home page on successful login
            return redirect("/")
            
        else:
            errors.append("Invalid email or password")

    return render_template("login.html", form=form, title=title, errors=errors)


@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect("/login")

    form = DeleteAccForm(request.form)
    title = "Delete account"
    errors = []

    if request.method == "POST" and form.validate():
        entered_password = form.password.data
        assert entered_password is not None

        user = db.session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, entered_password):
            db.session.delete(user)
            db.session.commit()
            session.clear()

            return redirect("/login")
        else:
            errors.append("Incorrect password")

    return render_template("delete_account.html", form=form, title=title, errors=errors)