import imaplib

from bs4 import BeautifulSoup  # html parser

from leadok.common import log, handle_exception
import leadok.customers
import leadok.distributor


@handle_exception(False)
def fetch_leads_from_mailbox():
    log('Fetching Leadia leads from dedicated mailbox ...')

    server = imaplib.IMAP4_SSL('imap.yandex.ru')
    server.login('login', 'password')
    server.select('INBOX')

    # ids contains ids of all unseen emails in INBOX folder:
    typ, ids = server.search(None, 'UNSEEN')

    if not ids[0].split():
        log('No new Leadia leads to fetch')

    try:
        for id in ids[0].split():
            _code, data = server.fetch(id, '(BODY.PEEK[TEXT])')
            html_email_body = data[0][1].decode('utf-8')
            soup = BeautifulSoup(html_email_body, 'html.parser')
            fields = [str(item.string).strip() for item in soup.find_all('td')]
            if len(fields) != 6:
                raise TypeError('The email is not a Leadia lead')

            lead = {}
            lead['name'] = fields[2]
            lead['phone'] = fields[3]
            lead['question'] = fields[5]
            lead['domain'] = 'jurist-msk'
            lead['source'] = 'leadia.ru'

            log('Leadia lead {} fetched '
                'from dedicated mailbox'.format(fields[0]))

            elena = leadok.customers.get_customer('elena54')
            # leadok.distributor.handle_incoming_lead(lead, customer=elena)

            server.store(id, '+FLAGS', '\SEEN')
    finally:
        server.close()
        server.logout()


if __name__ == '__main__':
    fetch_leads_from_mailbox()
