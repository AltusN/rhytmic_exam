import json
import datetime
from functools import wraps

from flask import render_template, redirect, url_for, flash, request, make_response, current_app
from flask_login import current_user, login_required

from rhytmic_exam_app import db
from rhytmic_exam_app.main.forms import (
    AddExamQuestionsForm,
    Disclaimer,
    UserEditForm
)

from rhytmic_exam_app.email import send_email

from rhytmic_exam_app.main.exam_utils import make_question_for_exam

from rhytmic_exam_app.models import User, ExamQuestions, ExamResult

from rhytmic_exam_app.main import bp

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User.query.filter_by(id=current_user.id).first()
        if user.is_admin:
            return f(*args, **kwargs)
        else:
            flash("You must be logged in as an admininstrative user to perform this action", "danger")
            return redirect(url_for("main.index"))
    return wrap

@bp.route("/")
@bp.route("/index")
def index():
    user_agent = request.user_agent.platform
    return render_template("index.html", title="Home", user_agent=user_agent)

@bp.route("/user_admin", methods=("GET", "POST"))
@login_required
@admin_required
def user_admin():
    page = request.args.get("page", 1, type=int)

    users = User.query.paginate(page=page , per_page=8)
    
    return render_template("exam/user_admin.html", title="User Admin", users=users)

@bp.route("/update_user/<int:id>", methods=("GET", "POST"))
@login_required
def update_user(id):
    user = User.query.filter_by(id=id).first_or_404()

    form = UserEditForm()

    if form.validate_on_submit(): 
        notify_user = False
        #Don't update the username
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data
        if not user.enabled and form.enabled.data:
            #then the user was not enabled previously but is now
            notify_user = True
        user.enabled = form.enabled.data
        user.admin = form.admin.data

        db.session.add(user)
        db.session.commit()
        
        if notify_user:
            send_email(
                "Rhytmic Exam - User Registration Complete",
                sender="no-reply@rhytmic_exam.co.za",
                recipients=[user.email],
                text_body=render_template("email/registration_complete.txt", user=user),
                html_body=render_template("email/registration_complete.html", user=user)
            )

        flash("User updated successfully", "success")

        return redirect(url_for("main.user_admin"))

    form.username.data = user.username
    form.name.data = user.name
    form.surname.data = user.surname
    form.sagf_id.data = user.sagf_id
    form.email.data = user.email
    form.enabled.data = user.enabled
    form.admin.data = user.admin
    
    return render_template("exam/update_user.html", title="Edit User", form=form, the_user=user.username)

@bp.route("/delete_user/<int:id>", methods=("POST",))
@login_required
@admin_required
def delete_user(id):
    user = User.query.filter_by(id=id).first_or_404()

    if user.username == current_user.username:
        flash("You cannot delete yourself", "danger")
        return redirect(url_for("main.index"))
    else:
        db.session.delete(user)
        db.session.commit()
        
        flash(f"{user.username} has been deleted", "success")
        return redirect(url_for("main.dashboard"))

@bp.route("/dashboard")
@login_required
def dashboard():
    exam_results = ExamResult.query.filter_by(sagf_id=current_user.sagf_id).first()
     
    return render_template("dashboard.html", title="Dashboard", exam_result=exam_results)

@bp.route("/edit_questions")
@login_required
def edit_questions():
    page = request.args.get("page", 1, type=int)

    question_pages = ExamQuestions.query.paginate(page=page , per_page=8)
    
    return render_template(
        "exam/edit_questions.html",
        title="Edit Questions",
        questions=question_pages)

@bp.route("/edit_exam_question/<int:question_id>", methods=("GET", "POST"))
@login_required
@admin_required
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
        return redirect(url_for("main.edit_questions"))

    form.question.data = exam_question.question
    form.question_type.data = exam_question.question_type
    form.question_images.data = exam_question.question_images
    form.option_a.data = exam_question.option_a
    form.option_b.data = exam_question.option_b
    form.option_c.data = exam_question.option_c
    form.option_d.data = exam_question.option_d
    form.question_category.data = exam_question.question_category
    
    return render_template("exam/edit_exam_question.html", title="Edit Exam Quesitons", question_id=exam_question.question_id, form=form)

@bp.route("/add_question", methods=("GET", "POST"))
@login_required
@admin_required
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
        return redirect(url_for("main.add_question"))
    
    return render_template("exam/add_question.html", title="Add Exam Question", form=form)

@bp.route("/delete_question/<int:question_id>", methods=("POST",))
@login_required
@admin_required
def delete_question(question_id):
    ExamQuestions.query.filter_by(question_id=question_id).delete()

    db.session.commit()

    flash(f"Question number {question_id} deleted", "success")
    
    return redirect(url_for("main.edit_questions"))

@bp.route("/disclaimer", methods=("GET", "POST"))
def disclaimer():
    """ 
        The user must agree (and mostly be aware) that they will have a limited
        time to complete the theory and practical exam
    """
    prev_page = request.cookies.get("previous_page")
    form = Disclaimer()

    if request.method == "POST":
        flash("redirected")
        #go back to the caller
        agreed = request.get["invalidCheck"]
        return redirect(redirect_url())

    resp = make_response(render_template("exam/disclaimer.html", form=form))
    resp.set_cookie("previous_page", request.referrer)

    return resp

@bp.route("/practical_exam", methods=("GET", "POST"))
@login_required
def practical_exam():
    user = User.query.filter_by(id = current_user.id).first_or_404()

    if user.answers and user.answers[0].practical_taken:
        flash("You have already taken the practical exam", "info")
        return redirect(url_for("main.dashboard"))

    practical_questions = ExamQuestions.query.filter_by(question_category="practical")
    
    practical_progress = ExamResult.query.filter_by(sagf_id=user.sagf_id).first()
    if not practical_progress:
        #The user has not taken the theory yet
        flash("The Theory Exam must be taken first", "info")
        return(redirect(url_for("main.dashboard")))

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
        #How many question have been answered
        progress["answered"] += 1

        practical_progress.practical_progress = json.dumps(progress)

        if practical_progress.practical_answer is None:
            practical_progress.practical_answer = json.dumps({f"answer_{progress['answered']}": form_result.get("answer")})
        else:
            answered_sofar = json.loads(practical_progress.practical_answer)
            answered_sofar[f"answer_{progress['answered']}"] = form_result.get("answer")
            #update the databse value
            practical_progress.practical_answer = json.dumps(answered_sofar)

        if progress["answered"] == 20:
            practical_progress.practical_taken = True

            db.session.add(practical_progress)
            db.session.commit()

            flash("Practical Exam completed. Good luck!", "success")
            return redirect(url_for("main.dashboard"))

        db.session.add(practical_progress)
        db.session.commit()

        return render_template("exam/practical_exam.html", title="National Practical Exam", q_dict=q_dict, progress=progress)
       
    return render_template("exam/practical_exam.html", title="National Practical Exam", q_dict=q_dict, progress=progress)
    
@bp.route("/theory_exam", methods=("GET", "POST"))
@login_required
def theory_exam():
    #set a cookie in the browser that will disable rendering the page in case a 
    #user deciceds to reload the page - which they shouldn't
    theory_exam_started = int(request.cookies.get("theory_loaded", 0))
    if theory_exam_started == 1:
        flash("You have already attempted the theory exam", "danger")
        current_app.logger.warn(f"{current_user.username} attempted re-entry into theory exam")
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(id = current_user.id).first_or_404()
    #check if the current user has already taken the theory exam
    if user.answers and user.answers[0].theory_taken:
            flash("You have already completed the theory exam", "info")
            return redirect(url_for("main.dashboard"))

    if request.method == "POST" and request.endpoint == "main.theory_exam":
        answers = request.form.to_dict()
        if "btnsubmit" in answers: 
            del answers["btnsubmit"]
        result = ExamResult(
            theory_answer=json.dumps(answers), 
            theory_taken=True,
            exam_start_date = datetime.datetime.today(),
            linked_user=user)

        db.session.add(result)
        db.session.commit()

        flash("Theory Exam completed. Good luck!", "success")
        return(redirect(url_for("main.dashboard")))

    q_list = []
    exam_questions = ExamQuestions.query.filter_by(question_category="theory")

    for exam_question in exam_questions:
        q_list.append(make_question_for_exam(exam_question,exam_question.question_type))

    resp = make_response(render_template("exam/theory_exam.html", title="National Theory Exam", questions=q_list))

    #set the cookie that will expire
    expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    resp.set_cookie("theory_loaded", "1", expires=expire_date)

    return resp

@bp.route("/results")
def results():
    """ Display a list of all the entrants results """

    results = ExamResult.query.all()




    return render_template("exam/results.html", title="Exam Results", results=results)

@bp.route("coming")
def coming_soon():
    return render_template("coming.html")

def redirect_url(default='main.index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)