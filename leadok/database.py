import datetime

from sqlalchemy import (
    Table, Column, String, Integer, Boolean, MetaData,
    ForeignKey, DateTime, Float, Time,
    Date, UniqueConstraint, Numeric,
)

from leadok import db


engine = db.engine

# metadata is deliberatly not bound to engine
metadata = MetaData()


class Customer(db.Model):
    __tablename__ = 'customers'

    uid                = Column(String, primary_key=True)
    password           = Column(String)
    email              = Column(String, default='')
    archived           = Column(Boolean, default=False)
    date_registered    = Column(DateTime, default=datetime.datetime.now)
    phone              = Column(String, default='')
    notes              = Column(String, default='')
    on                 = Column(Boolean, default=False)
    buffer             = Column(Boolean, default=False)
    balance_limit      = Column(Float, default=0.0)
    price              = Column(Float, default=450.0)
    email_needed       = Column(Boolean, default=False)
    balance_shift      = Column(Float, default=0.0)
    domain             = Column(String, nullable=False)
    new                = Column(Integer, default=0)
    beg_mon            = Column(Time, default=datetime.time(9))
    beg_tue            = Column(Time, default=datetime.time(9))
    beg_wed            = Column(Time, default=datetime.time(9))
    beg_thu            = Column(Time, default=datetime.time(9))
    beg_fri            = Column(Time, default=datetime.time(9))
    beg_sat            = Column(Time, default=datetime.time(9))
    beg_sun            = Column(Time, default=datetime.time(9))
    end_mon            = Column(Time, default=datetime.time(18))
    end_tue            = Column(Time, default=datetime.time(18))
    end_wed            = Column(Time, default=datetime.time(18))
    end_thu            = Column(Time, default=datetime.time(18))
    end_fri            = Column(Time, default=datetime.time(18))
    end_sat            = Column(Time, default=datetime.time(18))
    end_sun            = Column(Time, default=datetime.time(18))
    req_mon            = Column(Integer, default=0)
    req_tue            = Column(Integer, default=0)
    req_wed            = Column(Integer, default=0)
    req_thu            = Column(Integer, default=0)
    req_fri            = Column(Integer, default=0)
    req_sat            = Column(Integer, default=0)
    req_sun            = Column(Integer, default=0)
    allow_to_set_req   = Column(Boolean, default=False)



customers = Customer.__table__


leads_history = Table('leads_history', metadata,
    Column('id', Integer, primary_key=True),
    Column('lead_id', Integer),
    Column('action', String),
    Column('date', DateTime),
    Column('comment', String),
)

customers_payment_data_table = Table(
    'customers_payment_data',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('uid', String),
    Column('payment_method', String),
    Column('payment_info', String),
)
