from time import time
from datetime import datetime

import jwt
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from rhytmic_exam_app import db, login, app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    sagf_id = db.Column(db.Integer, index=True, unique=True)
    name = db.Column(db.String(64))
    surname = db.Column(db.String(64))
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    enabled = db.Column(db.Boolean(), default=False)
    admin = db.Column(db.Boolean, default=False)
    answers = db.relationship("ExamResult", backref="result", uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id,"exp": time() + expires_in},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        ).decode("utf-8")

    def allow_login(self):
        """ a 2 step proccess to actually authenticate on the website.
            Once registration requested, it must be enabled by an admin
            for now
        """
        return self.enabled

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except:
            return

        return User.query.get(id)

    def __repr__(self):
        return f"User <{self.username}>"

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sagf_id = db.Column(db.Integer, db.ForeignKey("user.sagf_id"), unique=True)
    theory_answer = db.Column(db.Text) #Store as json the result set
    practical_answer = db.Column(db.Text) #Store as json
    exam_start_date = db.Column(db.DateTime, default=datetime.today)
    exam_end_date = db.Column(db.DateTime)

class ExamQuestions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), index=True)
    question_type = db.Column(db.String(64))
    question_images = db.Column(db.Text) # store as json the images
    option_a = db.Column(db.String(64))
    option_b = db.Column(db.String(64))
    option_c = db.Column(db.String(64))
    option_d = db.Column(db.String(64))
    answer = db.Column(db.String(1))

    def __repr__(self):
        return f"Question <{self.question}>"


@login.user_loader
def load_user(id):
    return User.query.get(int(id))