import json
import datetime
from functools import wraps

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
    UserEditForm
)
from rhytmic_exam_app.models import User, ExamQuestions, ExamResult
from rhytmic_exam_app.email import send_password_reset_email, send_email
from rhytmic_exam_app.exam_utils import make_question_for_exam

agreed = True

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User.query.filter_by(id=current_user.id).first()
        if user.is_admin:
            return f(*args, **kwargs)
        else:
            flash("You must be logged in as an admininstrative user to perform this action", "danger")
            return redirect(url_for("index"))
    return wrap

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

@app.route("/user_admin", methods=("GET", "POST"))
@login_required
@admin_required
def user_admin():
    page = request.args.get("page", 1, type=int)

    users = User.query.paginate(page=page , per_page=8)
    
    return render_template("user_admin.html", title="User Admin", users=users)

@app.route("/update_user/<int:id>", methods=("GET", "POST"))
@login_required
def update_user(id):
    user = User.query.filter_by(id=id).first_or_404()

    form = UserEditForm()

    if form.validate_on_submit(): 
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data
        user.enabled = form.enabled.data
        user.admin = form.admin.data

        db.session.add(user)
        db.session.commit()

        flash("User updated successfully", "success")

        return redirect(url_for("user_admin"))

    form.username.data = user.username
    form.name.data = user.name
    form.surname.data = user.surname
    form.sagf_id.data = user.sagf_id
    form.email.data = user.email
    form.enabled.data = user.enabled
    form.admin.data = user.admin
    
    return render_template("update_user.html", title="Edit User", form=form, the_user=user.username)

@app.route("/delete_user/<int:id>", methods=("POST",))
def delete_user(id):
    user = User.query.filter_by(id=id).first_or_404()

    if user.username == current_user.username:
        flash("You cannot delete yourself", "danger")
        return redirect(url_for("index"))
    else:
        db.session.delete(user)
        db.session.commit()
        
        flash(f"{user.username} has been deleted", "success")
        return redirect(url_for("dashboard"))
    
@app.route("/profile/<string:username>")
def profile(username):
    return render_template("profile.html")

@app.route("/register", methods=("GET", "POST"))
def register():
    if current_user.is_authenticated:
        flash("You already have an account. Log out to create a new one", "info")
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
            "Rhytmic Exam - New User Registration",
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

    return render_template("reset_password.html", title="Reset Password", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    exam_results = ExamResult.query.filter_by(sagf_id=current_user.sagf_id).first()
    
    return render_template("dashboard.html", title="Dashboard", exam_result=exam_results)

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
    exam_question = ExamQuestions.query.filter_by(question_id=question_id).first_or_404()

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
        exam_question.question_category = form.question_category.data

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
    form.question_category.data = exam_question.question_category
    
    return render_template("edit_exam_question.html", title="Edit Exam Quesitons", question_id=exam_question.question_id, form=form)

@app.route("/add_question", methods=("GET", "POST"))
@login_required
def add_question():
    form = AddExamQuestionsForm()

    if form.validate_on_submit():
        q = ExamQuestions(
            question_id = db.session.query(db.func.max(ExamQuestions.question_id)).scalar() + 1,
            question=form.question.data,
            question_type=form.question_type.data,
            question_images=form.question_images.data,
            option_a=form.option_a.data,
            option_b=form.option_b.data,
            option_c=form.option_c.data,
            option_d=form.option_d.data,
            answer=form.answer.data,
            question_category=form.question_category.data
        )
        db.session.add(q)
        db.session.commit()

        flash("Question successfully added", "success")
        return redirect(url_for("add_question"))
    
    return render_template("add_question.html", title="Add Exam Question", form=form)

@app.route("/delete_question/<int:question_id>", methods=("POST",))
@login_required
@admin_required
def delete_question(question_id):
    ExamQuestions.query.filter_by(question_id=question_id).delete()

    db.session.commit()

    flash(f"Question number {question_id} deleted", "success")
    
    return redirect(url_for("edit_questions"))

@app.route("/play", methods=("GET","POST"))
def play():
    #Get a cookie if the video was laoded
    #figure out how cookies work
    if "video_loaded" in request.cookies:
        pass
        #return "Video already loaded"

    if request.method == "POST":
        pass

    #video = "static/exam_videos/Anna_Sokolova_rope.mp4"
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

@app.route("/practical_exam", methods=("GET", "POST"))
@login_required
def practical_exam():
    user = User.query.filter_by(id = current_user.id).first_or_404()

    if user.answers and user.answers[0].practical_taken:
        flash("You have already taken the practical exam", "info")
        return redirect(url_for("dashboard"))

    practical_questions = ExamQuestions.query.filter_by(question_category="practical")
    
    practical_progress = ExamResult.query.filter_by(sagf_id=user.sagf_id).first()
    if not practical_progress:
        #The user has not taken the theory yet
        flash("Please take the theory assesment first", "info")
        return(redirect(url_for("dashboard")))

    x = 1
    q_dict = {
        "questions":[],
        "videos":[],
        "heading":[],
    }

    for question in practical_questions:
        q_dict["questions"].append(json.loads(question.question)["question"])
        q_dict["heading"].append(json.loads(question.question)["heading"])
        #find a better way to do this... .loading the same data over and over again here
        q_dict["videos"] = [vid for vid in json.loads(question.question_images)["videos"]]
        x += 1

    progress = {"q_id":0, "v_id":0, "answered":0}
    if user.answers and user.answers[0].practical_progress is not None:
        progress = json.loads(user.answers[0].practical_progress)

    if request.method == "POST":
        form_result = request.form.to_dict()
        #Do some work to update the db with the progress
        if progress["v_id"] == 4:
            progress["v_id"] = 0
            progress["q_id"] += 1
        else:
            progress["v_id"] += 1
        #Save the answers so long
        progress["answered"] += 1

        practical_progress.practical_progress = json.dumps(progress)

        if practical_progress.practical_answer is None:
            practical_progress.practical_answer = json.dumps({f"answer_{progress['answered']}": form_result.get("answer")})
        else:
            answered_sofar = json.loads(practical_progress.practical_answer)
            answered_sofar[f"answer_{progress['answered']}"] = form_result.get("answer")
            practical_progress.practical_answer = json.dumps(answered_sofar)

        if progress["answered"] == 20:
            practical_progress.practical_taken = True

            db.session.add(practical_progress)
            db.session.commit()

            flash("Practical Exam completed. Good luck!", "success")
            return redirect(url_for("dashboard"))

        db.session.add(practical_progress)
        db.session.commit()

        return render_template("practical_exam.html", title="National Practical Exam", q_dict=q_dict, progress=progress)
       
    return render_template("practical_exam.html", title="National Practical Exam", q_dict=q_dict, progress=progress)
    
@app.route("/theory_exam", methods=("GET", "POST"))
@login_required
def theory_exam():
    #set a cookie in the browser that will disable rendering the page in case a 
    #user deciceds to reload the page - which he shouldn't
    theory_exam_started = int(request.cookies.get("theory_loaded", 0))
    if theory_exam_started == 1:
        flash("You have already attempted the theory exam", "danger")
        app.logger.error(f"{current_user.username} attempted re-entry into theory exam")
        return redirect(url_for("dashboard"))

    user = User.query.filter_by(id = current_user.id).first_or_404()
    #check if the current user has already taken the theory exam
    if user.answers and user.answers[0].theory_taken:
            flash("You have already completed the theory exam", "info")
            return redirect(url_for("dashboard"))

    if request.method == "POST" and request.endpoint == "theory_exam":
        answers = request.form.to_dict()
        if "btnsubmit" in answers: 
            del answers["btnsubmit"]
        result = ExamResult(
            theory_answer=json.dumps(answers), 
            theory_taken=True,
            exam_start_date = datetime.datetime.today(),
            result=user)

        db.session.add(result)
        db.session.commit()

        flash("Theory Exam completed. Good luck!", "success")
        return(redirect(url_for("dashboard")))

    q_list = []
    exam_questions = ExamQuestions.query.filter_by(question_category="theory")

    for exam_question in exam_questions:
        q_list.append(make_question_for_exam(exam_question,exam_question.question_type))

    resp = make_response(render_template("theory_exam.html", title="National Theory Exam", questions=q_list))

    #set the cookie to expire in 2 hours
    expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    resp.set_cookie("theory_loaded", "1", expires=expire_date)

    return resp
@app.route("/test")
def test_html():
    """ quickly check something out """
    return render_template("test.html")

def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)
