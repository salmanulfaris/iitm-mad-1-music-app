from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import redirect, url_for

# FLASK LOGIN CONFIG
login_manager = LoginManager()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('main.login'))


# SQLALCHEMY LOGIN
db = SQLAlchemy()
