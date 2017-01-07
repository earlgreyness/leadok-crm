import random
import arrow
from leadok.common import handle_exception
from leadok import app

logger = app.logger


@handle_exception(False)
def is_lead_test(lead):
    return lead['name'].lower().strip() == 'test'


@handle_exception(None)
def print_detailed_info(customers, factors={}, winner=None):
    msg = 'Customers summary: \n\n'
    factor_total = sum(factors.values())
    for customer in customers:
        factor = factors.get(customer.uid, 0)
        start, finish = customer.get_working_hours()
        s_start = start.format('HH:mm')
        s_finish = finish.format('HH:mm')
        msg += '    {:<10}:  '.format(customer.uid)
        msg += '{:<3} ({:<3})  '.format(customer.get_now(),
                                        customer.get_req())
        msg += '[{} - {}]  '.format(s_start, s_finish)
        if customer.is_off():
            msg += '(OFF)  '
        else:
            msg += ' '*7
        msg += 'Factor = {:<4}  '.format(factor)
        if winner is not None:
            if customer.uid == winner.uid:
                msg += '  (WINNER)'
        msg += '\n'
    logger.info(msg)


@handle_exception(None)
def winner_because_duplicate(customers, lead, duplicates):
    for _lead in duplicates:
        if _lead['domain'] != lead['domain']:
            continue
        prev_winner = customers.get(_lead['winner'])
        if not prev_winner.is_test():
            return prev_winner
    return None



@handle_exception({})
def get_factors(customers, lead, duplicates):
    if is_lead_test(lead):
        return {'test': 1}
    dupl_winner = winner_because_duplicate(customers, lead, duplicates)
    if dupl_winner:
        logger.info('Lead is duplicate '
            'for customer [{}]'.format(dupl_winner.uid))
        return {dupl_winner.uid: 1}

    factors = {}
    for c in customers:
        conditions = [
            c.is_test(),
            c.is_off(),
            c.get_balance(modified=True) < c.get_price(),
            not c.get_domain().is_lead_relevant(lead),
            not c.is_lead_needed(lead),
        ]
        if any(conditions):
            continue
        now = c.get_now()
        left = c.left
        if left <= 0 or not c.inside_working_hours():
            continue
        try:
            factors[c.uid] = int(100 * (left / now))
        except ZeroDivisionError:
            factors[c.uid] = int(100 * left)
    if factors:
        return factors

    # We get here if none of the customers has suitable working hours
    # or has number of leads received more than required.
    # In this case, if customer does not have "strict" property,
    # he can still receive the lead, regardless of the working_hours
    # and received leads number. It pertains only to not-strict customers.
    logger.info('Choosing between non-strict customers ...')
    factors = {}
    for c in customers:
        if c.is_test() or c.is_strict():
            continue
        if c.get_domain().is_lead_relevant(lead) and c.is_lead_needed(lead):
            _req = c.get_req()
            factors[c.uid] = 1 if _req <= 0 else _req
    return factors


@handle_exception(None)
def pick_winner(customers, lead, duplicates):
    # logger.debug('Getting factors ...')
    factors = get_factors(customers, lead, duplicates)
    # logger.debug('Calculating chances_list ...')
    chances_list = []
    for uid, factor in factors.items():
        chances_list.extend(uid for x in range(factor))
    if not chances_list:
        winner = None
    else:
        winner_uid = random.choice(chances_list)
        winner = customers.get(winner_uid)
    print_detailed_info(customers, factors, winner)
    if winner is None:
        logger.warning('All factors are zero. Picking fallback customer...')
        return customers.get('test')
    logger.info('Lead won by customer [{}]'.format(winner.uid))
    return winner
