# trails/threadlocals.py
import threading

_user = threading.local()

def get_current_user():
    return getattr(_user, 'value', None)

def set_current_user(user):
    _user.value = user
