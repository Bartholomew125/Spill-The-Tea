from functools import wraps
import os
from typing import Literal

from flask import Flask, redirect ,render_template, request, session
from sqlalchemy import CheckConstraint, ForeignKey, PrimaryKeyConstraint, String, insert, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from app.forms import RegisterForm, LoginForm, SearchForm, PostForm, DeleteAccForm, LogOutForm

from werkzeug.security import generate_password_hash, check_password_hash


class Base(DeclarativeBase): ...


app = Flask(__name__)

# Encryption
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

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


class PostImage(db.Model):
    __tablename__ = "post_images"

    id:        Mapped[int] = mapped_column(primary_key=True)
    post_id:   Mapped[int] = mapped_column(ForeignKey(Post.id))
    image_path: Mapped[str] = mapped_column(String(255))


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


# https://stackoverflow.com/questions/35307676/check-login-status-flask
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        print(session)
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            return redirect("/login")
    return wrap


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


@app.route("/post", methods=["GET", "POST"])
@login_required
def create_post():
    user_id = session.get("user_id")
    assert user_id is not None
    
    form = PostForm(request.form, request.files)
    title = "Create post"
    errors = []
    supported_formats = ["jpg", "jpeg", "png", "webp"]

    if request.method == "POST" and form.validate():
        post_title = form.title.data
        post_description = form.description.data
        images = request.files.getlist(form.images.name)

        # The form already enforced this
        # The assertions are just for pylance
        assert post_title is not None
        assert post_description is not None

        for image in images:
            name = image.filename
            assert name is not None
            if name.split(".")[-1].lower() not in supported_formats:
                errors.append(f"Unsupported image format: {name}")

        if not errors:
            new_post = Post()
            new_post.user_id = user_id
            new_post.title = post_title
            new_post.description = post_description

            db.session.add(new_post)
            db.session.flush()

            # All images are currently saved locally in the following directory
            os.makedirs(f"{app.static_folder}/post_images", exist_ok=True)

            for image in images:
                save_path = f"post_images/{image.filename}"
                image.save(f"{app.static_folder}/{save_path}")

                new_image = PostImage()
                new_image.post_id = new_post.id
                new_image.image_path = save_path

                db.session.add(new_image)

            db.session.commit()
            return redirect(f"/post/{new_post.id}")

    return render_template("create_post.html", form=form, title=title, errors=errors)


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
                    "display_name": f"Distinguished Tea Enjoyer",
                    "biography": ""
                })
            )
            db.session.commit()

            return redirect("/login")

        else:
            errors.append("User already exists")

    return render_template("register.html", form=form, title=title, errors=errors)


@app.route("/login", methods=["GET", "POST"])
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
            # TODO: If remember_me was set, then maybe add permanant or longer session

            #TODO: Redirect to e.g. home page on successful login
            return redirect("/")
            
        else:
            errors.append("Invalid email or password")

    return render_template("login.html", form=form, title=title, errors=errors)


@app.route("/post/<id>")
def post(id: int):
    post = db.session.get(Post, id)
    if not post:
        return {"error": "Post not found"}, 404
    user = db.session.get(User, post.user_id)
    creator = user.display_name if user else "Unknown User"
    return render_template("post.html", post=post, creator=creator)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    form = LogOutForm()
    title = "Log out"
    errors = []

    if request.method == "POST" and form.validate():
        session.clear()
        return redirect("/index")

    return render_template("logout.html", form=form, title=title, errors=errors)


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    user_id = session.get("user_id")

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
