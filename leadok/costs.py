from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Date
from sqlalchemy.orm.exc import NoResultFound
from leadok.common import handle_exception, get_days_list
from leadok import app, db

logger = app.logger


class Cost(db.Model):
    __tablename__ = 'costs'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    amount = Column(Numeric)
    name = Column(String)

    def __init__(self, date, amount, name):
        self.date = date
        self.amount = amount
        self.name = name

    def __repr__(self):
        return 'Cost({}, {}, {})'.format(self.date, self.amount, self.name)


class CostName(db.Model):
    __tablename__ = 'cost_names'

    id = Column(Integer, primary_key=True)
    name = Column(String)


@handle_exception([])
def get_all_cost_names():
    return [x.name for x in CostName.query.order_by(CostName.name).all()]


def get_costs(date_from, date_till):
    zero = Decimal('0.00')
    zero_cost = dict((name, zero) for name in get_all_cost_names())
    # zero_cost = {name: zero for name in get_all_cost_names()}
    # Initialization with zeros:
    costs = OrderedDict()
    for day in get_days_list(date_from, date_till):
        costs[day] = deepcopy(zero_cost)
    fetched_costs = Cost.query.\
        filter(Cost.date >= date_from, Cost.date <= date_till).\
        order_by(Cost.date.desc()).all()
    for item in fetched_costs:
        costs[item.date][item.name] = item.amount
    return costs


def add_or_update_cost(date, amount, name):
    try:
        cost = Cost.query.filter(Cost.name == name, Cost.date == date).one()
    except NoResultFound:
        cost = Cost(date, amount, name)
        db.session.add(cost)
        db.session.commit()
        logger.info('Cost inserted into DB: {}'.format(cost))
    else:
        cost.amount = amount
        db.session.commit()
        logger.info('Cost updated in DB: {}'.format(cost))
