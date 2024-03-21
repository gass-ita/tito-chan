from functools import wraps
from typing import Union
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import InvalidRequestError


def session_management(auto_commit=False):
    """
    Decorator to manage the session for the database operations.

    If a session is provided as a parameter, it will be used. Otherwise, a new session will be created and closed after the function is called.

    args:
        auto_commit (bool): If True, the session will be committed after the function is called and all the attributes of the session. Defaults to False.

    This decorator is used to manage the session for the database operations.

    Add to the parameters of the function to be decorated a parameter called session with a default value of None.

    The function will be called with the session as a parameter, and the session will be closed after the function is called.

    If the function raises an exception, the session will be rolled back and closed.

    The decorated function must be a method of a class that has a session_maker attribute that is a sessionmaker object.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if "session" in kwargs and kwargs["session"]:
                return func(self, *args, **kwargs)

            print("session management called...")
            session: Union[Session | None] = self.session_maker()
            print("session created...")
            try:
                kwargs["session"] = session
                result = func(self, *args, **kwargs)
                if auto_commit:
                    try:
                        session.commit()
                        # reload all the objects
                        if result:
                            for obj in session:
                                session.refresh(obj)
                    except InvalidRequestError:
                        pass
                return result
            except:
                session.rollback()
                session.close()
                raise
            finally:
                if session:
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

    return decorator