import json
import os

def make_question_for_exam(question, type):
    """ the question types that are rendered on the theory form
    can be in of 5 formats. consult the doc for examples on how the layout
    will look when deciding which layout to use
    """
    make_question = {
        "1":make_type_one_question,
        "2":make_type_two_question,
        "3":make_type_three_question,
        "4":make_type_four_question,
        "5":make_type_five_question
    }
    return make_question[type](question)

def make_type_one_question(question):

    q = {}
    q["q"] = question.id
    q["q_string"] = question.question
    q["type"] = "1"
    q["option_a"] = question.option_a
    q["option_b"] = question.option_b
    q["option_c"] = question.option_c
    q["option_d"] = question.option_d

    return q
def make_type_two_question(question):
    
    header = json.loads(question.question_images)
    path = header["path"]["location"]

    q = {}
    q["q"] = question.id
    q["q_string"] = question.question
    q["type"] = "2"
    q["attributes"] = {}
    q["attributes"]["header"] = [os.path.join(path, x) for x in json.loads(
        question.question_images)["path"]["filename"]]
    q["attributes"]["radio1"] = [os.path.join(path, x) for x in json.loads(
        question.option_a)["path"]["filename"]]
    q["attributes"]["radio2"] = [os.path.join(path, x) for x in json.loads(
        question.option_b)["path"]["filename"]]
    q["attributes"]["radio3"] = [os.path.join(path, x) for x in json.loads(
        question.option_c)["path"]["filename"]]
    q["attributes"]["radio4"] = [os.path.join(path, x) for x in json.loads(
        question.option_d)["path"]["filename"]]

    return q

    
def make_type_three_question(question):
    header = json.loads(question.question_images)
    path = header["path"]["location"]

    q = {}
    q["q"] = question.id
    q["q_string"] = question.question
    q["type"] = "3"
    q["images"] = [os.path.join(path, x) for x in json.loads(
        question.question_images)["path"]["filename"]]
    q["option_a"] = [x for x in json.loads(
        question.option_a)["q_a"]]
    q["option_b"] = [x for x in json.loads(
        question.option_b)["q_a"]]
    q["option_c"] = [x for x in json.loads(
        question.option_c)["q_a"]]
    q["option_d"] = [x for x in json.loads(
        question.option_d)["q_a"]]

    return q

def make_type_four_question(question):
    q = {}
    q["q"] = question.id
    q["q_string"] = question.question
    q["type"] = "4"
    q["attributes"] = {}
    q["attributes"]["question_image"] = json.loads(question.question_images)["location"]
    q["attributes"]["radio1_image"] = json.loads(question.option_a)["image_location"]
    q["attributes"]["radio1_text"] = json.loads(question.option_a)["text"]
    q["attributes"]["radio2_image"] = json.loads(question.option_b)["image_location"]
    q["attributes"]["radio2_text"] = json.loads(question.option_b)["text"]
    q["attributes"]["radio3_image"] = json.loads(question.option_c)["image_location"]
    q["attributes"]["radio3_text"] = json.loads(question.option_c)["text"]
    q["attributes"]["radio4_image"] = json.loads(question.option_d)["image_location"]
    q["attributes"]["radio4_text"] = json.loads(question.option_d)["text"]

    return q

def make_type_five_question(question):
    # this one has a place holder in the text so we'll need to split it up
    q = {}
    q["q"] = question.id

    #get the string and figure out where the images are
    question_string = json.loads(question.question)["question"]
    
    replace_with_image = json.loads(question.question)["images"]

    #if there is nothing to replace... then we'll just return the string later
    if "<q_1>" in question_string:
        question_string = question_string.replace("<q_1>","<img src='{}'>".format(replace_with_image[0]))
        
    if "<q_2>" in question_string:
        question_string = question_string.replace("<q_2>","<img src='{}'>".format(replace_with_image[1]))

    q["q_string"] = question_string
    q["type"] = "5"
    q["attributes"] = {}
    q["attributes"]["radio1_image"] = json.loads(question.option_a)["image_location"]
    q["attributes"]["radio1_text"] = json.loads(question.option_a)["text"]
    q["attributes"]["radio2_image"] = json.loads(question.option_b)["image_location"]
    q["attributes"]["radio2_text"] = json.loads(question.option_b)["text"]
    q["attributes"]["radio3_image"] = json.loads(question.option_c)["image_location"]
    q["attributes"]["radio3_text"] = json.loads(question.option_c)["text"]
    q["attributes"]["radio4_image"] = json.loads(question.option_d)["image_location"]
    q["attributes"]["radio4_text"] = json.loads(question.option_d)["text"]

    return q