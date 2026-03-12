# Online rhytmic exam [![Build Status](https://travis-ci.com/AltusN/rhytmic_exam.svg?branch=master)](https://travis-ci.com/AltusN/rhytmic_exam)

**This app is pupouse built for an online version of the national rhytmic gymnastics exam**
*Alter at own risk*
---
## Theory
A multiple choice form that can generate 5 types of questions. see doc for examples

## Practical
Allows a video to be played only once and expects an answer.

## Reporting
Allows results to be downloaded to csv

**No localisation support yet**

////
Accessing the db:
you will start with an empty database. You must first run:
* flask --app rhytmic db upgrade 
* flask --app rhytmic shell
* create a new user:
    u1 = User(username='pies', enabled=True, admin=True)
    u1.set_password('password')
    db.session.add(u1)
    db.session.commit()

You can now login by running the flask builtin or some other webserver
