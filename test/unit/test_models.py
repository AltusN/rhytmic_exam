
def test_new_user(new_user):
    """
        Test new create users
    """
    pwd = "cat"

    new_user.set_password(pwd)

    assert new_user.email == "james@may.com"
    assert new_user.name == "James"
    assert new_user.surname == "May"
    assert new_user.sagf_id == "123"
    assert True is new_user.check_password(pwd)

def test_new_user_is_enabled(new_user):
    """
        check if the new iser is enabled
    """
    assert not new_user.is_enabled()