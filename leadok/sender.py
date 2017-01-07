import smtplib
from email.mime.text import MIMEText
import socket
import time

import arrow

from leadok.common import pretty_number, handle_exception
from leadok import app

logger = app.logger

SENDER_LOGIN = app.config['SENDER_LOGIN']
SENDER_PASSWORD = app.config['SENDER_PASSWORD']
SENDER_EMAIL = app.config['SENDER_EMAIL']
SENDER_TO = app.config['SENDER_TO']
SENDER_SMS_TO = app.config['SENDER_SMS_TO']


@handle_exception(False)
def send_mail(to, subject, message):
    host = 'smtp.yandex.ru'
    port = 465  # SMTP SSL
    login = SENDER_LOGIN
    password = SENDER_PASSWORD
    sender = SENDER_EMAIL
    timeout = 10  # sec
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(to)
    start = time.time()
    try:
        server = smtplib.SMTP_SSL(host, port, timeout=timeout)
        server.login(login, password)
        server.sendmail(sender, to, msg.as_string())
        dt = round(time.time() - start, 1)
        logger.info('Email {} to {} has been sent'.format(subject, to))
        return True
    except (smtplib.SMTPException, socket.timeout) as e:
        dt = round(time.time() - start, 1)
        logger.error('Email {} to {} has not been sent '
            '({} sec passed, timeout = {} sec) : '
            '{} : {}'.format(subject, to, dt, timeout, type(e), e))
        return False
    finally:
        try:
            server.quit()
        except Exception: pass


@handle_exception(False)
def send_mail_to_us(subject, message):
    return send_mail(SENDER_TO, subject, message)


@handle_exception(False)
def send_sms(message):
    logger.debug('Sending SMS ...')
    to = SENDER_SMS_TO
    if send_mail(to, subject=message, message=''):
        logger.info('SMS "{}" successfully sent'.format(message))
        return True
    else:
        logger.error('Sending SMS "{}" failed'.format(message))
        return False


@handle_exception(False)
def _send_lead_via_email(customer, lead):
    cur_time = arrow.get(lead['date']).to('Europe/Moscow').format('YYYY-MM-DD HH:mm')
    name     = lead['name']
    phone    = lead['phone']
    question = lead['question']
    message = (
        '{}\nИмя: {}\nТелефон {}\nВопрос: '
        '{}\n'.format(cur_time, name, pretty_number(phone),
                      question.replace('\n', ''))
    )
    if send_mail([customer.email], '[ leadok ] Новая заявка', message):
        logger.info('Lead successfully emailed to customer '
            '[{}]'.format(customer.uid))
        return True
    return False


@handle_exception()
def send_lead_to_customer_via_email(customer, lead):
    for n in range(5):
        if _send_lead_via_email(customer, lead):
            break
        time.sleep(1.25)
