from hashlib import sha3_512
import os
from flask import Flask, redirect, render_template, request
from sqlalchemy import CheckConstraint, ForeignKey, PrimaryKeyConstraint, String, insert, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from app.forms.register_form import RegisterForm


class Base(DeclarativeBase): ...


app = Flask(__name__)

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

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    title = "Create account"
    errors = []

    if request.method == "POST" and form.validate():
        email = form.email.data
        password = form.password.data

        assert password is not None
        password_hash = sha3_512(password.encode()).hexdigest()

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

    return render_template("register_page.html", form=form, title=title, errors=errors)
