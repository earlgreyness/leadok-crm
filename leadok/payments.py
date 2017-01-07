from decimal import Decimal
from sqlalchemy import func, select, Integer, String, Numeric, Column
from sqlalchemy_utils import ArrowType
from leadok.database import engine
from leadok.database import customers_payment_data_table
from leadok import app, db


logger = app.logger


class Payment(db.Model):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    uid = Column(String)
    amount = Column(Numeric)
    date = Column(ArrowType(timezone=True))
    method = Column(String)
    status = Column(String)
    comment = Column(String)

    def __init__(self, uid, amount, date,
                 method, status, comment=''):
        self.uid = uid
        self.amount = amount
        self.date = date
        self.method = method
        self.status = status
        self.comment = comment
        if not self.comment:
            t = customers_payment_data_table
            q = select([t]).where(t.c.uid == self.uid).\
                where(t.c.payment_method == self.method)
            r = engine.execute(q).first()
            if r is not None:
                self.comment = r['payment_info']

    def __repr__(self):
        return '<Payment {}>'.format(self.id)


def get_payments(uid, datetime_span):
    query = Payment.query.filter(Payment.uid != 'test',
                                 Payment.date.between(*datetime_span))
    if uid is not None:
        query = query.filter(Payment.uid == uid)
    return query.order_by(Payment.date.desc()).all()


def get_payment_by_id(payment_id):
    return Payment.query.get(payment_id)


def get_total_for(uid):
    result = db.session.query(func.sum(Payment.amount)).\
                filter(Payment.uid == uid,
                       Payment.status != 'rejected').scalar()
    return Decimal('0.00') if result is None else result


def add_payment(payment):
    db.session.add(payment)
    db.session.commit()


def update_payment(payment_id, method, comment, status):
    payment = Payment.query.get(payment_id)
    payment.method = method
    payment.comment = comment
    payment.status = status
    db.session.commit()


def delete_all_rejected_payments():
    items_deleted = Payment.query.filter_by(status='rejected').delete()
    db.session.commit()
    logger.info('Rejected payments deleted ({} items)'.format(items_deleted))
