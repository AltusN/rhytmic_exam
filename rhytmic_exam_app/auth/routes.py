from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, current_user, logout_user
from sqlalchemy.exc import IntegrityError

from werkzeug.urls import url_parse

from rhytmic_exam_app import db
from rhytmic_exam_app.models import User
#auth module
from rhytmic_exam_app.auth import bp
from ..auth.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm
)
from ..auth.email import send_password_reset_email, send_email

@bp.route("/login", methods=("GET","POST"))
def login():
    if current_user.is_authenticated:
        flash("You are already logged in", "info")
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        #Get the user from the database
        user = User.query.filter_by(username = form.username.data).first()
        #check if it's a valid login attempt
        if not user or not user.check_password(form.password.data):
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))
        if not user.is_enabled():
            flash("Registration is still in progress", "info")
            return redirect(url_for("auth.login"))

        login_user(user, remember = form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc:
            flash("Logged in successfully", "success")
            next_page = url_for("main.dashboard")
        
        return redirect(next_page)
    
    return render_template("auth/login.html", title="Sign In", form=form)

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@bp.route("/register", methods=("GET", "POST"))
def register():
    if current_user.is_authenticated:
        flash("You already have an account. Log out to create a new one", "info")
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data,
                    sagf_id=form.sagf_id.data,
                    name=form.name.data,
                    surname=form.surname.data,
                    email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash(f"An user with {form.name.data} {form.surname.data} already exists", "danger")
            db.session.rollback()
            return redirect(url_for("auth.register"))
        #Now the user is in the database, send an email to admin to request activation
        send_email(
            "Rhytmic Exam - New User Registration",
            sender="no-reply.rhytmic_exam.co.za",
            recipients=[current_app.config["ADMINS"][0]],
            text_body=render_template("email/new_user.txt"),
            html_body=render_template("email/new_user.html")
        )

        flash("Registration requested. You will receive an email once activated", "info")
        return redirect(url_for("main.index"))
    
    return render_template("auth/register.html", title="Regisgter", form=form)

@bp.route("/reset_password_request", methods=("GET", "POST"))
def reset_password_request():
    if current_user.is_authenticated:
        flash("You're already logged in")
        return redirect(url_for("main.dashboard"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        #flash even if there isn't a valid user
        flash("Password request has been sent. Check your email for instructions", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password_request.html", title="Reset Password", form=form)

@bp.route("/reset_password/<token>", methods=("GET","POST"))
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for("main.index"))
    
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password update successfully", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", title="Reset Password", form=form)

@bp.route("/profile/<string:username>")
def profile(username):
    return render_template("auth/profile.html")