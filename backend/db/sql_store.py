from models import UserProfile, ToDo, Instructions
from db import get_session
import uuid

class PostgresStore:
    def search(self, namespace):
        session = get_session()
        kind, user_id = namespace
        if kind == "profile":
            result = session.query(UserProfile).filter_by(user_id=user_id).all()
        elif kind == "todo":
            result = session.query(ToDo).filter_by(user_id=user_id).all()
        elif kind == "instructions":
            result = session.query(Instructions).filter_by(user_id=user_id).all()
        else:
            result = []
        session.close()
        return result

    def put(self, namespace, key, value):
        session = get_session()
        kind, user_id = namespace
        if kind == "profile":
            obj = session.query(UserProfile).filter_by(user_id=user_id).one_or_none()
            if obj is None:
                obj = UserProfile(user_id=user_id)
            # value is expected as json/dict, update fields
            for k, v in value.items():
                setattr(obj, k, v)
            session.merge(obj)
        elif kind == "todo":
            obj = session.query(ToDo).filter_by(id=key).one_or_none()
            if obj is None:
                obj = ToDo(id=key, user_id=user_id)
            for k, v in value.items():
                setattr(obj, k, v)
            session.merge(obj)
        elif kind == "instructions":
            obj = session.query(Instructions).filter_by(user_id=user_id).one_or_none()
            if obj is None:
                obj = Instructions(user_id=user_id)
            obj.instructions = value.get("memory", "")
            session.merge(obj)
        session.commit()
        session.close()

    def get(self, namespace, key):
        session = get_session()
        kind, user_id = namespace
        if kind == "profile":
            return session.query(UserProfile).filter_by(user_id=user_id).one_or_none()
        elif kind == "todo":
            return session.query(ToDo).filter_by(id=key).one_or_none()
        elif kind == "instructions":
            return session.query(Instructions).filter_by(user_id=user_id).one_or_none()
        else:
            return None
