from sqlalchemy import create_engine, func, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .migrations.migration import Base, Posts, Sections, Motds
from typing import Union
from sqlalchemy.engine.url import URL
from functools import wraps
from sqlalchemy.exc import InvalidRequestError


class DatabaseManager:
    def __init__(self, db_uri: Union[str, URL] = "sqlite:///:memory:"):
        self.engine = create_engine(db_uri, echo=True)
        self.Base = declarative_base()
        self.session_maker = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def session_management(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            print("session management called...")
            session = self.session_maker()
            print("session created...")
            try:
                kwargs["session"] = session
                result = func(self, *args, **kwargs)
                return result
            except:
                session.rollback()
                session.close()
                raise
            finally:
                if session:
                    try:
                        print("committing session...")
                        session.commit()
                        print("committed!")
                        pass
                    except InvalidRequestError:
                        print("already committed!")
                        pass
                    if session.is_active:
                        try:
                            print("closing session...")
                            session.close()
                            print("closed!")
                            pass
                        except InvalidRequestError:
                            print("already closed!")
                            pass

        return wrapper

    def get_base_obj_properties(self, base_obj):
        # Get the mapper for the base object
        mapper = inspect(base_obj.__class__)

        # Extract the properties of the base object
        base_properties = {
            prop.key: getattr(base_obj, prop.key) for prop in mapper.attrs
        }

        class ObjectWithProperties:
            def __init__(self, properties):
                self.__dict__.update(properties)

        obj = ObjectWithProperties(base_properties)

        return obj

    @session_management
    def create_thread(
        self,
        username: str,
        section_id: int,
        title: str,
        content: str = None,
        image_uuid: str = None,
        parent_id: int = None,
        session=None,
    ):
        # TODO: check for image_uuid existence, section and parent

        post = Posts(
            title=title,
            username=username,
            content=content,
            image_uuid=image_uuid,
            section_id=section_id,
            parent_id=parent_id,
        )
        session.add(post)

        post_obj = self.get_base_obj_properties(post)

        session.commit()

        return post_obj.id

    @session_management
    def get_threads(
        self,
        section_id: int = None,
        page: int = 0,
        size: int = 50,
        ascending: bool = False,
        session=None,
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

        ret_threads = []

        for t in threads:
            ret_threads.append(self.get_base_obj_properties(t))

        return ret_threads

    @session_management
    def get_post_max_pages(
        self, section_id=None, parent_id=None, size=50, session=None
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

    @session_management
    def get_thread_by_id(self, thread_id, session=None):
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        return self.get_base_obj_properties(thread)

    @session_management
    def delete_thread_by_id(self, session, thread_id):
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        if thread:
            session.delete(thread)
            session.commit()

    @session_management
    def update_thread_by_id(
        self, thread_id, title, username, content, image_uuid, section_id, session=None
    ):
        thread = session.query(Posts).filter(Posts.id == thread_id).first()
        thread.title = title
        thread.username = username
        thread.content = content
        thread.image_uuid = image_uuid
        thread.section_id = section_id
        session.commit()

    @session_management
    def get_comments_by_thread_id(self, parent_id, page=0, size=50, session=None):
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
            ret_comments.append(self.get_base_obj_properties(c))

        return ret_comments

    @session_management
    def create_section(self, section_name, session=None):
        section = Sections(section_name=section_name)
        session.add(section)
        session.commit()

    @session_management
    def get_all_sections(self, session=None):
        sections = session.query(Sections).all()
        ret_sections = []
        for s in sections:
            ret_sections.append(self.get_base_obj_properties(s))

        return ret_sections

    @session_management
    def get_random_motd(self, session=None):
        import random

        motds = session.query(Motds).all()
        motd = random.choice(motds)
        return self.get_base_obj_properties(motd)

    @session_management
    def get_random_post(self, session=None):
        import random

        posts = session.query(Posts).all()
        post = random.choice(posts)
        return self.get_base_obj_properties(post)

    @session_management
    def get_section_by_id(self, section_id, session=None):
        section = session.query(Sections).filter(Sections.id == section_id).first()
        return self.get_base_obj_properties(section)

    def close(self):
        self.engine.dispose()
        self.session_maker.close_all()
