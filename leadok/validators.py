import datetime
import decimal
from decimal import Decimal
import calendar
import arrow
from flask import g

from leadok.common import handle_exception
from leadok import app
import leadok.payments
import leadok.settings

logger = app.logger


class ValidationError(Exception):
    pass


@handle_exception((arrow.now('Europe/Moscow').year, arrow.now('Europe/Moscow').month))
def form_get_year_and_month(args):
    if 'year' in args and 'month' in args:
        year = int(args['year'])
        month = int(args['month'])
        if year > 2012 and month > 0 and month < 13:
            return (year, month)
    return (arrow.now('Europe/Moscow').year, arrow.now('Europe/Moscow').month)


@handle_exception({})
def form_to_dict(args, user, default_all=False, timezone='Europe/Moscow'):
    data = {}

    now = arrow.now('Europe/Moscow')

    try:
        data['year'] = int(args['year'])
        if data['year'] < 2014 or data['year'] > 2099: raise TypeError
    except Exception:
        data['year'] = now.year

    try:
        data['month'] = int(args['month'])
        if data['month'] not in range(1, 13): raise TypeError
    except Exception:
        data['month'] = now.month

    if user.is_admin():
        try:
            data['uid'] = str(args['uid'])
            if data['uid'] not in g.CUSTOMERS:
                raise TypeError
        except Exception:
            if default_all:
                data['uid'] = '__everyone__'
            else:
                data['uid'] = g.CUSTOMERS[0]
        if data['uid'] == '__everyone__':
            data['uid'] = None
    else:
        data['uid'] = user.uid

    data['uids'] = g.CUSTOMERS

    data['today'] = now

    try:
        data['day_from'] = datetime.datetime.strptime(args['date_from'], '%d.%m.%Y')
        data['day_till'] = datetime.datetime.strptime(args['date_from'], '%d.%m.%Y')
        data['date_from'] = arrow.get(data['day_from'], timezone).floor('day')
        data['date_till'] = arrow.get(data['day_till'], timezone).ceil('day')
        assert data['date_till'] >= data['date_from']
    except Exception:
        now = arrow.now(timezone)
        data['date_from'] = now.replace(days=-6).ceil('day')
        data['date_till'] = now
        data['day_from'] = data['date_from'].date()
        data['day_till'] = data['date_till'].date()
    data['datetime_span'] = (data['date_from'], data['date_till'])
    data['timezone'] = timezone
    data['day_today'] = arrow.now(timezone).date()

    try:
        data['status'] = int(args['status'])
    except Exception:
        data['status'] = 99
    if data['status'] == 99:
        data['status'] = None

    return data


@handle_exception({})
def get_admin_leads_data(args, timezone='Europe/Moscow'):
    data = {}

    # DATETIMES
    try:
        data['day_from'] = datetime.datetime.strptime(args['date_from'], '%d.%m.%Y')
        data['day_till'] = datetime.datetime.strptime(args['date_till'], '%d.%m.%Y')
        arrow_from = arrow.get(data['day_from'], timezone).floor('day')
        arrow_till = arrow.get(data['day_till'], timezone).ceil('day')
        assert arrow_till > arrow_from
    except Exception:
        now = arrow.now(timezone)
        arrow_from = now.replace(days=-6).floor('day')
        arrow_till = now.ceil('day')
        data['day_from'] = arrow_from.date()
        data['day_till'] = arrow_till.date()
    data['datetime_span'] = (arrow_from, arrow_till)
    data['timezone'] = timezone

    # STATUSES
    try:
        status = int(args['status'])
    except Exception:
        status = None

    data['statuses'] = None if status is None else [status]

    # UIDS
    try:
        _uid = str(args['uid'])
    except Exception:
        _uid = '__everyone__'
    data['uid'] = None if _uid == '__everyone__' else _uid

    return data


def get_dates_span(args):
    try:
        year = int(args['year'])
        month = int(args['month'])
        assert year > 0
        assert month > 0 and month < 13
        last_day_of_month = calendar.monthrange(year, month)[1]
        date_from = datetime.date(year, month, 1)
        date_till = datetime.date(year, month, last_day_of_month)
        today = arrow.now('Europe/Moscow').date()
        if today < date_till:
            date_till = today
        return date_from, date_till
    except Exception:
        pass
    try:
        from_s = str(args['date_from'])
        till_s = str(args['date_till'])
        date_from = arrow.get(from_s, 'DD.MM.YYYY').date()
        date_till = arrow.get(till_s, 'DD.MM.YYYY').date()
        if date_from > date_till:
            raise TypeError
    except Exception:
        today = arrow.now('Europe/Moscow').date()
        date_from = datetime.date(today.year, today.month, 1)
        date_till = today
    return (date_from, date_till)



@handle_exception(None)
def form_get_payment(form, uid, timezone='Europe/Moscow'):
    amount = Decimal(form['sum'])
    try:
        date = arrow.get(form['date'] + ' ' + form['time'],
                         'DD.MM.YYYY HH:mm').replace(tzinfo=timezone)
    except Exception:
        date = arrow.now('Europe/Moscow')
    method = form['comment']
    return leadok.payments.Payment(uid, amount, date, method, 'pending')


@handle_exception(None)
def form_get_payment_admin(form, timezone='Europe/Moscow'):
    uid = form['uid'].strip()
    amount = Decimal(form['sum'])
    try:
        date = arrow.get(form['date'] + ' ' + form['time'],
                         'DD.MM.YYYY HH:mm').replace(tzinfo=timezone)
    except Exception:
        date = arrow.now('Europe/Moscow')
    method = form['method']
    comment = form['comment']
    return leadok.payments.Payment(uid, amount, date,
                                   method, 'accepted', comment=comment)


def form_get_customer_settings(form):
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    filtered_data = {}
    allowed_keys_num = ['num_leads_required_' + day for day in days]
    for key in form:
        if key in allowed_keys_num:
            try:
                if int(form[key]) >= 0:
                    filtered_data[key] = int(form[key])
            except Exception: pass

    allowed_keys_hours = []
    allowed_keys_hours += ['working_hours_start_' + day for day in days]
    allowed_keys_hours += ['working_hours_finish_' + day for day in days]
    for key in form:
        if key in allowed_keys_hours:
            try:
                arrow.get(form[key], 'HH:mm')
                filtered_data[key] = form[key]
            except Exception as e:
                pass

    filtered_data['on'] = 'on' in form
    filtered_data['buffer_customer'] = 'buffer_customer' in form
    filtered_data['send_email'] = 'send_email' in form

    try:
        filtered_data['balance_limit'] = float(form['balance_limit'])
    except Exception:
        filtered_data['balance_limit'] = 0

    try:
        filtered_data['notes'] = form['notes']
    except Exception:
        filtered_data['notes'] = ''

    try:
        filtered_data['allow_to_set_req'] = 'allow_to_set_req' in form
    except Exception:
        filtered_data['allow_to_set_req'] = False

    return filtered_data


@handle_exception({'sort_by_brack_percent': True})
def get_phrases_stats_options(args):
    try:
        if args['sort-crit'] == 'sort_by_brack':
            return {'sort_by_brack_percent': True}
    except Exception:
        pass
    return {'sort_by_brack_percent': False}


def get_adwords_expense_options(form):
    try:
        data = {}
        data['date'] = arrow.get(form['date'], 'DD.MM.YYYY').format('YYYY-MM-DD')
        data['amount'] = float(form['expense'])
        return data
    except Exception:
        raise ValidationError


def get_new_cost(form):
    cost = {}
    cost['date'] = arrow.get(str(form['date']), 'DD.MM.YYYY').date()
    cost['name'] = str(form['name'])
    cost['amount'] = Decimal(str(form['amount'])).quantize(Decimal('0.00'))
    return cost


@handle_exception({})
def get_settings(form):
    logger.debug('Settings POST form : {}'.format(form))
    all_settings = leadok.settings.get_all_settings()
    prev_settings = dict((s.key, s) for s in all_settings)
    next_settings = {}
    for key in form:
        next_settings[key] = form[key]
    for key, s in prev_settings.items():
        if key not in next_settings and s.present_in_web_interface():
            next_settings[key] = 'No'
    logger.debug('new_settings dict = {}'.format(next_settings))
    return next_settings
