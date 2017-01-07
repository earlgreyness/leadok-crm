import time
import datetime
from datetime import timedelta
import random
from collections.abc import Mapping, MutableMapping
import collections.abc
import csv

import arrow
from sqlalchemy import select, and_, or_, func, Column, Integer, String, Unicode
from sqlalchemy import Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import PhoneNumber
from sqlalchemy_utils import ArrowType, PhoneNumberType

from leadok.common import get_only_digits, handle_exception
from leadok.common import truncate_string, pretty_number
from leadok.database import engine
from leadok.database import leads_history as leads_history_table
from leadok import app, db


logger = app.logger

NAME_MAX_LENGTH = 32
QUESTION_MAX_LENGTH = 1024


class StatusMixin:
    @classmethod
    def get_all(cls):
        return db.session.query(cls).order_by(cls.id).all()

    def __repr__(self):
        return "<{} '{}'>".format(type(self).__name__, self.name)


class LeadStatus(db.Model, StatusMixin):
    __tablename__ = 'lead_statuses'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_rus = Column(Unicode, nullable=False, unique=True)

    def is_brack_related(self):
        return 'brack_' in self.name

    def is_brack(self):
        return self.name in ['brack_pending', 'brack_accepted']


class LeadQuality(db.Model, StatusMixin):
    __tablename__ = 'lead_qualities'

    id = Column(Integer, nullable=False, unique=True)
    name = Column(String, primary_key=True)
    name_rus = Column(Unicode, unique=True, nullable=False)


class Lead(db.Model):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    question = Column(String)
    source = Column(String)
    date = Column(ArrowType(timezone=True))
    brack_report_date = Column(ArrowType(timezone=True))
    winner = Column(String)
    id2 = Column(Integer)
    status = Column(Integer)
    comment = Column(String)
    commentbrack = Column(String)
    price = Column(Float)
    domain = Column(String)
    giga_brack_notification = Column(String)
    brack_rejected_once = Column(Boolean)
    moderator_response = Column(String)
    status_text = Column(String, ForeignKey('lead_statuses.name'))
    quality_name = Column('quality', String, ForeignKey('lead_qualities.name'),
                          nullable=False, default='notset')

    quality = relationship('LeadQuality', foreign_keys='[Lead.quality_name]', lazy='joined')

    status_object = relationship('LeadStatus', foreign_keys='[Lead.status_text]', lazy='joined')

    @staticmethod
    def get_all_qualities():
        return LeadQuality.get_all()

    @staticmethod
    def get_all_statuses():
        return LeadStatus.get_all()

    def is_brack(self):
        return self.status_object.is_brack()

    def __getitem__(self, key):
        return self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return 'Lead({}, {})'.format(self.id, self.phone)


def export_leads_for_portal(filename):
    app.logger.info('Started exporting leads for portal...')
    leads = Lead.query.order_by(Lead.date.desc()).all()
    with open(filename, 'wt', encoding='utf8') as csv_file:
        writer = csv.writer(csv_file, delimiter='|')
        for lead in leads:
            row = [
                lead.date.format('YYYY-MM-DD HH:mm'),
                lead.source,
                lead.status_text,
                lead.question.replace('\n', ' ').replace('\r', ''),
                lead.commentbrack.replace('\n', ' ').replace('\r', ''),
            ]
            writer.writerow([str(item) for item in row])
    app.logger.info('Export completed.')


@handle_exception(None)
def get_lead_by_id(lead_id):
    return Lead.query.get(lead_id)


@handle_exception(None)
def get_lead_by_id2(uid, lead_id2):
    return Lead.query.filter(Lead.winner == uid, Lead.id2 == lead_id2).one()


@handle_exception(None)
def get_most_recent_lead(**kwargs):
    conditions = define_conditions(**kwargs)
    return (
        db.session.query(Lead)
                  .filter(conditions)
                  .order_by(Lead.date.desc())
                  .first()
    )


@handle_exception([])
def get_leads(**kwargs):
    conditions = define_conditions(**kwargs)
    return (
        db.session.query(Lead)
                  .filter(conditions)
                  .order_by(Lead.date.desc())
                  .all()
    )


@handle_exception(0)
def count_leads(**kwargs):
    conditions = define_conditions(**kwargs)
    return db.session.query(Lead.id).filter(conditions).count()


def get_leads_awaiting_brack():
    BRACK_PENDING = 1
    return get_leads(status=BRACK_PENDING,
                     exclude_test=True)


@handle_exception([])
def get_duplicates(lead, only_recent=False):
    # Here lead can be either a dict or a Lead instance
    # Remember this fact.
    try:
        phone = lead.phone
        lead_id = lead.id
    except AttributeError:
        # It's a dict.
        phone = lead.get('phone')
        lead_id = lead.get('id')
    if not phone:
        return []
    query = (
        db.session.query(Lead)
                  .filter(Lead.phone == phone)
                  .filter(Lead.id != lead_id)
    )
    if only_recent:
        since = arrow.now() - timedelta(days=30)
        query = query.filter(Lead.date > since)
    return query.order_by(Lead.date.desc()).all()


@handle_exception(0.0)
def get_price_sum(**kwargs):
    conditions = define_conditions(**kwargs)
    q = select([func.sum(Lead.__table__.c.price)]).where(conditions)
    result = engine.execute(q).scalar()
    return 0.0 if result is None else result


def define_conditions(**kwargs):
    t = Lead.__table__
    filters = []
    exclude_bracks = kwargs.get('exclude_bracks', False)
    domain = kwargs.get('domain', None)
    exclude_test = kwargs.get('exclude_test', False)
    datetime_span = kwargs.get('datetime_span', None)
    uid = kwargs.get('uid', None)
    uids = kwargs.get('uids', None)
    domains = kwargs.get('domains', None)
    statuses = kwargs.get('statuses', None)
    status = kwargs.get('status', None)
    ignored_statuses = kwargs.get('ignored_statuses', None)
    source = kwargs.get('source', None)
    only_calls = kwargs.get('only_calls', False)
    if exclude_bracks:
        filters.append(~t.c.status.in_([1, 2]))
    if only_calls:
        filters.append(t.c.source.like('%/zvonok%'))
    if datetime_span is not None:
        datetime_from = arrow.get(datetime_span[0])
        datetime_till = arrow.get(datetime_span[1])
        filters.append(t.c.date >= datetime_from)
        filters.append(t.c.date <= datetime_till)
    if uid is not None:
        filters.append(t.c.winner == uid)
    if uids is not None:
        filters.append(t.c.winner.in_(uids))
    if uids is None and uid is None and exclude_test:
        filters.append(t.c.winner != 'test')
    if domain is not None:
        filters.append(t.c.domain == domain)
    if domains is not None:
        filters.append(t.c.domain.in_(domains))
    if status is not None:
        filters.append(t.c.status == status)
    if statuses is not None:
        filters.append(t.c.status.in_(statuses))
    if ignored_statuses is not None:
        filters.append(~t.c.status.in_(ignored_statuses))
    if source is not None:
        filters.append(t.c.source == source)
    return and_(*filters)



@handle_exception([])
def get_lead_history(lead_id):
    t = leads_history_table
    q = select([t]).where(t.c.lead_id == lead_id).\
        order_by(t.c.date.desc())
    return list(engine.execute(q))


@handle_exception()
def record_that_lead_was_seen_by_user(lead_id, ip_address):
    t = leads_history_table
    q = t.insert().values(action='seen_by_user',
                          lead_id=lead_id,
                          comment=str(ip_address))
    engine.execute(q).close()


@handle_exception()
def upgrade_lead(lead_id, **vals):
    t = Lead.__table__
    q = t.update(t.c.id == lead_id).values(**vals)
    engine.execute(q).close()


def prepare_incoming_lead(raw_lead, lead_date=None):
    lead = {}

    lead['date'] = arrow.utcnow()
    if lead_date is not None:
        try:
            lead['date'] = arrow.get(lead_date)
        except Exception:
            pass

    try:
        lead['phone'] = get_only_digits(raw_lead['phone'])
    except Exception:
        lead['phone'] = ''
    for key in ['name', 'question', 'source', 'domain']:
        try:
            lead[key] = str(raw_lead[key]).strip()
        except Exception:
            lead[key] = ''
    lead['name'] = truncate_string(lead['name'],
                                   NAME_MAX_LENGTH,
                                   ellipsis='')
    lead['question'] = truncate_string(lead['question'],
                                       QUESTION_MAX_LENGTH,
                                       ellipsis='')
    if not lead['domain']:
        lead['domain'] = 'jurist-msk'
    return lead


def insert_new_lead(lead, winner):
    t = Lead.__table__
    q = select([func.max(t.c.id2)]).\
        where(t.c.winner == winner.uid)
    lead['winner'] = winner.uid
    lead['price'] = winner.get_price()
    for _ in range(5):
        try:
            max_id2 = engine.execute(q).scalar() or 0
            lead['id2'] = max_id2 + 1
            assigned_id = engine.\
                execute(t.insert().values(lead)).inserted_primary_key[0]
            logger.info('Lead inserted into DB, id assigned: {}'.format(assigned_id))
            return
        except Exception:
            time.sleep(0.25)
    for _ in range(5):
        try:
            max_id2 = engine.execute(q).scalar() or 0
            lead['id2'] = max_id2 + random.choice(range(5, 13))
            assigned_id = engine.\
                execute(t.insert().values(lead)).inserted_primary_key[0]
            logger.info('Lead inserted into DB, id assigned: {}'.format(assigned_id))
            return
        except Exception:
            time.sleep(0.5)
    logger.error('Lead has not been inserted into DB')


@handle_exception()
def report_brack(lead_id, brack_reason):
    set_status(lead_id, 1)
    upgrade_lead(lead_id,
                 commentbrack=brack_reason,
                 brack_report_date=arrow.utcnow())
    lead = get_lead_by_id(lead_id)
    logger.info('Brack reported for lead '
        '{} ({}) ({})'.format(lead_id, lead.winner, brack_reason))


@handle_exception()
def reject_brack(lead_id, moderator_response=''):
    set_status(lead_id, 3)
    lead = get_lead_by_id(lead_id)
    new_commentbrack = lead.commentbrack + '\n[' + moderator_response + ']'
    upgrade_lead(lead_id,
                 moderator_response=moderator_response,
                 commentbrack=new_commentbrack,
                 brack_rejected_once=True)
    lead = get_lead_by_id(lead_id)
    logger.info('Brack rejected for lead '
        '{} ({})'.format(lead_id, lead.winner))


@handle_exception()
def accept_brack(lead_id, moderator_response=''):
    set_status(lead_id, 2)
    upgrade_lead(lead_id,
                 moderator_response=moderator_response)
    lead = get_lead_by_id(lead_id)
    logger.info('Brack accepted for lead '
        '{} ({}) ({})'.format(lead_id, lead.winner,
                            lead.commentbrack))


@handle_exception()
def set_status(lead_id, status):
    try:
        _status = db.session.query(LeadStatus).get(status)
        lead = get_lead_by_id(lead_id)
        lead.status = _status.id
        lead.status_text = _status.name
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

