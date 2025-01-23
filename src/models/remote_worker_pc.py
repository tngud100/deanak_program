from sqlalchemy import Column, String, Integer
from database import Base

class RemoteWorkerPcs(Base):
    __tablename__ = 'workers'
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(String(45), nullable=False)
    pc_num = Column(Integer, nullable=False)

    def __repr__(self):
        return f"workers(worker_id={self.worker_id}, pc_num={self.pc_num})"