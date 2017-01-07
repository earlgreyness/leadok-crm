from sqlalchemy import select, Column, Integer, String
import leadok.customers
from leadok import app, db

logger = app.logger


class Domain(db.Model):
    __tablename__ = 'lead_domains'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    region_description = Column(String)
    scope_description = Column(String)
    short_description = Column(String)
    region_short_description = Column(String)
    scope_short_description = Column(String)

    def is_lead_relevant(self, lead):
        try:
            return lead.domain == self.name
        except AttributeError:
            return lead['domain'] == self.name

    def needs_ads_on(self):
        """
        Returns either True or False
        """
        # Get all customers with the same domain as self
        customers = leadok.customers.get_customers(domain=self)
        N_LEADS_LEFT_CRITICAL = 3
        SECONDS_ALARM = 7 * 60
        total_remaining = 0
        for customer in customers:
            if customer.is_off():
                logger.debug('{} is off'.format(customer))
                continue
            if customer.is_test():
                logger.debug('{} is test'.format(customer))
                continue
            if customer.already_finished():
                logger.debug('{} already finished'.format(customer))
                continue
            if customer.seconds_till_finish < SECONDS_ALARM:
                logger.debug('{} almost done'.format(customer))
                continue
            total_remaining += customer.leads_remaining_today()
            logger.debug('Total left : {}'.format(total_remaining))
        return total_remaining > N_LEADS_LEFT_CRITICAL

    def __repr__(self):
        return "Domain('{}')".format(self.name)


def get_domains():
    return Domain.query.order_by(Domain.name).all()


def get_domain_by_name(name):
    return Domain.query.filter_by(name=name).one()
