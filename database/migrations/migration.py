from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Sequence,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Posts(Base):
    __tablename__ = "posts"
    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, default=None)
    content = Column(Text, nullable=True)
    image_uuid = Column(String(255), nullable=True)
    parent_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    section_id = Column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(DateTime, nullable=False, default=func.current_timestamp())


class Sections(Base):
    __tablename__ = "sections"
    id = Column(Integer, autoincrement=True, primary_key=True)
    section_name = Column(String(255))
    image_uuid = Column(String(255), nullable=True)


class Motds(Base):
    __tablename__ = "motds"
    id = Column(Integer, autoincrement=True, primary_key=True)
    motd = Column(Text, unique=True)
    
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, autoincrement=True, primary_key=True)
    username = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    
