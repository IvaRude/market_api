import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class History(Base):
    __tablename__ = 'history'

    history_id = Column(Integer, primary_key=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.item_id'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    total_price = Column(Integer, nullable=True)
    amount_of_offers = Column(Integer, nullable=True)
    price = Column(Integer, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String, nullable=False)


class Items(Base):
    __tablename__ = 'items'

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    parent_id = Column(UUID(as_uuid=True), ForeignKey('items.item_id'), nullable=True)
    name = Column(String, nullable=False, default='')
    type = Column(String, nullable=False)
    total_price = Column(Integer, nullable=True)
    amount_of_offers = Column(Integer, nullable=True)
    price = Column(Integer, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String, nullable=False)


metadata = Base.metadata
