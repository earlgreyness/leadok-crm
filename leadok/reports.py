import calendar
import datetime
import decimal
from decimal import DivisionUndefined, InvalidOperation, Decimal, DivisionByZero

import arrow

from leadok.common import handle_exception, \
                          get_days_list
from leadok.common import get_dates_range
import leadok.leads
import leadok.customers
import leadok.costs
import leadok.domains


@handle_exception(0)
def _average(iterable, ignore_zeros=True):
    s = 0
    n = 0
    for x in iterable:
        if x is None:
            continue
        if x == 0 and ignore_zeros:
            continue
        s += x
        n += 1
    return s / n if n else None


@handle_exception([])
def get_stats(uid, year, month):
    days_in_month = calendar.monthrange(year, month)[1]
    data = {}
    data['year'] = year
    data['month'] = month
    data['uid'] = uid
    stats = []
    dates = get_dates_range(year, month)
    for day in dates:
        datetime_span = arrow.get(day, 'Europe/Moscow').span('day')
        total_price = leadok.leads.get_price_sum(uid=uid,
                                                 datetime_span=datetime_span,
                                                 exclude_bracks=True)
        n_leads_clean = leadok.leads.count_leads(uid=uid,
                                                 datetime_span=datetime_span,
                                                 exclude_bracks=True)
        n_leads_dirty = leadok.leads.count_leads(uid=uid,
                                                 datetime_span=datetime_span)
        if n_leads_clean > 0:
            lead_price = total_price / n_leads_clean
        else:
            lead_price = 0.0
        stats.append({"date": day,
                      "leads_num": n_leads_clean,
                      "lead_price": lead_price,
                      "leads_brack": n_leads_dirty - n_leads_clean,
                      "total_spent": total_price})
    data['stats'] = stats
    return data


@handle_exception({})
def get_stats_admin(uid, year, month):
    dates = get_dates_range(year, month)
    info = {}
    info['year'] = year
    info['month'] = month
    info['uid'] = uid
    info['lines'] = []
    for date in dates:
        datetime_span = arrow.get(date, 'Europe/Moscow').span('day')
        total_price = leadok.leads.get_price_sum(uid=uid,
                                                 datetime_span=datetime_span,
                                                 exclude_bracks=True)
        n_leads_clean = leadok.leads.count_leads(uid=uid,
                                                 datetime_span=datetime_span,
                                                 exclude_bracks=True)
        n_leads_dirty = leadok.leads.count_leads(uid=uid,
                                                 datetime_span=datetime_span)
        n_bracks = n_leads_dirty - n_leads_clean
        if n_leads_clean > 0:
            lead_price = total_price / n_leads_clean
        else:
            lead_price = 0.0
        try:
            bracks_percent = n_bracks / n_leads_dirty * 100
            buying_price = lead_price * (1 - bracks_percent / 100)
        except (ZeroDivisionError, DivisionUndefined, InvalidOperation):
            bracks_percent = None
            buying_price = None
        info['lines'].append({'date': date,
                              'num_leads': n_leads_clean,
                              'num_bracks': n_bracks,
                              'total_price': total_price,
                              'buying_price': buying_price,
                              'lead_price': lead_price,
                              'bracks_percent': bracks_percent})
    info['leads_total'] = sum(x['num_leads'] for x in info['lines'])
    info['bracks_total'] = sum(x['num_bracks'] for x in info['lines'])
    info['total_total_price'] = sum(x['total_price'] for x in info['lines'])
    info['avg_lead_price'] = _average(x['lead_price'] for x in info['lines'])
    try:
        info['av_lpb'] = (info['bracks_total'] /
                          (info['leads_total'] + info['bracks_total']) * 100)
        info['avg_buying_price'] = info['avg_lead_price'] * (1 - info['av_lpb'] / 100)
    except (ZeroDivisionError, DivisionUndefined, InvalidOperation, Exception):
        info['av_lpb'] = None
        info['avg_buying_price'] = None
    return info





@handle_exception({})
def get_costs(date_from, date_till):
    daily_data = []
    costs = leadok.costs.get_costs(date_from, date_till)
    for day in get_days_list(date_from, date_till):
        d = {}
        d['date'] = day
        datetime_span = arrow.get(day, 'Europe/Moscow').span('day')
        d['leads_clean'] = leadok.leads.count_leads(
            datetime_span=datetime_span,
            exclude_bracks=True,
            exclude_test=True,
        )
        d['spent_yandex'] = costs[day]['Yandex.Direct']
        d['spent_google'] = costs[day]['Google AdWords']
        d['spent_giga'] = costs[day]['giga']
        d['spent_wilstream'] = costs[day]['WILStream']
        d['spent_all'] = sum(costs[day][name] for name in costs[day])
        datetime_span = arrow.get(day, 'Europe/Moscow').span('day')
        d['earned'] = leadok.leads.get_price_sum(datetime_span=datetime_span,
                                                 exclude_bracks=True,
                                                 exclude_test=True)
        d['income'] = decimal.Decimal(d['earned']) - d['spent_all']

        d['leads_dirty'] = leadok.leads.count_leads(datetime_span=datetime_span,
                                                    exclude_test=True)
        d['bracks'] = d['leads_dirty'] - d['leads_clean']
        try:
            d['brack_percent'] = d['bracks'] / d['leads_dirty'] * 100
        except (ZeroDivisionError, DivisionUndefined, InvalidOperation):
            d['brack_percent'] = None

        try:
            d['lead_price_clean'] = d['spent_all'] / Decimal(d['leads_clean'])
        except (DivisionUndefined, DivisionByZero, InvalidOperation, ZeroDivisionError):
            d['lead_price_clean'] = 0
        daily_data.append(d)
    data = {}
    data['year'] = date_from.year
    data['month'] = date_from.month
    data['date_from_str'] = arrow.get(date_from).format('DD.MM.YYYY')
    data['date_till_str'] = arrow.get(date_till).format('DD.MM.YYYY')
    data['daily_data'] = daily_data
    names = [
        'spent_yandex', 'spent_google',
        'spent_giga', 'spent_wilstream',
        'spent_all', 'earned', 'income',
        'leads_clean', 'lead_price_clean',
        'bracks', 'leads_dirty',
    ]
    for name in names:
        data['total_' + name] = sum(x[name] for x in daily_data)
        data['avg_' + name] = _average((x[name] for x in daily_data), ignore_zeros=False)

    try:
        data['avg_brack_percent'] = data['total_bracks'] / data['total_leads_dirty'] * 100
    except Exception:
        data['avg_brack_percent'] = None

    return data




@handle_exception({})
def get_lead_stats(year, month):
    data = {}
    data['year'] = year
    data['month'] = month
    daily_data = []
    for date in get_dates_range(year, month):
        datetime_span = arrow.get(date, 'Europe/Moscow').span('day')
        line = {}
        line['date'] = date
        line['n_calls'] = leadok.leads.count_leads(datetime_span=datetime_span,
                                                   exclude_bracks=True,
                                                   only_calls=True,
                                                   exclude_test=True)
        line['n_leads_clean'] = leadok.leads.\
            count_leads(datetime_span=datetime_span,
                        exclude_bracks=True,
                        exclude_test=True)
        line['n_not_calls'] = line['n_leads_clean'] - line['n_calls']
        try:
            line['calls_ratio'] = line['n_calls'] / line['n_leads_clean'] * 100
        except (ZeroDivisionError, DivisionUndefined, InvalidOperation):
            line['calls_ratio'] = None

        line['brack_ratio_calls'] = 0

        line['brack_ratio_not_calls'] = 0

        line['brack_ratio_leads_clean'] = 0

        daily_data.append(line)

    data['avg_n_calls'] = _average(x['n_calls'] for x in daily_data)
    data['avg_n_not_calls'] = _average(x['n_not_calls'] for x in daily_data)
    data['avg_brack_ratio_calls'] = _average(x['brack_ratio_calls'] for x in daily_data)
    data['avg_brack_ratio_not_calls'] = _average(x['brack_ratio_not_calls'] for x in daily_data)
    data['avg_n_leads_clean'] = _average(x['n_leads_clean'] for x in daily_data)
    data['avg_brack_ratio_leads_clean'] = _average(x['brack_ratio_leads_clean'] for x in daily_data)

    data['sum_n_calls'] = sum(x['n_calls'] for x in daily_data)
    data['sum_n_not_calls'] = sum(x['n_not_calls'] for x in daily_data)
    data['sum_n_leads_clean'] = sum(x['n_leads_clean'] for x in daily_data)

    try:
        data['avg_calls_ratio'] = data['sum_n_calls'] / data['sum_n_leads_clean'] * 100
    except (ZeroDivisionError, DivisionUndefined, InvalidOperation):
        data['avg_calls_ratio'] = None

    data['daily_data'] = daily_data

    return data


def _get_trimmed_url(url):
    trimmed_0 = url.split('http://')[-1]
    trimmed_1 = trimmed_0.split('?')[0]
    return trimmed_1
    if len(trimmed_1.split('/')) == 4 and trimmed_1[3] != '':
        return trimmed_1
    return None



@handle_exception({'phrases': []})
def get_phrases_statistics(sort_by_brack_percent=True):
    phrases = {}
    leads = leadok.leads.get_leads()
    for item in leads:
        url = _get_trimmed_url(item['source'])
        if url is None:
            continue
        is_brack = item['status'] in [1, 2]
        if url not in phrases:
            data = {'total': 1, 'bracks': 1 if is_brack else 0}
            phrases[url] = data
        else:
            existing_data = phrases[url]
            new_data = {}
            new_data['total'] = existing_data['total'] + 1
            new_data['bracks'] = existing_data['bracks'] + (1 if is_brack else 0)
            phrases[url] = new_data
    results = []
    for key in phrases:
        d = {}
        d['url'] = key
        d['total'] = phrases[key]['total']
        d['bracks'] = phrases[key]['bracks']
        d['brack_percent'] = 100 * d['bracks'] / d['total']
        results.append(d)

    results_sorted_1 = sorted(results, key=lambda x: x['total'], reverse=True)

    results_sorted_2 = sorted(results, key=lambda x: x['brack_percent'], reverse=True)

    data = {}
    if sort_by_brack_percent:
        data['sort_by_brack_percent'] = True
        data['phrases'] = results_sorted_2
    else:
        data['sort_by_brack_percent'] = False
        data['phrases'] = results_sorted_1

    return data


@handle_exception({})
def get_domains_summary():
    data = {}
    data['domains_list'] = []
    domains = leadok.domains.get_domains()
    for domain in domains:
        line = {}
        line['domain'] = domain
        line['customers_count'] = leadok.customers.\
            get_customers_count_for_domain(domain.name)
        line['leads_count'] = leadok.leads.\
            count_leads(domain=domain.name,
                        exclude_bracks=True)
        line['last_lead_time'] = leadok.leads.\
            get_most_recent_lead(domain=domain.name,
                                 exclude_bracks=True)['date']
        data['domains_list'].append(line)
    return data


@handle_exception({})
def get_giga_statistics(date_from, date_till):
    data = {}
    data['month'] = date_from.month
    data['year'] = date_from.year

    costs = leadok.costs.get_costs(date_from, date_till)

    daily_data = []
    for date in get_days_list(date_from, date_till):
        d = {}
        d['date'] = date
        NAME = 'Георгий Цеквава'
        datetime_span = arrow.get(date, 'Europe/Moscow').span('day')
        d['leads_dirty'] = leadok.leads.\
            count_leads(datetime_span=datetime_span,
                        source=NAME,
                        exclude_test=True)
        BRACK_STATUSES = [1, 2]
        d['bracks'] = leadok.leads.\
            count_leads(datetime_span=datetime_span,
                        source=NAME,
                        statuses=BRACK_STATUSES,
                        exclude_test=True)
        d['leads_clean'] = d['leads_dirty'] - d['bracks']
        d['cost'] = costs[date]['giga']
        try:
            d['lead_cost'] = d['cost'] / d['leads_clean']
        except (ZeroDivisionError, DivisionUndefined, InvalidOperation):
            d['lead_cost'] = decimal.Decimal('0.00')
        daily_data.append(d)

    names = ['leads_dirty', 'bracks', 'leads_clean', 'cost']

    for name in names:
        data['total_' + name] = sum(x[name] for x in daily_data)
        data['avg_' + name] = _average((x[name] for x in daily_data),
                                             ignore_zeros=False)
    data['lines'] = daily_data
    return data

