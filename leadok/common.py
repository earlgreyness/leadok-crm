from functools import wraps
import traceback
import calendar
from collections import OrderedDict
from decimal import Decimal
import datetime
import arrow
from leadok import app

logger = app.logger

_month_numbers = range(1, 13)
_month_names = ('Январь Февраль Март Апрель Май Июнь '
               'Июль Август Сентябрь Октябрь Ноябрь Декабрь').split()
MONTHS = OrderedDict(zip(_month_numbers, _month_names))


def handle_exception(default_result=None):
    def real_decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                logger.error(traceback.format_exc())
                return default_result
        return wrapper
    return real_decorator


@handle_exception([])
def get_dates_range(year, month, until_today=True):
    num_days = calendar.monthrange(year, month)[1]
    today = arrow.now('Europe/Moscow').date()
    dates = []
    for n in range(1, num_days + 1):
        date = datetime.date(year, month, n)
        if until_today and date > today:
            break
        dates.append(date)
    return dates


@handle_exception([])
def get_days_list(date_from, date_till):
    day_count = (date_till - date_from).days + 1
    return [date_from + datetime.timedelta(n) for n in range(day_count)]


@handle_exception('')
def pretty_currency(num, template='0.01'):
    if num is None:
        return ''
    x = Decimal(num).quantize(Decimal(template))
    return '{:,}'.format(x).replace(',', ' ').replace('-', '–')


def pretty_number(s):
    # '84950000000' -> '8 (495) 000-00-00'
    try:
        if len(s) not in (10, 11):
            raise IndexError
        return '{} ({}) {}-{}-{}'.format(
            s[0], s[1:4], s[4:7], s[7:9], s[9:]
        )
    except Exception:
        return ''


def get_only_digits(phone_raw):
    TESTS = [
        ('7  (929) 968-5531', '89299685531'),
        ('9299685531', '89299685531'),
        ('889269294909', '89269294909'),
    ]
    try:
        phone = ''.join(ch for ch in phone_raw if ch.isdigit())
        if len(phone) == 12 and phone[0] == 8 and phone[1] == 8:
            return phone[1:]
        if len(phone) == 11 and phone[0] == '7':
            return '8' + phone[1:]
        if len(phone) == 10:
            return '8' + phone
        return phone
    except Exception:
        return ''


def truncate_string(s, n, ellipsis='...'):
    m = n - len(ellipsis)
    if m < 0:
        return ''
    else:
        return (s[:m] + ellipsis) if len(s) > m else s
