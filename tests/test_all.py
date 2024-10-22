from app.utils import get_user_by_username

def test_username():
    assert get_user_by_username() == str
