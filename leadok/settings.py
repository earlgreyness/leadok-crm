from collections import OrderedDict
import arrow
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.hybrid import hybrid_property
from leadok import app, db

logger = app.logger


class Setting(db.Model):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String)
    value = Column(String)
    _description = Column('description', String)
    default_value = Column(String)
    archived = Column(Boolean)

    @hybrid_property
    def description(self):
        if not self._description:
            return self.key
        else:
            return self._description

    @description.setter
    def description(self, value):
        self._description = value

    def is_yes_no(self):
        return self.value in ['Yes', 'No']

    def present_in_web_interface(self):
        return not self.archived

    def __repr__(self):
        return "<Setting '{}': '{}'>".format(self.key, self.value)


def get_setting_value(key):
    try:
        return Setting.query.filter_by(key=key).one().value
    except NoResultFound:
        return None


def get_all_settings():
    return Setting.query.order_by(Setting.key).all()


def update_settings(new_settings):
    for key, value in new_settings.items():
        try:
            setting = Setting.query.filter_by(key=key).one()
        except NoResultFound:
            continue
        if setting.value == value:
            continue
        if setting.is_yes_no() and value not in ['Yes', 'No']:
            continue
        setting.value = value
        db.session.commit()
        logger.info('Setting "{}" changed to '
                    '"{}"'.format(setting.key, setting.value))


def restore_default_settings():
    settings = get_all_settings()
    for setting in settings:
        setting.value = setting.default_value
    db.session.commit()


def get_default_timezone():
    fallback_timezone = 'Europe/Moscow'
    s = Setting.query.filter_by(key='timezone').first()
    if s is None:
        return fallback_timezone
    try:
        _ = arrow.now(s.value)
        return s.value
    except arrow.parser.ParserError:
        return fallback_timezone
