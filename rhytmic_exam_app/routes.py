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
    AddExamQuestionsForm,
    Disclaimer,
)
from rhytmic_exam_app.models import User, ExamQuestions
from rhytmic_exam_app.email import send_password_reset_email, send_email
from rhytmic_exam_app.exam_utils import make_question_for_exam

agreed = True

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="Home")

@app.route("/login", methods=("GET","POST"))
def login():
    if current_user.is_authenticated:
        flash("You are already logged in", "info")
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        #Get the user from the database
        user = User.query.filter_by(username = form.username.data).first()
        #check if it's a valid login attempt
        if not user or not user.check_password(form.password.data):
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))
        if not user.is_enabled():
            flash("Registration is still in progress", "info")
            return redirect(url_for("login"))

        login_user(user, remember = form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc:
            flash("Logged in successfully", "success")
            next_page = url_for("dashboard")
        
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

        flash("Registration requested. You will receive an email once activated", "info")
        return redirect(url_for("index"))
    
    return render_template("register.html", title="Regisgter", form=form)

@app.route("/reset_password_request", methods=("GET", "POST"))
def reset_password_request():
    if current_user.is_authenticated:
        flash("You're already logged in")
        return redirect(url_for("dashboard"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        #flash even if there isn't a valid user
        flash("Password request has been sent. Check your email for instructions", "info")
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
        flash("Your password has been reset. Please check your email.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard")

@app.route("/edit_questions")
def edit_questions():
    page = request.args.get("page", 1, type=int)

    question_pages = ExamQuestions.query.paginate(page=page , per_page=8)
    
    return render_template(
        "edit_questions.html",
        title="Edit Questions",
        questions=question_pages)

@app.route("/edit_exam_question/<int:question_id>", methods=("GET", "POST"))
def edit_exam_question(question_id):
    exam_question = ExamQuestions.query.filter_by(id=question_id).first_or_404()

    form = AddExamQuestionsForm()

    if form.validate_on_submit():
        exam_question.question = form.question.data
        exam_question.question_images = form.question_images.data
        exam_question.question_type = form.question_type.data
        exam_question.option_a = form.option_a.data
        exam_question.option_b = form.option_b.data
        exam_question.option_c = form.option_c.data
        exam_question.option_d = form.option_d.data
        exam_question.answer = form.answer.data

        db.session.add(exam_question)
        db.session.commit()

        flash(f"Question {question_id} updated successfully", "success")
        return redirect(url_for("edit_questions"))

    form.question.data = exam_question.question
    form.question_type.data = exam_question.question_type
    form.question_images.data = exam_question.question_images
    form.option_a.data = exam_question.option_a
    form.option_b.data = exam_question.option_b
    form.option_c.data = exam_question.option_c
    form.option_d.data = exam_question.option_d
    
    return render_template("edit_exam_question.html", question_id=exam_question.id, form=form)

@app.route("/add_question", methods=("GET", "POST"))
@login_required
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

        flash("Question successfully added", "success")
        return redirect(url_for("add_question"))
    
    return render_template("add_question.html", title="Add Exam Question", form=form)

@app.route("/delete_question/<int:question_id>", methods=("POST",))
@login_required
def delete_question(question_id):
    ExamQuestions.query.filter_by(id=question_id).delete()

    db.session.commit()

    flash(f"Question number {question_id} deleted", "success")
    
    return redirect(url_for("edit_questions"))

@app.route("/play", methods=("GET",))
def play():
    if not agreed:
        return redirect(url_for("disclaimer"))
    #Get a cookie if the video was laoded
    #figure out how cookies work
    if "video_loaded" in request.cookies:
        pass
        #return "Video already loaded"

    video = "static/video/Megamind.mp4"
    resp = make_response(render_template("play.html", video=video))
    resp.set_cookie("video_loaded", "1")
    return resp

@app.route("/disclaimer", methods=("GET", "POST"))
def disclaimer():
    """ the user must agree (and mostly be aware) that they will have a limited
    time to complete the theory and practical exam
    """
    prev_page = request.cookies.get("previous_page")
    form = Disclaimer()

    if request.method == "POST":
        flash("redirected")
        #go back to the caller
        agreed = request.get["invalidCheck"]
        return redirect(redirect_url())

    resp = make_response(render_template("disclaimer.html", form=form))
    resp.set_cookie("previous_page", request.referrer)

    return resp
    
@app.route("/theory_exam", methods=("GET", "POST"))
@login_required
def theory_exam():

    if request.method == "POST":
        result = request.form

        flash("Exam completed. Good luck!", "success")
        return(redirect(url_for("dashboard")))

    q_list = []

    exam_questions = ExamQuestions.query.all()

    for exam_question in exam_questions:
        q_list.append(make_question_for_exam(exam_question,exam_question.question_type))
        
    return render_template("theory_exam.html", title="National Theory Exam 2019", questions=q_list)

@app.route("/test")
def test_html():
    """ quickly check something out """
    return render_template("test.html")

def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)