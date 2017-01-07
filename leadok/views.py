from functools import wraps
import time
import traceback
import datetime
import decimal
import math

import arrow
from flask import (render_template, redirect, url_for,
                   request, g, abort, session, jsonify)
from flask_login import (login_user, logout_user,
                         current_user, login_required)

import leadok.direct
import leadok.payments
import leadok.customers
import leadok.reports
import leadok.leads
import leadok.distributor
import leadok.validators
import leadok.domains
import leadok.settings
from leadok.settings import Setting
import leadok.costs
import leadok.misc
from leadok.common import (handle_exception,
                           pretty_number,
                           MONTHS,
                           pretty_currency,
                           get_dates_range,
                           get_only_digits)
from leadok import app, login_manager, db


logger = app.logger


@app.errorhandler(Exception)
def handle_500(e=None):
    logger.error(
        '{}'.format(traceback.format_exc())
    )
    return (
        'Error 500. Flask error occured. '
        'Refer to log file for details.'
    )


@handle_exception({})
def request_to_dict_advanced(request):
    # request is a flask request object
    # it always contains args, form and json
    # but each of these three is either dict or None
    d = {}
    for container in [request.args, request.form, request.json]:
        try:
            for item in container:
                d[item] = container[item]
        except TypeError:  # in case container is not a dict but None
            pass
    return d


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user is None:
            return redirect(url_for('login'))
        try:
            if not current_user.is_admin():
                abort(403)
        except AttributeError:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user is None:
            return redirect(url_for('login'))
        try:
            if current_user.is_admin():
                abort(403)
        except AttributeError:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def run_before_each_request():
    g.user = current_user
    g.time_now = arrow.now('Europe/Moscow')
    g.TZ = 'Europe/Moscow'
    g.YEARS = list(range(2015, g.time_now.year + 1))
    g.MONTHS = MONTHS
    g.pretty_number = pretty_number
    g.pretty_currency = pretty_currency
    g.arrow = arrow
    g.Lead = leadok.leads.Lead
    try:
        if not current_user.is_authenticated():
            return
    except TypeError:
        if not current_user.is_authenticated:
            return
    g.CUSTOMERS = leadok.customers.get_customers().uids
    datetime_span = arrow.now('Europe/Moscow').span('day')
    role = None
    try:
        if current_user.is_admin():
            role = 'admin'
        else:
            role = 'user'
    except AttributeError as e:
        logger.error('in run_before_each_request : {}'.format(e))

    try:
        if role == 'admin':
            g.TOTAL_NOW = leadok.leads.count_leads(
                datetime_span=datetime_span,
                exclude_bracks=True,
                exclude_test=True
            )
        elif role == 'user':
            g.TOTAL_NOW = leadok.leads.count_leads(
                uid=current_user.uid,
                datetime_span=datetime_span,
                exclude_bracks=True
            )
        else:
            g.TOTAL_NOW = 0
    except Exception as e:
        logger.error('in run_before_each_request last line: {}'.format(e))
        g.TOTAL_NOW = 0


class Admin(dict):
    uid = 'admin'

    def get_id(self): return self.uid

    def is_active(self): return True

    def is_anonymous(self): return False

    def is_authenticated(self): return True

    def is_admin(self): return True

    def get_balance(self): return 0


def get_user(uid, password=None):
    if uid == 'admin':
        return Admin() if password in [None, '8zaVV9v7FYNa'] else None
    c = leadok.customers.get_customer(uid)
    if c is None:
        return None
    return c if password is None or c.is_password_valid(password) else None


@login_manager.user_loader
def load_user(uid):
    return get_user(uid)







# ============ LANDING BEGIN =========


@app.route('/jurist-lp', methods=['GET', 'POST'])
def show_landing_page_jurist():
    if request.method == 'POST':
        _name = request.form.get('question', '')
        _phone = request.form.get('phone', '')
        lead = {}
        lead['source'] = request.url
        lead['domain'] = 'leadgen-rus'
        lead['phone'] = _phone
        lead['name'] = 'test'
        lead['question'] = 'Заявка юриста по имени {}'.format(_name)
        leadok.distributor.handle_incoming_lead(lead)
        return redirect(url_for('show_landing_page_jurist_thanks'))
    return render_template('index-jurist.html')


@app.route('/jurist-thanks')
def show_landing_page_jurist_thanks():
    return render_template('thanks-jurist.html')


@app.route('/callcenter-operator-lp', methods=['GET', 'POST'])
def show_landing_page_callcenter_operator():
    if request.method == 'POST':
        _name = request.form.get('question', '')
        _phone = request.form.get('phone', '')
        lead = {}
        lead['source'] = request.url
        lead['domain'] = 'leadgen-rus'
        lead['phone'] = _phone
        lead['name'] = 'test'
        lead['question'] = 'Заявка оператора колл-центра по имени {}'.format(_name)
        leadok.distributor.handle_incoming_lead(lead)
        return redirect(url_for('show_landing_page_jurist_thanks'))
    return render_template('index-callcenter-operator.html')


@app.route('/send-message.php', methods=['POST'])
def send_lead_from_landing():
    _name = request.form.get('name', '')
    _phone = request.form.get('phone', '')
    _email = request.form.get('mail', '')
    lead = {}
    lead['source'] = request.url
    lead['domain'] = 'leadgen-rus'
    lead['phone'] = _phone
    lead['name'] = 'test'
    lead['question'] = 'Заявка по лидогенерации. Имя: {}, Email: {}'.format(_name, _email)
    leadok.distributor.handle_incoming_lead(lead)
    return redirect(url_for('show_landing_page_thanks'))


@app.route('/')
def show_landing_page():
    return render_template('landing_index.html')



# ============ LANDING END =========








# ============ ADMIN VIEWS =========

@app.route('/crm/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def show_admin_settings():
    if request.method == 'POST':
        data = leadok.validators.get_settings(request.form)
        leadok.settings.update_settings(data)
    settings = leadok.settings.get_all_settings()
    return render_template('admin_settings.html', settings=settings)


@app.route('/crm/admin/leads')
@login_required
@admin_required
def show_admin_leads():
    try:
        data = leadok.validators.get_admin_leads_data(
            request.args, timezone='Europe/Moscow')
        logger.debug('/crm/admin/leads GET args : {}'.format(request.args))
        data['leads'] = leadok.leads.get_leads(uid=data['uid'],
                                               datetime_span=data['datetime_span'],
                                               statuses=data['statuses'])
        return render_template('admin_leads.html', data=data,
                               timezone='Europe/Moscow')
    except Exception:
        return '{}'.format(traceback.format_exc())


@app.route('/crm/admin/bracks')
@login_required
@admin_required
def show_leads_brack():
    data = {}
    LS = leadok.leads.LeadStatus
    s = db.session.query(LS).filter_by(name='brack_pending').one()
    data['leads'] = leadok.leads.get_leads(statuses=[s.id])
    return render_template('admin_bracks.html', data=data)


@app.route('/crm/admin/bracks_giga')
@login_required
@admin_required
def show_leads_brack_giga():
    data = {}
    LS = leadok.leads.LeadStatus
    ss = db.session.query(LS).filter(LS.name.in_(['brack_pending', 'brack_accepted'])).all()
    leads = leadok.leads.get_leads(statuses=[s.id for s in ss],
                                   source='Георгий Цеквава',
                                   exclude_test=True)
    data['leads'] = [x for x in leads if x['giga_brack_notification'] is None]
    return render_template('admin_bracks.html', data=data)


@app.route('/crm/admin/leads/<int:n>', methods=['GET', 'POST'])
@login_required
@admin_required
def show_admin_lead(n):
    lead_id = n
    lead = leadok.leads.get_lead_by_id(lead_id)
    if lead is None:
        abort(404)
    if request.method == 'POST':
        f = request.form
        status = int(f['status'])
        answer = str(f.get('moderator_answer', ''))

        if status == 2:
            leadok.leads.accept_brack(lead_id, '')
        elif status == 3:
            leadok.leads.reject_brack(lead_id, answer)
        else:
            leadok.leads.set_status(lead_id, status)
        quality_name = f.get('quality_name')
        try:
            if quality_name is not None:
                lead.quality_name = quality_name
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return redirect(url_for('index'))
    lead_history = leadok.leads.get_lead_history(lead_id)
    duplicates = leadok.leads.get_duplicates(lead)
    data=dict(lead=lead,
              lead_history=lead_history,
              duplicates=duplicates)
    return render_template('admin_lead.html', data=data)


@app.route('/crm/admin/direct', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_direct():
    if request.method == 'POST':
        data = request_to_dict_advanced(request)
        logger.debug('Button clicked: {}'.format(data))
        on = True if 'turnon' in data else False
        for domain in leadok.domains.get_domains():
            if on:
                leadok.direct.turn_ads_on(domain)
            else:
                leadok.direct.turn_ads_off(domain)
    info = {}
    info['campaigns'] = leadok.direct.get_campaigns()
    balance = leadok.direct.get_balance()
    try:
        info['balance'] = math.floor(balance / 100) * 100
    except Exception:
        info['balance'] = None
    return render_template('admin_direct_list.html', info=info)


@app.route('/crm/admin/direct/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_direct_campaign(campaign_id):
    if request.method == 'POST':
        logger.info('admin_direct_campaign FORM: {}'.format(request.form))
        chosen = 'chosen' in request.form
        domain = request.form['domain'].strip()
        if not domain:
            domain = None
        leadok.direct.update_campaign(campaign_id,
                                      chosen=chosen,
                                      domain=domain)
        return redirect(url_for('admin_direct'))
    campaign = leadok.direct.get_campaign_by_id(campaign_id)
    if campaign is None:
        abort(404)
    return render_template('admin_direct_campaign.html', campaign=campaign)


@app.route('/crm/admin/direct/<int:campaign_id>/phrases')
@login_required
@admin_required
def admin_direct_campaign_phrases(campaign_id):
    campaigns = leadok.direct.get_campaigns()
    name = None
    for c in campaigns:
        if c.id == campaign_id:
            name = c.name
            break
    info = {'data': []}
    info['Name'] = name
    return render_template('admin_direct.html', info=info)


@app.route('/crm/admin/reports/phrases-statistics')
@login_required
@admin_required
def admin_show_phrases_statistics():
    options = leadok.validators.get_phrases_stats_options(request.args)
    data = leadok.reports.get_phrases_statistics(
        sort_by_brack_percent=options['sort_by_brack_percent']
    )
    try:
        return render_template('admin_report_phrases_stats.html', data=data)
    except Exception as e:
        logger.error(e)
        return 'SHIT HAPPENED'


@app.route('/crm/admin/reports/giga-statistics')
@login_required
@admin_required
def admin_show_giga_statistics():
    year, month = leadok.validators.form_get_year_and_month(request.args)
    dates_range = get_dates_range(year, month, until_today=True)
    date_from = dates_range[0]
    date_till = dates_range[-1]
    data = leadok.reports.get_giga_statistics(date_from, date_till)
    try:
        return render_template('admin_report_giga_stats.html', data=data)
    except Exception as e:
        return '{}'.format(traceback.format_exc())


@app.route('/crm/admin/send_lead', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_send_lead():
    try:
        if request.method == 'POST':
            lead = {}
            for item in ['name', 'phone', 'question']:
                lead[item] = request.form[item]
            uid = request.form['uid']
            customer = leadok.customers.get_customer(uid)
            lead['source'] = request.url
            lead['domain'] = customer.get_domain().name
            leadok.distributor.handle_incoming_lead(lead, customer)
            return redirect(url_for('show_admin_leads'))
    except Exception as e:
        app.logger.exception('Cannot send lead.')
        return str(e)
    return render_template('admin_send_lead.html')


@app.route('/crm/admin/reports/income')
@login_required
@admin_required
def admin_income():
    date_from, date_till = leadok.validators.\
                           get_dates_span(request.args)
    data = leadok.reports.get_costs(date_from, date_till)
    return render_template('admin_report_costs.html', data=data)


@app.route('/crm/admin/add_cost', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_cost():
    if request.method == 'POST':
        cost = leadok.validators.get_new_cost(request.form)
        leadok.costs.add_or_update_cost(cost['date'],
                                        cost['amount'],
                                        cost['name'])
        return redirect(url_for('admin_income'))
    return render_template('admin_add_cost.html')



@app.route('/crm/admin/reports')
@login_required
@admin_required
def admin_show_reports():
    return render_template('admin_reports_list.html')


@app.route('/crm/admin/reports/calls_stats')
@login_required
@admin_required
def admin_show_lead_stats():
    year, month = leadok.validators.form_get_year_and_month(request.args)
    data = leadok.reports.get_lead_stats(year, month)
    return render_template('admin_report_calls_stats.html', data=data)


@app.route('/crm/admin/log')
@login_required
@admin_required
def show_log():
    try:
        date = arrow.now('Europe/Moscow').format('YYYY-MM-DD')
        log_file = '{}{}.log'.format(
            app.config['LOGS_BASE_FILENAME'], date
        )
        with open(log_file, 'rt', encoding='utf-8') as f:
            lines = f.readlines()
    except (KeyError, OSError) as e:
        lines = ['Error loading log: {}'.format(e)]
    return render_template('admin_log.html', lines=lines)


@app.route('/crm/admin/reports/domains_summary')
@login_required
@admin_required
def show_domains_summary():
    data = leadok.reports.get_domains_summary()
    return render_template('admin_report_domains.html', data=data)


@app.route('/crm/admin/customers')
@login_required
@admin_required
def admin_customers_info():
    cs = leadok.customers.get_customers()
    return render_template('admin_customers.html', customers=cs)


@app.route('/crm/admin/customers/<uid>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_show_customer(uid):
    if request.method == 'POST':
        settings = leadok.validators.form_get_customer_settings(request.form)
        c = leadok.customers.get_customer(uid)
        if c is not None:
            c.set_settings(settings)
        return redirect(url_for('admin_customers_info'))
    customer = leadok.customers.get_customer(uid) or {}
    return render_template('admin_customer.html', m=5, customer=customer)


@app.route('/crm/admin/reports/bracks_stats')
@login_required
@admin_required
def show_admin_stats():
    info = leadok.validators.form_to_dict(request.args, current_user)
    data = leadok.reports.get_stats_admin(info['uid'],
                                          info['year'],
                                          info['month'])
    return render_template('admin_report_bracks_stats.html', info=data)


@app.route('/crm/admin/payments')
@login_required
@admin_required
def show_admin_payments():
    data = leadok.validators.form_to_dict(request.args,
                                   current_user,
                                   default_all=True)
    info = {}
    datetime_span = arrow.get(
        datetime.date(data['year'], data['month'], 1),
        'Europe/Moscow').span('month')
    info['payments'] = leadok.payments.\
        get_payments(data['uid'], datetime_span)
    info['month'] = data['month']
    info['year'] = data['year']
    info['uid'] = data['uid']
    info['sum_sberbank'] = sum(x.amount for x in info['payments']
                               if x.method == 'Сбербанк')
    info['sum_yandex'] = sum(x.amount for x in info['payments']
                             if x.method == 'Яндекс.Деньги')
    return render_template('admin_payments.html', info=info)


@app.route('/crm/admin/payments/<int:payment_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def show_payment(payment_id):
    if request.method == 'POST':
        f = request.form
        leadok.payments.update_payment(payment_id,
                                       f['method'],
                                       f['comment'],
                                       f['status'])
        return redirect(url_for('show_admin_payments'))
    payment = leadok.payments.get_payment_by_id(payment_id)
    return render_template('admin_edit_payment.html', payment=payment)


@app.route('/crm/admin/pay', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_pay():
    if request.method == 'POST':
        payment = leadok.validators.form_get_payment_admin(request.form)
        leadok.payments.add_payment(payment)
        return redirect(url_for('show_admin_payments'))
    return render_template('admin_add_payment.html')









# USER VIEWS





@app.route('/crm/leads')
@login_required
@user_required
def show_leads():
    try:
        leadok.customers.reset_counter(current_user.uid)
        data = leadok.validators.\
            get_admin_leads_data(request.args, timezone='Europe/Moscow')
        data['leads'] = leadok.leads.\
            get_leads(uid=current_user.uid,
                      datetime_span=data['datetime_span'],
                      statuses=data['statuses'])
        return render_template('user_leads.html', data=data,
                               timezone='Europe/Moscow')
    except Exception:
        m = '/crm/leads: {}'.format(traceback.format_exc())
        logger.error(m)
        raise


@app.route('/crm/leads/<int:n>', methods=['GET', 'POST'])
@login_required
@user_required
def show_lead(n):
    try:
        lead = leadok.leads.get_lead_by_id2(current_user.uid, n)
        if request.method == 'POST':
            f = request.form
            if 'comment' in f:
                leadok.leads.upgrade_lead(
                    lead.id, comment=f['comment'].strip())
                prev_status = lead.status_object
                if not prev_status.is_brack_related():
                    status = int(f['status'])
                    leadok.leads.set_status(lead.id, status)
            elif 'brack_reason' in f:
                leadok.leads.report_brack(lead.id, f['brack_reason'].strip())
            quality_name = f.get('quality_name')
            if quality_name is not None:
                try:
                    lead.quality_name = quality_name
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    raise
            return redirect(url_for('index'))
        leadok.leads.record_that_lead_was_seen_by_user(
            lead.id, str(request.remote_addr))
        return render_template('user_lead.html', lead=lead)
    except Exception:
        m = '/crm/leads/lead_id: {}'.format(traceback.format_exc())
        logger.error(m)
        raise


@app.route('/crm/payments', methods=['GET', 'POST'])
@login_required
@user_required
def show_payments():
    try:
        if request.method == 'POST':
            payment = leadok.validators.form_get_payment(request.form,
                                                         current_user.uid)
            leadok.payments.add_payment(payment)
        _t = leadok.validators.form_get_year_and_month(request.args)
        year, month = _t
        info = {}
        info['month'] = month
        info['year'] = year
        datetime_span = arrow.get(datetime.date(year, month, 1),
                                  'Europe/Moscow').span('month')
        info['payments'] = leadok.payments.\
            get_payments(current_user.uid, datetime_span)
        return render_template('user_payments.html', info=info)
    except Exception:
        m = '/crm/payments: {}'.format(traceback.format_exc())
        logger.error(m)
        raise


@app.route('/crm/stats')
@login_required
@user_required
def show_stats():
    year, month = leadok.validators.form_get_year_and_month(request.args)
    data = leadok.reports.get_stats(current_user.uid, year, month)
    return render_template('user_stats.html', data=data)


@app.route('/crm/settings', methods=['GET', 'POST'])
@login_required
@user_required
def show_settings():
    day_of_week = arrow.now('Europe/Moscow').format('dddd').lower()
    if request.method == 'POST':
        num_req = int(request.form['num_leads_required_today'])
        customer = leadok.customers.get_customer(current_user.uid)
        if customer.is_setting_req_allowed() and num_req >= 0:
            customer.set_req(num_req)
    customer = leadok.customers.get_customer(current_user.uid)
    data = {'customer': customer, 'day_of_week': day_of_week}
    return render_template('user_settings.html', data=data)


# OTHER VIEWS

@app.route('/crm/login', methods=['GET', 'POST'])
def login():
    try:
        session.permanent = True
        if request.method == 'POST':
            uid = request.form['name']
            password = request.form['password']
            user = get_user(uid, password)
            if user is not None:
                login_user(user, remember=False)
            else:
                # What is happening here is just brilliant
                # No, it's actually pure bullshit...
                BRUTE_FORCE_PROTECTION_DELAY = 5  # sec
                time.sleep(BRUTE_FORCE_PROTECTION_DELAY)
    except Exception:
        pass
    try:
        if current_user.is_authenticated():
            return redirect(url_for('index'))
    except TypeError:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route("/crm/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/crm')
@login_required
def index():
    try:
        if current_user.is_admin():
            return redirect(url_for('show_leads_brack'))
        return redirect(url_for('show_leads'))
    except Exception:
        m = '/crm: {}'.format(traceback.format_exc())
        logger.error(m)
        raise


@app.route('/sender', methods=['POST'])
def sender():
    try:
        lead = request_to_dict_advanced(request)
        phone = get_only_digits(lead.get('phone', ''))
        if len(phone) >= 10:
            logger.info('Incoming lead phone: "{}"'.format(phone))
            leadok.distributor.handle_incoming_lead(lead)
        else:
            logger.info(
                'Incoming lead has very short number: '
                '{}'.format(phone)
            )
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error('New lead not processed')
        return jsonify({'success': False})
    return jsonify({'success': True})


@app.route('/ajax/newleadscount', methods=['GET', 'POST'])
@login_required
def new_leads_count():
    n = int(leadok.customers.get_counter(current_user.uid))
    return jsonify(result=n)



@app.route('/send_lead', methods=['GET', 'POST'])
def external_send_lead():
    if request.method == 'POST':
        try:
            f = request.form
            lead = {}
            lead['name'] = f['name']
            lead['phone'] = f['phone']
            lead['question'] = f['question']
            lead['domain'] = 'jurist-msk'
            lead['source'] = 'Георгий Цеквава'
            leadok.distributor.handle_incoming_lead(lead)
            return render_template('message_success.html')
        except Exception:
            return render_template('message_fail.html')
    return render_template('external_send_lead.html')




@app.route('/ajax/notify_giga_about_brack_via_email', methods=['GET', 'POST'])
@login_required
@admin_required
def notify_giga_about_brack_via_email():
    try:
        lead_id = int(request.json['lead_id'])
        notification = str(request.json['notification'])
        leadok.misc.notify_giga_about_brack_via_email(lead_id, notification)
        result = True
    except Exception:
        result = False
    return jsonify(result=result)


@app.route('/ajax/delete_all_rejected_payments', methods=['POST'])
@login_required
@admin_required
def remove_rejected_payments():
    result = True
    try:
        leadok.payments.delete_all_rejected_payments()
    except Exception as e:
        logger.error('{}'.format(traceback.format_exc()))
        result = False
    return jsonify(result=result)


@app.route('/direct_api_get_token')
def get_direct_api_token():
    return ''
