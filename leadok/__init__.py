from datetime import timedelta
from logging import FileHandler, NullHandler, Formatter, DEBUG, INFO
import arrow
from flask import Flask
from flask_login import AnonymousUserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from jinja2 import evalcontextfilter, Markup, escape


class CustomFileHandler(FileHandler):
    """
    A custom FileHandler implementation that allows log files
    to be organized by days.  TimedRotatingFileHandler does not work
    as expected because it does not rotate log files at midnight.

    This class differs from original FileHandler class only in
    that it uses dynamic filename based on current date.  baseFilename
    is not set at creation of the class time, but each time emit()
    is called.
    """
    def __init__(self, filename):
        FileHandler.__init__(self, filename, mode='a',
                             encoding='utf-8', delay=True)
        self.originalBaseFilename = filename

    def emit(self, record):
        self.baseFilename = self._get_current_filename()
        FileHandler.emit(self, record)
        self.close()

    def _get_current_filename(self):
        todays_date = arrow.now('Europe/Moscow').format('YYYY-MM-DD')
        return '{}{}.log'.format(self.originalBaseFilename,
                                 todays_date)


app = Flask(__name__)
app.config.from_object('leadok.config')

# LOGGING CONFIGURATION BEGIN
try:
    handler = CustomFileHandler(app.config['LOGS_BASE_FILENAME'])
except Exception:  # KeyError or OSError
    handler = NullHandler()
handler.setLevel(INFO)
handler.setFormatter(
    Formatter(
        '%(asctime)s [%(levelname)-5s] (%(module)-s:%(lineno)-d) %(message)s'
    )
)
app.logger.addHandler(handler)
app.logger.setLevel(DEBUG)
# LOGGING CONFIGURATION END


# flask-login anonymous user class

class Anonymous(AnonymousUserMixin):
    def is_admin(self):
        return False

    def get_balance(self):
        return 0.0

    def __init__(self):
        self.uid = '<Anonymous()>'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'
login_manager.anonymous_user = Anonymous


db = SQLAlchemy(app)


# For jinja2 templates
@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    lines = escape(value).replace('\r', '').split('\n')
    result = '\n\n'.join('{}<br>'.format(line) for line in lines)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


import leadok.views
