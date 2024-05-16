from sqlalchemy import create_engine, func, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .migrations.migration import Base, Posts, Sections, Motds, Users
from typing import Union
from sqlalchemy.engine.url import URL
from functools import wraps
from sessionmanager.SessionManager import SessionManager
from sqlalchemy.orm.session import Session

class DatabaseManager:
    def __init__(self, db_uri: Union[str, URL] = "sqlite:///:memory:"):
        self.engine = create_engine(db_uri)
        self.Base = declarative_base()
        self.session_maker = sessionmaker(bind=self.engine)
        self.create_tables()
        
        self.SM = SessionManager()
        self.SM.set_session_maker(self.session_maker)


    def create_tables(self):
        Base.metadata.create_all(self.engine)


    @property
    def create_thread(self):
        @self.SM.session_management(auto_commit=True)
        def _create_thread(
            user_id: int,
            section_id: int,
            title: str,
            content: str = None,
            image_uuid: str = None,
            parent_id: int = None,
            session=None,
        ) -> int:
            
            
            # TODO: check for image_uuid existence, section and parent

            post = Posts(
                title=title,
                user_id=user_id,
                content=content,
                image_uuid=image_uuid,
                section_id=section_id,
                parent_id=parent_id,
            )
            session.add(post)
            session.commit()

            return post.id
        
        return _create_thread

    @property
    def get_threads(self):
        @self.SM.session_management(raise_error_types=(ValueError))
        def _get_threads(
            section_id: int = None,
            page: int = 0,
            size: int = 50,
            ascending: bool = False,
            session: Session=None,
        ):
            if size <= 0:
                raise ValueError("size must be > 0")

            if page < 0 or page >= self.get_post_max_pages(
                section_id=section_id, size=size
            ):
                raise ValueError(
                    f"Page must be >= 0 and < {self.get_post_max_pages(section_id=section_id, size=size)}"
                )

            # ! leave the boolean operand '==' as 'is' doesn't work.
            query = session.query(Posts).filter(
                Posts.parent_id == None
            )  # Threads have no parent_id  # noqa: E711
            

            if section_id is not None:
                print("searching for section_id =", section_id)
                query = query.filter(Posts.section_id == section_id)

            if ascending:
                query = query.order_by(Posts.date.asc())
            else:
                query = query.order_by(Posts.date.desc())

            threads = query.offset(page * size).limit(size).all()
            print("found", len(threads), "threads")

            return threads
        
        return _get_threads

    @property
    def get_post_max_pages(self):
        @self.SM.session_management()
        def _get_post_max_pages(
            section_id=None, parent_id=None, size=50, session=None
        ):
            query = session.query(func.count(Posts.id))

            if section_id is not None:
                query = query.filter(Posts.section_id == section_id)

            if parent_id is not None:
                query = query.filter(Posts.parent_id == parent_id)

            total_threads = query.scalar()

            if total_threads is None:
                return -1

            return (total_threads + size - 1) // size
        
        return _get_post_max_pages
        
    @property    
    def get_thread_by_id(self):
        @self.SM.session_management()
        def _get_thread_by_id(thread_id, session=None):
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            return thread
        
        return _get_thread_by_id

    @property
    def delete_thread_by_id(self):
        @self.SM.session_management(auto_commit=True)
        def _delete_thread_by_id(thread_id, session=None):
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            if thread:
                session.delete(thread)
                session.commit()
        
        return _delete_thread_by_id
    

    
    @property
    def update_thread_by_id(self):
        @self.SM.session_management(auto_commit=True)
        def _update_thread_by_id(thread_id, title, username, content, image_uuid, section_id, session=None):
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            thread.title = title
            thread.username = username
            thread.content = content
            thread.image_uuid = image_uuid
            thread.section_id = section_id
            session.commit()
        
        return _update_thread_by_id
        
    
        
    @property
    def get_comments_by_thread_id(self):
        @self.SM.session_management()
        def _get_comments_by_thread_id(parent_id, page=0, size=50, session=None):
            if size < 0:
                raise ValueError("size must be >= 0")

            if self.get_post_max_pages(parent_id=parent_id, size=size) == 0:
                return []

            if page < 0 or page >= self.get_post_max_pages(parent_id=parent_id, size=size):
                raise ValueError(
                    f"Page must be >= 0 and < {self.get_post_max_pages(parent_id=parent_id, size=size)}"
                )

            query = session.query(Posts).filter(Posts.parent_id == parent_id)

            query.order_by(Posts.date.desc())

            comments = query.offset(page * size).limit(size).all()

            ret_comments = []
            for c in comments:
                ret_comments.append(c)

            return ret_comments
        
        return _get_comments_by_thread_id
    
    @property
    def create_section(self):
        @self.SM.session_management(auto_commit=True)
        def _create_section(section_name, session=None):
            section = Sections(section_name=section_name)
            session.add(section)
            session.commit()
        
        return _create_section
            

    
    @property
    def get_all_sections(self):
        @self.SM.session_management()
        def _get_all_sections(session=None):
            sections = session.query(Sections).all()
            ret_sections = []
            for s in sections:
                ret_sections.append(s)

            return ret_sections
        return _get_all_sections

    @property
    def get_random_motd(self):
        @self.SM.session_management()
        def _get_random_motd(session=None):
            import random

            motds = session.query(Motds).all()
            motd = random.choice(motds)
            return motd
        
        return _get_random_motd

    @property
    def get_random_post(self):
        @self.SM.session_management()
        def _get_random_post(session=None):
            import random

            posts = session.query(Posts).all()
            post = random.choice(posts)
            return post
        
        return _get_random_post

    @property
    def get_section_by_id(self):
        @self.SM.session_management()
        def _get_section_by_id(section_id, session=None):
            section = session.query(Sections).filter(Sections.id == section_id).first()
            return section
        
        return _get_section_by_id
        
        
    @property
    def register_user(self):
        @self.SM.session_management(auto_commit=True)
        def _register_user(username, password, email, session=None):
            import hashlib

            md5_passwd = hashlib.md5(password.encode()).hexdigest()
            user = Users(username=username, password=md5_passwd, email=email)
            session.add(user)
            session.commit()
            return user.id
        
        return _register_user
    
    @property
    def get_user_by_username(self):
        @self.SM.session_management()
        def _get_user_by_username(username, session=None):
            user = session.query(Users).filter(Users.username == username).first()
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        
        return _get_user_by_username
    
    @property
    def get_user_by_id(self):
        @self.SM.session_management()
        def _get_user_by_id(user_id, session=None):
            user = session.query(Users).filter(Users.id == user_id).first()
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        
        return _get_user_by_id
    
    @property
    def check_user_existence(self):
        @self.SM.session_management()
        def _check_user_existence(username, session=None):
            user = session.query(Users).filter(Users.username == username).first()
            return user is not None
        
        return _check_user_existence
        
        

    def close(self):
        self.engine.dispose()
        self.session_maker.close_all()
