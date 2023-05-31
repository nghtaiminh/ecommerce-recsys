from flask import Blueprint
from .forms import LoginForm, RegistrationForm

auth = Blueprint("auth", __name__)


@auth.app_context_processor
def inject_form():
    return {"login_form": LoginForm(), "register_form": RegistrationForm()}


from . import views
