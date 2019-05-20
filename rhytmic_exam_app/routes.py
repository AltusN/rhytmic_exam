import json

from flask import render_template, redirect, url_for, flash, redirect, request, make_response
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.urls import url_parse

from rhytmic_exam_app import app, db
from rhytmic_exam_app.forms import (
    LoginForm, 
    RegistrationForm, 
    ResetPasswordRequestForm, 
    ResetPasswordForm, 
    Questionare,
    AddExamQuestionsForm,
)
from rhytmic_exam_app.models import User, ExamQuestions
from rhytmic_exam_app.email import send_password_reset_email, send_email
from rhytmic_exam_app.exam_utils import make_question_for_exam

@app.route("/")
@app.route("/index")
def index():

    return render_template("index.html", title="Home")

@app.route("/login", methods=("GET","POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        #Get the user from the database
        user = User.query.filter_by(username = form.username.data).first()
        #check if it's a valid login attempt
        if not user or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        if not user.allow_login():
            flash("Registration not completed.")
            return redirect(url_for("login"))

        login_user(user, remember = form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc:
            next_page = url_for("index")
        
        return redirect(next_page)
    
    return render_template("login.html", title="Sign In", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/user/<username>")
def user(username):
    return username

@app.route("/register", methods=("GET", "POST"))
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data,
                    sagf_id=form.sagf_id.data,
                    name=form.name.data,
                    surname=form.surname.data,
                    email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        #Now the user is in the database, send an email to admin to request activation
        send_email(
            "New User Registration",
            sender="no-reply.rhytmic_exam.co.za",
            recipients=[app.config["ADMINS"][0]],
            text_body=render_template("email/new_user.txt"),
            html_body=render_template("email/new_user.html")
        )

        flash("Registration requested. You will receive an email once activated")
        return redirect(url_for("index"))
    
    return render_template("register.html", title="Regisgter", form=form)

@app.route("/reset_password_request", methods=("GET", "POST"))
def reset_password_request():
    if current_user.is_authenticated:
        flash("You're already logged in")
        return redirect(url_for("index"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        #flash even if there isn't a valid user
        flash("Password request has been sent. Check your email for instructions")
        return redirect(url_for("login"))

    return render_template("reset_password_request.html", title="Reset Password", form=form)

@app.route("/reset_password/<token>", methods=("GET","POST"))
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for("index"))
    
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset")
        return redirect(url_for("login"))

    return render_template("reset_password.html", form=form)

@app.route("/temp", methods=("GET", "POST"))
@login_required
def test_temp():
    form = Questionare()

    form.q3.choices=[("A","<img src={}> Value=0.30".format(url_for('static', filename='q17/A-1.png'))),
                        ("B","<img src={}>".format(url_for('static', filename='q17/A-2.png')))]

    if form.validate_on_submit():
        pass
    
    return render_template("temp.html", form=form)

@app.route("/add_question", methods=("GET", "POST"))
def add_question():
    form = AddExamQuestionsForm()

    if form.validate_on_submit():
        q = ExamQuestions(
            question=form.question.data,
            question_type=form.question_type.data,
            question_images=form.question_images.data,
            option_a=form.option_a.data,
            option_b=form.option_b.data,
            option_c=form.option_c.data,
            option_d=form.option_d.data,
            answer=form.answer.data
        )
        db.session.add(q)
        db.session.commit()

        flash("Question successfully added")
        return redirect(url_for("add_question"))
    
    return render_template("add_question.html", title="Add Exam Question", form=form)


@app.route("/play", methods=("GET",))
def play():
    #Get a cookie if the video was laoded
    #figure out how cookies work
    if "video_loaded" in request.cookies:
        pass
        #return "Video already loaded"

    video = "static/Megamind.mp4"
    resp = make_response(render_template("play.html", video=video))
    resp.set_cookie("video_loaded", "1")
    return resp

@app.route("/table_radio", methods=("GET", "POST"))
def table_radio():

    if request.method == "POST":
        result = request.form
        flash(result)
        return(redirect(url_for("index")))

    q_list = []

    exam_questions = ExamQuestions.query.all()

    for exam_question in exam_questions:
        q_list.append(make_question_for_exam(exam_question,exam_question.question_type))
        
    return render_template("table_radio.html", questions=q_list)

