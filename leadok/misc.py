import datetime
import decimal
from decimal import Decimal, ROUND_DOWN, ROUND_UP, InvalidOperation

import arrow

import leadok.settings
from leadok.settings import get_setting_value
import leadok.leads
import leadok.sender
import leadok.distributor
import leadok.direct
import leadok.costs
import leadok.customers
import leadok.domains
import leadok.payments
from leadok.common import pretty_number, handle_exception
from leadok import app

logger = app.logger

BRACK_ACCEPTED_STATUS = 2
BRACK_PENDING = 1


def notify_giga_about_brack_via_email(lead_id, notification):
    BRACK_ACCEPTED = 2
    BRACK_PENDING = 1
    GIGA_NAME = 'Георгий Цеквава'

    giga_timezone = 'Europe/Moscow'

    lead = leadok.leads.get_lead_by_id(lead_id)
    if (lead.status_text not in ['brack_accepted', 'brack_pending'] or
            lead.source != GIGA_NAME or
            lead.giga_brack_notification is not None):
        raise RuntimeError('giga should not be notified')

    giga_address = get_setting_value('giga_email')
    if giga_address is None:
        return

    timestamp = arrow.get(lead['date']).to(giga_timezone).format('DD.MM.YYYY HH:mm:ss')

    subject = 'БРАК'
    text = ('{}\n\nДата: {}\n\nИмя: {}\n\n'
            'Телефон: {}\n\nВопрос: {}\n\n'.format(notification,
                                                   timestamp,
                                                   lead['name'],
                                                   pretty_number(lead['phone']),
                                                   lead['question']))

    if not leadok.sender.send_mail(giga_address, subject, text):
        raise RuntimeError('error sending email')

    leadok.leads.upgrade_lead(lead_id, giga_brack_notification=notification)


def send_migration_from_elena_to_timur():
    key = 'auto_send_migration_leads_from_elena54_to_timur'
    if get_setting_value(key) != 'Yes':
        return
    leads = leadok.leads.get_leads(uid='elena54', status=1)
    words = ['миграци', 'гражданство', 'регистраци', 'международн']
    for lead in leads:
        comment = lead['commentbrack'].lower().strip()
        if not any(word in comment for word in words):
            continue
        logger.debug('Lead {} is a migration '
            'lead for elena54'.format(lead['id']))
        new_lead = lead.copy()
        timur = leadok.customers.get_customer('timur')
        leadok.distributor.handle_incoming_lead(new_lead, customer=timur)
        leadok.leads.accept_brack(lead['id'])
        logger.info('Lead was sent to timur and bracked for elena54')


@handle_exception()
def auto_brack_regions():
    if get_setting_value('auto_brack_regions') != 'Yes':
        return
    BRACK_PENDING = 1
    leads = leadok.leads.get_leads(domain='jurist-msk', status=BRACK_PENDING)
    words = [
        'регион', 'ростов-на-дону', 'петербург', 'ая область',
        'чуваш', 'курск', 'белгород'
    ]
    codes = '902 961 920 987 950 951 952 953 914'.split()
    # Chuvashiya
    additional = '971 972 973 974 975 976 977 978 979'.split()
    codes = codes + ['919' + item for item in additional]
    codes.append('960')
    for lead in leads:
        if 'zvonok' in lead['source']:
            continue
        commentbrack = lead['commentbrack']
        comment = commentbrack.lower().strip()
        phone = lead['phone']
        if not any(word in comment for word in words):
            continue
        if not any(phone[1:].startswith(num) for num in codes):
            continue
        leadok.leads.accept_brack(lead['id'])
        logger.info(
            'Lead {} auto bracked as region '
            '({}, "{}")'.format(lead['id'], phone, commentbrack)
        )


@handle_exception()
def auto_brack_already_consulted():
    if get_setting_value('auto_brack_already_consulted') != 'Yes':
        return
    leads = leadok.leads.get_leads(source='Георгий Цеквава',
                                   status=BRACK_PENDING)
    words = [
        'уже записан',
        'уже проконсультирован',
        'проконсультировали',
        'обращалась',
        'обращался',
        'записан',
    ]
    for lead in leads:
        if 'zvonok' in lead['source']:
            continue
        commentbrack = lead['commentbrack']
        comment = commentbrack.lower().strip()
        if not any(word in comment for word in words):
            continue
        leadok.leads.accept_brack(lead['id'])
        logger.info(
            'Lead {} auto bracked as already consulted '
            '("{}")'.format(lead['id'], commentbrack)
        )


@handle_exception()
def auto_brack_short_phone_numbers():
    if get_setting_value('auto_brack_short_numbers') != 'Yes':
        return
    BRACK_PENDING = 1
    leads = leadok.leads.get_leads(status=BRACK_PENDING)
    for lead in leads:
        if 'zvonok' in lead['source']:
            continue
        phone = lead['phone']
        lead_id = lead['id']
        if not len(phone) < 9:
            continue
        leadok.leads.accept_brack(lead_id)
        logger.info('Lead {} auto bracked because of '
                    'short phone number ({})'.format(lead_id, phone))


@handle_exception()
def auto_brack_duplicates():
    if get_setting_value('auto_brack_duplicates') != 'Yes':
        return
    words = ['повтор', 'дубль', 'клиент от', 'от']
    for lead in leadok.leads.get_leads_awaiting_brack():
        comment = lead.commentbrack.lower().strip()
        if not any(word in comment for word in words):
            continue
        for duplicate in leadok.leads.get_duplicates(lead):
            if duplicate.status == BRACK_ACCEPTED_STATUS:
                continue
            leadok.leads.accept_brack(lead.id)
            logger.info('Lead {} auto bracked as '
                        'duplicate'.format(lead.id))
            break


@handle_exception()
def update_direct_expenses_cache():
    app.logger.debug('Updating Yandex.Direct start...')
    expenses = leadok.direct.get_direct_expenses(days_back=7)
    for date in sorted(expenses):
        amount = decimal.Decimal('{0:.2f}'.format(expenses[date]))
        leadok.costs.add_or_update_cost(date, amount, 'Yandex.Direct')
    app.logger.debug('Updating Yandex.Direct costs '
                     'successfully finished')


@handle_exception()
def check_direct_balance():
    value = get_setting_value('direct_threshold_value') or '10000'
    try:
        THRESHOLD_VALUE = Decimal(value)  # RUB
    except InvalidOperation:
        # In case parsing failed
        THRESHOLD_VALUE = Decimal('10000')
    balance = leadok.direct.get_balance()
    if balance < THRESHOLD_VALUE:
        x = 10 * (balance / 10).quantize(Decimal('1.'),
                                         rounding=ROUND_DOWN)
        leadok.sender.send_sms('DIRECT BALANCE: {}'.format(x))


@handle_exception()
def turn_off_ads_if_necessary():
    s_1 = get_setting_value('auto_direct_turn_on_often') == 'Yes'
    s_2 = get_setting_value('auto_direct_turn_off_often') == 'Yes'
    for domain in leadok.domains.get_domains():
        on = domain.needs_ads_on()
        word = 'ON' if on else 'OFF'
        logger.debug('Ads for {} must be {}'.format(domain, word))
        if on and s_1:
            leadok.direct.turn_ads_on(domain)
        if not on and s_2:
            if leadok.direct.is_domain_off(domain):
                logger.debug('Ads for {} already OFF'.format(domain))
                continue
            leadok.direct.turn_ads_off(domain)
            leadok.sender.send_sms(
                'LEADOK отключил {}'.format(domain.name.upper())
            )


@handle_exception()
def turn_on_direct_ads_if_necessary():
    if get_setting_value('auto_direct_turn_on_mornings') != 'Yes':
        return
    logger.info('Early morning. Turning ON Yandex.Direct campaigns...')
    for domain in leadok.domains.get_domains():
        if domain.needs_ads_on():
            logger.info('Ads for {} must be ON'.format(domain))
            leadok.direct.turn_ads_on(domain)
        else:
            logger.info('Ads for {} must be OFF'.format(domain))


@handle_exception()
def remove_rejected_payments_if_necessary():
    if get_setting_value('auto_delete_rejected_payments') != 'Yes':
        return
    leadok.payments.delete_all_rejected_payments()
