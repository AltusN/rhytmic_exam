import csv

from rhytmic_exam_app import db
from rhytmic_exam_app.models import ExamQuestions

with open(r"c:\temp\exam_questions.csv","r") as csv_file:
    csv_records = csv.reader(csv_file, delimiter=",")
    for record in csv_records:
        new_rec = ExamQuestions(
            question_id=record[1],
            question=record[2],
            question_type=record[3],
            question_images=record[4],
            option_a=record[5],
            option_b=record[6],
            option_c=record[7],
            option_d=record[8],
            answer=record[9],
            question_category=record[10]
        )

        db.session.add(new_rec)

db.session.commit()
