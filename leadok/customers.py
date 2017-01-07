import collections
import datetime
import decimal
from decimal import Decimal
import arrow
from sqlalchemy import select, func, and_

import leadok.database
import leadok.payments
import leadok.leads
import leadok.domains
from leadok.database import engine
from leadok.common import handle_exception

from leadok import app

logger = app.logger


class Customer:
    def __init__(self, d):
        self._d = d
        self.uid = d['uid']
        self.on = d['on']
        self.notes = d['notes']
        self.phone = d.get('phone', '')
        self.email = d.get('email', '')
        self.balance_shift = d['balance_shift']
        self.balance_limit = d['balance_limit']
        self.email_needed = d['email_needed']
        self.enabled = self.on
        try:
            self.timezone = d['timezone']
        except KeyError:
            self.timezone = 'Europe/Moscow'

    def __repr__(self):
        return '<Customer {}>'.format(self.uid)

    def get_id(self): return self.uid
    def is_active(self): return True
    def is_anonymous(self): return False
    def is_authenticated(self): return True
    def is_admin(self): return False

    def get_domain(self):
        return leadok.domains.get_domain_by_name(self._d['domain'])

    def is_password_valid(self, password):
        if not isinstance(password, str) or not password:
            return False
        return password == self._d['password']

    @handle_exception(False)
    def is_test(self):
        return self.uid.strip().lower() == 'test'

    @handle_exception(True)
    def is_off(self): return not self.on

    @handle_exception(True)
    def is_strict(self):
        return not self._d['buffer']

    def is_buffer(self):
        return not self.is_strict()

    @handle_exception(True)
    def is_lead_needed(self, lead):
        if lead['domain'] == 'jurist-msk' and 'mirzakonov.ru' in lead['source']:
            return False
        return True

    @handle_exception(0)
    def get_price(self): return self._d['price']

    @handle_exception(None)
    def get_last_lead_time(self):
        return leadok.leads.\
            get_most_recent_lead(uid=self.uid, exclude_bracks=True)['date']


    @handle_exception(None)
    def get_date_registered(self):
        return self._d['date_registered']


    @handle_exception(Decimal('-35.00'))
    def get_balance(self, modified=False):
        minus = leadok.leads.get_price_sum(uid=self.uid,
                                           exclude_bracks=True)
        plus = leadok.payments.get_total_for(self.uid)
        balance = Decimal(plus) - Decimal(minus) + Decimal(self.balance_shift)
        if modified:
            return balance - Decimal(self.balance_limit)
        return balance

    @handle_exception(0)
    def get_now(self):
        span = arrow.now(self.timezone).span('day')
        return leadok.leads.count_leads(uid=self.uid,
                                        datetime_span=span,
                                        exclude_bracks=True)

    @handle_exception(0)
    def get_req(self, day_of_week=None):
        if self.is_test():
            return 0
        if day_of_week is None:
            day_of_week = arrow.now('Europe/Moscow').format('dddd').lower()
        req = self._d['req_' + day_of_week.lower()[:3]]
        if not isinstance(req, int) or req < 0:
            raise TypeError('"req" field not appropriate type or < 0')
        return req


    @handle_exception(False)
    def set_req(self, req):
        cs = leadok.database.Customer.__table__
        data = dict(req_mon=req,
                    req_tue=req,
                    req_wed=req,
                    req_thu=req,
                    req_fri=req,
                    req_sat=req,
                    req_sun=req)
        q = cs.update(cs.c.uid == self.uid).values(data)
        engine.execute(q).close()


    @handle_exception(False)
    def is_setting_req_allowed(self):
        return self._d['allow_to_set_req']

    @property
    def seconds_till_finish(self):
        time_now = arrow.now(self.timezone)
        fi = self.get_working_hours()[1].time()
        time_finish = time_now.replace(hour=fi.hour,
                                       minute=fi.minute,
                                       second=fi.second)
        if time_finish > time_now:
            return (time_finish - time_now).seconds
        else:
            return 0

    def inside_working_hours(self):
        return not self.has_not_started() and not self.already_finished()

    def has_not_started(self):
        time_now = arrow.now(self.timezone)
        time_start = self.get_working_hours()[0]
        return time_now < time_start

    def already_finished(self):
        time_now = arrow.now(self.timezone)
        time_finish = self.get_working_hours()[1]
        return time_now > time_finish

    @property
    def left(self):
        # how many leads left for this customer today
        if self.is_off() or self.is_test():
            return 0
        # if not self.inside_working_hours():
        #     return 0
        balance_modified = self.get_balance(modified=True)
        price = self.get_price()
        if balance_modified < price:
            return 0
        left_by_schedule = self.get_req() - self.get_now()
        if left_by_schedule < 0:
            return 0
        try:
            left_by_balance = float(balance_modified) // float(price)
        except ZeroDivisionError:
            left_by_balance = 100
        return min(left_by_schedule, left_by_balance)

    def leads_remaining_today(self):
        return self.left

    @handle_exception(False)
    def set_settings(self, data):
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        cs = leadok.database.Customer.__table__
        for day in days:
            try:
                h_st = int(data['working_hours_start_' + day].split(':')[0])
                m_st = int(data['working_hours_start_' + day].split(':')[1])
                h_fi = int(data['working_hours_finish_' + day].split(':')[0])
                m_fi = int(data['working_hours_finish_' + day].split(':')[1])
                req = int(data['num_leads_required_' + day])
                q = cs.update(cs.c.uid == self.uid).\
                       values({'beg_' + day: datetime.time(h_st, m_st),
                               'end_' + day: datetime.time(h_fi, m_fi),
                               'req_' + day: req})
                engine.execute(q).close()
            except Exception:
                pass
            for key in ['on', 'balance_limit', 'notes', 'allow_to_set_req']:
                try:
                    q = cs.update(cs.c.uid == self.uid).\
                           values({key: data[key]})
                    engine.execute(q).close()
                except Exception:
                    pass
            try:
                q = cs.update(cs.c.uid == self.uid).\
                       values(buffer=data['buffer_customer'])
                engine.execute(q).close()
            except Exception:
                pass
            try:
                q = cs.update(cs.c.uid == self.uid).\
                       values(email_needed=data['send_email'])
                engine.execute(q).close()
            except Exception:
                pass
        logger.debug('Settings successfully set for '
            'customer [{}]'.format(self.uid))
        return True


    @handle_exception([])
    def get_status(self):
        status = []
        if self.is_off():
            status.append('Выключен')
        if self.get_balance(modified=True) < self.get_price():
            status.append('Баланса недостаточно')
        if self.get_now() >= self.get_req():
            status.append('Заявки не нужны или все получены')
        if not self.inside_working_hours():
            status.append('Нерабочее время')
        return status

    @handle_exception((arrow.now('Europe/Moscow').replace(hour=9, minute=0),
                       arrow.now('Europe/Moscow').replace(hour=18, minute=0)))
    def get_working_hours(self, day_of_week=None, hours_only=False):
        # Return today's working hours of customer.
        time_now = arrow.now(self.timezone)
        if day_of_week is None:
            day_of_week = time_now.format('dddd').lower()
        st = self._d['beg_' + day_of_week[:3]]
        fi = self._d['end_' + day_of_week[:3]]
        if hours_only:
            return st, fi
        start = time_now.replace(hour=st.hour,
                                 minute=st.minute,
                                 second=st.second)
        finish = time_now.replace(hour=fi.hour,
                                  minute=fi.minute,
                                  second=st.second)
        return start, finish


class Customers(collections.Iterable, collections.Sized):

    def __init__(self, domain=None):
        cs = leadok.database.Customer.__table__
        cond = [
            cs.c.archived == False,
        ]
        if domain is not None:
            cond.append(cs.c.domain == domain.name)
        q = select([cs]).where(and_(*cond)).order_by(cs.c.uid)
        self._data = list(engine.execute(q))
        self.uids = [c['uid'] for c in self._data]

    @handle_exception(None)
    def get(self, uid):
        if uid not in self.uids:
            return None
        for item in self._data:
            if item['uid'] == uid:
                return Customer(dict(item))
        return None

    def __iter__(self):
        for uid in self.uids:
            yield self.get(uid)

    def __len__(self): return len(self.uids)


def get_customers(domain=None):
    return Customers(domain=domain)


def get_customer(uid):
    cs = leadok.database.Customer.__table__
    q = select([cs]).where(cs.c.uid == uid).\
                     where(cs.c.archived == False)
    row = engine.execute(q).first()
    return None if row is None else Customer(dict(row))


@handle_exception(False)
def increment_counter(uid):
    n = get_counter(uid)
    cs = leadok.database.Customer.__table__
    q = cs.update(cs.c.uid == uid).\
           values(new=n + 1)
    engine.execute(q).close()
    return True


@handle_exception(False)
def reset_counter(uid):
    cs = leadok.database.Customer.__table__
    q = cs.update(cs.c.uid == uid).values(new=0)
    engine.execute(q).close()
    return True


@handle_exception(-14)
def get_counter(uid):
    cs = leadok.database.Customer.__table__
    q = select([cs.c.new]).where(cs.c.uid == uid)
    return engine.execute(q).scalar()


@handle_exception(0)
def get_customers_count_for_domain(domain_name):
    cs = leadok.database.Customer.__table__
    q = select([func.count(cs.c.uid)]).where(cs.c.domain == domain_name)
    return engine.execute(q).scalar()
