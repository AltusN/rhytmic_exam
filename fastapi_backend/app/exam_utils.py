import json
import math
import os
from typing import Any, Dict, Sequence


def _safe_json_load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def make_question_for_exam(question: Any) -> Dict[str, Any]:
    question_type = str(question.question_type)
    builders = {
        "1": _make_type_one_question,
        "2": _make_type_two_question,
        "3": _make_type_three_question,
        "4": _make_type_four_question,
        "5": _make_type_five_question,
    }
    return builders.get(question_type, _make_type_one_question)(question)


def _make_type_one_question(question: Any) -> Dict[str, Any]:
    return {
        "q": question.question_id,
        "q_string": question.question,
        "type": "1",
        "option_a": question.option_a,
        "option_b": question.option_b,
        "option_c": question.option_c,
        "option_d": question.option_d,
    }


def _make_type_two_question(question: Any) -> Dict[str, Any]:
    header = _safe_json_load(question.question_images, {})
    path = header.get("path", {}).get("location", "")

    return {
        "q": question.question_id,
        "q_string": question.question,
        "type": "2",
        "attributes": {
            "header": [os.path.join(path, x) for x in _safe_json_load(question.question_images, {}).get("path", {}).get("filename", [])],
            "radio1": [os.path.join(path, x) for x in _safe_json_load(question.option_a, {}).get("path", {}).get("filename", [])],
            "radio2": [os.path.join(path, x) for x in _safe_json_load(question.option_b, {}).get("path", {}).get("filename", [])],
            "radio3": [os.path.join(path, x) for x in _safe_json_load(question.option_c, {}).get("path", {}).get("filename", [])],
            "radio4": [os.path.join(path, x) for x in _safe_json_load(question.option_d, {}).get("path", {}).get("filename", [])],
        },
    }


def _make_type_three_question(question: Any) -> Dict[str, Any]:
    header = _safe_json_load(question.question_images, {})
    path = header.get("path", {}).get("location", "")

    return {
        "q": question.question_id,
        "q_string": question.question,
        "type": "3",
        "images": [os.path.join(path, x) for x in _safe_json_load(question.question_images, {}).get("path", {}).get("filename", [])],
        "option_a": _safe_json_load(question.option_a, {}).get("q_a", []),
        "option_b": _safe_json_load(question.option_b, {}).get("q_a", []),
        "option_c": _safe_json_load(question.option_c, {}).get("q_a", []),
        "option_d": _safe_json_load(question.option_d, {}).get("q_a", []),
    }


def _make_type_four_question(question: Any) -> Dict[str, Any]:
    option_a = _safe_json_load(question.option_a, {})
    option_b = _safe_json_load(question.option_b, {})
    option_c = _safe_json_load(question.option_c, {})
    option_d = _safe_json_load(question.option_d, {})

    return {
        "q": question.question_id,
        "q_string": question.question,
        "type": "4",
        "attributes": {
            "question_image": _safe_json_load(question.question_images, {}).get("location"),
            "radio1_image": option_a.get("image_location"),
            "radio1_text": option_a.get("text"),
            "radio2_image": option_b.get("image_location"),
            "radio2_text": option_b.get("text"),
            "radio3_image": option_c.get("image_location"),
            "radio3_text": option_c.get("text"),
            "radio4_image": option_d.get("image_location"),
            "radio4_text": option_d.get("text"),
        },
    }


def _make_type_five_question(question: Any) -> Dict[str, Any]:
    q_payload = _safe_json_load(question.question, {})
    question_string = q_payload.get("question", question.question)
    replace_with_image = q_payload.get("images", [])

    if "<q_1>" in question_string and len(replace_with_image) > 0:
        question_string = question_string.replace("<q_1>", f"<img src='{replace_with_image[0]}'>")
    if "<q_2>" in question_string and len(replace_with_image) > 1:
        question_string = question_string.replace("<q_2>", f"<img src='{replace_with_image[1]}'>")

    option_a = _safe_json_load(question.option_a, {})
    option_b = _safe_json_load(question.option_b, {})
    option_c = _safe_json_load(question.option_c, {})
    option_d = _safe_json_load(question.option_d, {})

    return {
        "q": question.question_id,
        "q_string": question_string,
        "type": "5",
        "attributes": {
            "radio1_image": option_a.get("image_location"),
            "radio1_text": option_a.get("text"),
            "radio2_image": option_b.get("image_location"),
            "radio2_text": option_b.get("text"),
            "radio3_image": option_c.get("image_location"),
            "radio3_text": option_c.get("text"),
            "radio4_image": option_d.get("image_location"),
            "radio4_text": option_d.get("text"),
        },
    }


def calculate_theory_score(user_answers: Dict[str, str], actual_answers: Dict[str, str]) -> tuple[float, Dict[str, list[str | None]]]:
    total = len(actual_answers)
    if total == 0:
        return 0.0, {}

    correct = 0
    incorrect_answers: Dict[str, list[str | None]] = {}

    for key, actual in actual_answers.items():
        user_choice = user_answers.get(key, "E")
        if actual == user_choice:
            correct += 1
        else:
            incorrect_answers[key] = [actual, user_answers.get(key)]

    percentage = round(correct / total * 100, 1)
    return percentage, incorrect_answers


def calculate_practical_score(user_answers: Dict[str, str], actual_answers: Sequence[Any]) -> tuple[float, Dict[str, Dict[str, list[Any]]]]:
    user_result: Dict[str, list[Any]] = {}
    total_score = 0.0

    for answer in actual_answers:
        user_answer = user_answers.get(answer.internal_question_value)
        user_answer = None if user_answer == "" else user_answer

        if user_answer:
            user_answer = _sanitize_user_answer(user_answer)
            mark = get_practical_mark(str(answer.control_score), str(user_answer))
        else:
            mark = 0

        user_result[answer.internal_question_value] = [
            answer.discipline,
            answer.result_question_value,
            answer.control_score,
            user_answer if user_answer is not None else "-1",
            mark,
        ]

        total_score += float(mark)

    percentage = _round_half((total_score / 100) * 100)
    grouped = _sort_practical_result(user_result)
    return percentage, grouped


def get_practical_mark(control_score: str, user_score: str) -> float:
    if control_score == user_score:
        return 5

    difference = _round_half(abs(float(control_score) - float(user_score)), decimal=2)
    point_allocation = [x * 0.25 for x in range(1, 20)][::-1]
    diff_arr = [_round_half(x * 0.05) for x in range(1, 20)]

    if difference >= 1 or difference <= 0:
        return 0
    return point_allocation[diff_arr.index(difference)]


def _round_half(n: float, decimal: int = 2) -> float:
    multiplier = 10**decimal
    return math.floor(n * multiplier + 0.5) / multiplier


def _sort_practical_result(result: Dict[str, list[Any]]) -> Dict[str, Dict[str, list[Any]]]:
    practical_answers: Dict[str, Dict[str, list[Any]]] = {}

    current_apparatus = ""
    for answer in result.values():
        if current_apparatus != answer[0]:
            current_apparatus = answer[0]
            if current_apparatus not in practical_answers:
                practical_answers[current_apparatus] = {}

        practical_answers[current_apparatus][answer[1]] = [answer[2], answer[3], answer[4]]

    return practical_answers


def _sanitize_user_answer(answer: str) -> str:
    if not answer:
        return answer

    if answer[0] == ".":
        answer = "0" + answer

    return answer.replace("/", ".").replace(",", ".").replace("-", "")
