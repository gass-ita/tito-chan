from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Threads(Base):
    __tablename__ = 'threads'
    id = Column(Integer, Sequence('thread_id_seq'), primary_key=True)
    title = Column(String(50))
    username = Column(String(50))
    content = Column(String(500))
    image_path = Column(String(100))
    parent_id = Column(Integer)
    section_id = Column(Integer)

class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, Sequence('section_id_seq'), primary_key=True)
    section_name = Column(String(50))
