from sqlalchemy import Column, String, Integer, DateTime
from database import Base

class Deanak(Base):
    __tablename__ = 'daenak'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String(45), nullable=True)
    worker_id = Column(String(255), nullable=True)
    pw2 = Column(String(45), nullable=True)
    otp = Column(Integer, nullable=True)
    coupon_count = Column(Integer, nullable=False, default=0)
    state = Column(Integer, nullable=True)
    otp_pass = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Deanak(deanak_id={self.id})"
