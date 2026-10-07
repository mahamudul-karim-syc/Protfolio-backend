from database import Base
from sqlalchemy import Column, Integer, String


class Message_Table(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    Name = Column(String, nullable=False)
    Email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    Phone = Column(String, nullable=False)
    message = Column(String, nullable=False)