from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .migrations.migration import Base, Threads

class DatabaseManager:
    def __init__(self, db_uri='sqlite:///:memory:'):
        self.engine = create_engine(db_uri, echo=True)
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)


    def create_thread(self, title, username, content, image_path, section_id):
        session = self.Session()
        thread = Threads(title=title, username=username, content=content, image_path=image_path, section_id=section_id)
        session.add(thread)
        session.commit()
        session.close()

    def get_all_threads(self):
        session = self.Session()
        threads = session.query(Threads).all()
        session.close()
        return threads
    
    def get_thread_with_limit(self, limit):
        session = self.Session()
        threads = session.query(Threads).limit(limit).all()
        session.close()
        return threads
    
    def get_thread_by_section(self, section_id):
        session = self.Session()
        threads = session.query(Threads).filter(Threads.section_id == section_id).all()
        session.close()
        return threads
    
    def get_thread_by_id(self, thread_id):
        session = self.Session()
        thread = session.query(Threads).filter(Threads.id == thread_id).first()
        session.close()
        return thread
    
    def delete_thread_by_id(self, thread_id):
        session = self.Session()
        thread = session.query(Threads).filter(Threads.id == thread_id).first()
        session.delete(thread)
        session.commit()
        session.close()

    def update_thread_by_id(self, thread_id, title, username, content, image_path, section_id):
        session = self.Session()
        thread = session.query(Threads).filter(Threads.id == thread_id).first()
        thread.title = title
        thread.username = username
        thread.content = content
        thread.image_path = image_path
        thread.section_id = section_id
        session.commit()
        session.close()

    def create_section(self, section_name):
        session = self.Session()
        section = Sections(section_name=section_name)
        session.add(section)
        session.commit()
        session.close()

    def get_all_sections(self):
        session = self.Session()
        sections = session.query(Sections).all()
        session.close()
        return sections
    
    

    def close(self):
        self.engine.dispose()
        self.Session.close_all()

    
    
    
    
