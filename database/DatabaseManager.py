from sqlalchemy import create_engine, Column, Integer, String, Sequence, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .migrations.migration import Base, Posts, Sections

class DatabaseManager:
    def __init__(self, db_uri='sqlite:///:memory:'):
        self.engine = create_engine(db_uri, echo=True)
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)


    def create_thread(self, title, username, content, image_uuid, section_id):
        session = self.Session()
        thread = Posts(title=title, username=username, content=content, image_uuid=image_uuid, section_id=section_id)
        session.add(thread)
        session.commit()
        session.close()
        return thread.id

    def get_threads(self, section_id=None, page=0, size=50):
        if page < 0 or page >= self.get_thread_max_pages(section_id=section_id, size=size):
            raise ValueError(f"Page must be >= 0 and < {self.get_thread_max_pages(section_id=section_id, size=size)}")
        
        session = self.Session()
        query = session.query(Posts).filter(Posts.parent_id == None)  # Threads have no parent_id
        
        if section_id is not None:
            query = query.filter(Posts.section_id == section_id)
        
        query = query.order_by(Posts.date.asc())
        
        threads = query.offset(page * size).limit(size).all()
        session.close()
        return threads



    def get_thread_max_pages(self, section_id=None, size=50):
        session = self.Session()
        query = session.query(func.count(Posts.id))

        if section_id is not None:
            query = query.filter(Posts.section_id == section_id)

        total_threads = query.scalar()
        session.close()

        if total_threads is None:
            return -1
        
        return (total_threads + size - 1) // size

    
    
    def get_thread_by_id(self, thread_id):
        session = self.Session()
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        session.close()
        return thread
    
    def delete_thread_by_id(self, thread_id):
        session = self.Session()
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        if thread:
            session.delete(thread)
            session.commit()
        session.close()
        
    def update_thread_by_id(self, thread_id, title, username, content, image_path, section_id):
        session = self.Session()
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        thread.title = title
        thread.username = username
        thread.content = content
        thread.image_path = image_path
        thread.section_id = section_id
        session.commit()
        session.close()

    def get_comments_by_thread_id(self, thread_id):
        # TODO: implement paging here
        session = self.Session()
        comments = session.query(Posts).filter(Posts.parent_id == thread_id).all()
        session.close()
        return comments

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

    
    
    
    
