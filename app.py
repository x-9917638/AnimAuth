from email.policy import default
from os import sendfile

import sqlalchemy
from flask import Flask, render_template, request, redirect, flash, url_for, abort, session, \
    send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc, update
from flask_uuid import FlaskUUID
from werkzeug.security import generate_password_hash, check_password_hash

from hashlib import md5, sha256
from datetime import datetime, timedelta
from PIL import Image
from PIL.ExifTags import TAGS
import time, os, base64, filetype, uuid
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = base64.b64decode(os.getenv('SECRET_KEY'))
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///default.db'
    app.config["UPLOAD_FOLDER"] = app.static_folder + "/media/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 # 32 mb (Images can't be that big, rightttt)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['USE_PERMANENT_SESSION'] = True

    return app


app = create_app()
FlaskUUID(app)


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4())
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    about = db.Column(db.String(5000))


class UserUploadedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(40), nullable=False)
    format = db.Column(db.String(5), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    author_id = db.Column(db.Uuid, db.ForeignKey('user.id'), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    # public = db.Column(db.Boolean, nullable=False, default=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(5000)) # This one is optional


with app.app_context():
    db.create_all()


def check_extensions(extension: str):
    """Check if file extension is in list of accepted image formats""" # Maybe pivot to checking whether the actual file is an image?
    return extension not in ("jpg", "png", "jpeg", "gif", "tif", "svg")


def get_recent_images(app: Flask, num: int):
    """Returns a list of the file ids of the last 10 images upload"""  # Will use on landing page probably
    return UserUploadedImage.query.order_by(UserUploadedImage.created.desc()).limit(num)


def handle_json_submission() -> None | tuple[str, str]:
    json_data = request.get_json()
    if not json_data:
        return abort(415)

    if not json_data.get("username"):
        flash("Username is required", "error")
        return "", ""
    username: str = json_data.get("username")

    if not len(username) < 80 and not len(username) >= 3:
        flash("Username must be between 3 and 80 characters.", "error")
        return "", ""

    if any([(
            not a.isalpha() and a not in ["_", "."] and not a.isnumeric()
    ) for a in username]):
        flash("Username may only contain letters, numbers and '.', '_'.", "error")
        return "", ""

    if not json_data.get("frames"):
        flash("Please submit an animation.", "error")
        return username, ""

    if len(json_data["frames"]) < 3 or len(json_data["frames"]) > 10:
        flash("Your animation must have 3-10 frames.", "error")
        return username, ""


    image_frames = [str(base64.b64decode(data[22:])) for data in json_data.get("frames")]
    # hashed_password = generate_password_hash("".join(image_frames))
    return username, "".join(image_frames) + json_data.get("animSpeed")


def validate_image(stream):
    format = filetype.guess_extension(stream)
    if not format:
        return None
    return format

@app.route('/')
def index():
    return render_template("index.html", images=get_recent_images(app, 5))

@app.route("/gallery")
def gallery():
    page = request.args.get('page', 1, type=int)

    sort = request.args.get("sort")
    if not sort: sort = "id"

    order = request.args.get("sort-order")
    if not order: order = "desc"

    str_end_date = request.args.get("end-date")
    if not str_end_date: str_end_date = "9999-12-31"
    end_date = datetime.strptime(str_end_date, "%Y-%m-%d")


    str_start_date = request.args.get("start-date")
    if not str_start_date: str_start_date = "0001-01-01"
    start_date = datetime.strptime(str_start_date, "%Y-%m-%d")

    author = request.args.get("author")

    title = request.args.get("title")

    query = UserUploadedImage.query.filter(
        UserUploadedImage.created >= start_date,
        UserUploadedImage.created <= end_date,
    )

    if order == "desc":
        query = query.order_by(desc(func.lower(getattr(UserUploadedImage, sort, None))))
    else:
        query = query.order_by(func.lower(getattr(UserUploadedImage, sort, None)))

    if author:
        query = query.filter(
            UserUploadedImage.author.like(f"%{author.lower()}%")
        )

    if title:
        query = query.filter(
            UserUploadedImage.title.like(f"%{title.lower()}%")
        )

    images = query.offset((page - 1) * 12).limit(12).all()
    return render_template(
        "gallery.html",
        images=images,
        page=page,
        author=author,
        title=title,
        sort=sort,
        order=order,
        start_date=str_start_date,
        end_date=str_end_date
    )

@app.route('/login', methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        flash("You are already signed in.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        username, password = handle_json_submission()
        user = User.query.filter_by(username=username).one_or_none()

        if not user:
            flash("Incorrect username or password!", "error")
            return redirect(url_for("login"))

        pwhash = user.password_hash

        if not check_password_hash(pwhash, password):
            flash("Incorrect username or password!", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        flash(f"Login success! Logged in as {user.username}.", "success")
        return redirect(url_for("user_profile", id=user.id))

    else:
        return render_template("login.html")

@app.route('/register/', methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        flash("You are already signed in.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        username, password = handle_json_submission()
        pwhash = generate_password_hash(password)

        user = User(username=username, password_hash=pwhash)
        db.session.add(user)
        try:
            db.session.commit()
        except:
            flash("An error occurred. Please try again", "error")
            return redirect(url_for("register"))
        flash("Successful registration! Please log in.", "success")
        return redirect(url_for("index"))
    else:
        return render_template("register.html")


@app.route('/logout', methods=["GET", "POST"])
def logout():
    if not session.get("user_id"):
        flash("You are not logged in...", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        session.clear()
        flash("Successfully logged out!", "success")
        return redirect(url_for("index"))
    return render_template("logout.html")


@app.route('/user/<uuid(strict=False):id>', methods=["POST", "GET"])
def user_profile(id):
    user = User.query.filter_by(id=id).one_or_none()

    if not user:
        abort(404)

    if request.method == "GET":
        is_authorised = False
        if session.get("user_id") == id:
            is_authorised = True

        images = UserUploadedImage.query.filter_by(author_id=id).order_by(desc(UserUploadedImage.created)).limit(4)
        return render_template("user_profile.html", user=user, images=images, is_authorised=is_authorised)
    else:
        if not session.get("user_id") == id:
            abort(403)

        pending_change = request.form.get("about")

        if len(pending_change) > 5000:
            flash("About me must be less than 5000 characters in length.", "error")
            return redirect(url_for("user_profile", id=user.id))

        user.about = pending_change
        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("user_profile", id=user.id))

@app.route('/upload', methods=["GET", 'POST'])
def upload():
    if not session.get("user_id"):
        flash("Please sign in to upload an image.", "error")
        return redirect(url_for("login"))
    user = User.query.filter_by(id=session.get("user_id")).one_or_none()

    title, description = (request.form.get(field) for field in ("title", "description"))
    if request.method == "GET":
        return render_template('upload.html', title=title, description=description)
    if request.method == "POST":
        if not title:
            flash("Please provide a title.", "error")
            return redirect(url_for("upload", title=title, description=description))

        if len(title) > 100:
            flash("The maximum length of a title is 100 characters.", "error")
            return redirect(url_for("upload"))

        if len(description) > 5000:
            flash("The maximum length of the description is 5000 characters", "error")
            return redirect(url_for("upload", title=title))

        if not description: description = f"This is where a meaningful description would go… if {user.username} had imagination."

        if "image" not in request.files:
            flash("Please upload a file.", "error")
            return redirect(url_for("upload", title=title, description=description))

        file = request.files["image"]

        extension: str = validate_image(file)

        if check_extensions(extension):
            flash("Unknown file type.", "error")
            return redirect(url_for("upload", title=title, description=description))

        filename = md5(file.read() + bytes(round(time.time()))).hexdigest() + '.' + extension
        file.seek(0)  # Move back to beginning
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        file_entry = UserUploadedImage(filename=filename, format=extension, author=user.username, author_id=user.id, title=title, description=description) # Temp placeholder for author_id, will somehow do it when I figure out session :c
        db.session.add(file_entry)
        try:
            db.session.commit()
            flash("Upload success!", "success")
        except Exception as e:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            abort(500, f"Exception {e}")

    return redirect(url_for("index"))

@app.route('/images/<filename>')
def images(filename):
    image_db_object = UserUploadedImage.query.filter_by(filename=filename).one_or_none()
    if not image_db_object:
        abort(404)

    metadata = {}
    with Image.open(app.static_folder + f"/media/uploads/{filename}") as img:
        info = img.info
        exifdata = img._getexif()
        exifdata = {} if not exifdata else exifdata
        for tag_id in TAGS:
            metadata[TAGS[tag_id]] = exifdata.get(tag_id)

        for attribute in ["format", "size", "width", "height", "is_animated", "n_frames"]:
            metadata[attribute] = getattr(img, attribute, None)

    return render_template("image.html", image=image_db_object, metadata=metadata)
    return f"<h1>Visited image page of image {filename}</h1>"

@app.route('/download/<filename>')
def download(filename):
    image = UserUploadedImage.query.filter_by(filename=filename).one_or_none()
    if not image:
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename,
                               download_name=image.title + "." + image.format,
                               as_attachment=True)

if __name__ == '__main__':
    app.run()
