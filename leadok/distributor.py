from leadok.common import handle_exception
import leadok.leads
import leadok.customers
import leadok.logic
import leadok.sender
from leadok import app

logger = app.logger


@handle_exception(False)
def handle_incoming_lead(raw_lead, customer=None):
    lead = leadok.leads.prepare_incoming_lead(raw_lead)
    logger.info('Distributing new lead : {}'.format(lead))
    if customer is None:  # customer not specified -> needs to be chosen
        duplicates = leadok.leads.get_duplicates(lead, only_recent=True)
        customers = leadok.customers.get_customers()
        winner = leadok.logic.pick_winner(customers, lead, duplicates)
    else:
        logger.info('This lead must be sent to customer '
            '[{}]'.format(customer.uid))
        winner = customer
    leadok.leads.insert_new_lead(lead, winner)
    leadok.customers.increment_counter(winner.uid)
    if winner.email_needed:
        leadok.sender.send_lead_to_customer_via_email(winner, lead)
    return True

