from sqlalchemy import create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .migrations.migration import Base, Posts, Sections
from typing import Union
from sqlalchemy.engine.url import URL


class DatabaseManager:
    def __init__(self, db_uri: Union[str, URL] = "sqlite:///:memory:"):
        self.engine = create_engine(db_uri, echo=True)
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def create_thread(
        self,
        username: str,
        section_id: int,
        title: str,
        content: str = None,
        image_uuid: str = None,
        parent_id: int = None,
    ):
        # TODO: check for image_uuid existence, section and parent
        try:
            session = self.Session()
            post = Posts(
                title=title,
                username=username,
                content=content,
                image_uuid=image_uuid,
                section_id=section_id,
                parent_id=parent_id,
            )
            session.add(post)
            session.commit()
            # session.close()
            return post.id
        finally:
            session.close()

    def get_threads(
        self,
        section_id: int = None,
        page: int = 0,
        size: int = 50,
        ascending: bool = False,
    ):
        if size <= 0:
            raise ValueError("size must be > 0")

        if page < 0 or page >= self.get_post_max_pages(
            section_id=section_id, size=size
        ):
            raise ValueError(
                f"Page must be >= 0 and < {self.get_post_max_pages(section_id=section_id, size=size)}"
            )

        try:
            session = self.Session()
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
        finally:
            session.close()

    def get_post_max_pages(self, section_id=None, parent_id=None, size=50):
        try:
            session = self.Session()
            query = session.query(func.count(Posts.id))

            if section_id is not None:
                query = query.filter(Posts.section_id == section_id)

            if parent_id is not None:
                query = query.filter(Posts.parent_id == parent_id)

            total_threads = query.scalar()

            if total_threads is None:
                return -1

            return (total_threads + size - 1) // size
        finally:
            session.close()

    def get_thread_by_id(self, thread_id):
        try:
            session = self.Session()
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            return thread
        finally:
            session.close()

    def delete_thread_by_id(self, thread_id):
        try:
            session = self.Session()
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            if thread:
                session.delete(thread)
                session.commit()
        finally:
            session.close()

    def update_thread_by_id(
        self, thread_id, title, username, content, image_uuid, section_id
    ):
        try:
            session = self.Session()
            thread = session.query(Posts).filter(Posts.id == thread_id).first()
            thread.title = title
            thread.username = username
            thread.content = content
            thread.image_uuid = image_uuid
            thread.section_id = section_id
            session.commit()
        finally:
            session.close()

    def get_comments_by_thread_id(self, parent_id, page=0, size=50):
        if size < 0:
            raise ValueError("size must be >= 0")

        if self.get_post_max_pages(parent_id=parent_id, size=size) == 0:
            return []

        if page < 0 or page >= self.get_post_max_pages(parent_id=parent_id, size=size):
            raise ValueError(
                f"Page must be >= 0 and < {self.get_post_max_pages(parent_id=parent_id, size=size)}"
            )

        try:
            session = self.Session()
            query = session.query(Posts).filter(Posts.parent_id == parent_id)

            query.order_by(Posts.date.desc())

            comments = query.offset(page * size).limit(size).all()
            return comments
        finally:
            session.close()

    def create_section(self, section_name):
        try:
            session = self.Session()
            section = Sections(section_name=section_name)
            session.add(section)
            session.commit()
        finally:
            session.close()

    def get_all_sections(self):
        try:
            session = self.Session()
            sections = session.query(Sections).all()
            return sections
        finally:
            session.close()

    def close(self):
        self.engine.dispose()
        self.Session.close_all()
