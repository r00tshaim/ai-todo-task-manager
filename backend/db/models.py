from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "profiles"
    user_id = Column(String, primary_key=True)
    name = Column(String)
    location = Column(String)
    job = Column(String)
    connections = Column(JSONB)  # List[str]
    interests = Column(JSONB)    # List[str]

class ToDo(Base):
    __tablename__ = "todos"
    id = Column(String, primary_key=True)          # UUID
    user_id = Column(String, index=True)
    task = Column(Text)
    time_to_complete = Column(Integer)
    deadline = Column(DateTime)
    solutions = Column(JSONB)                      # List[str]
    status = Column(String, default="not started") # not started | in progress | done | archived

class Instructions(Base):
    __tablename__ = "instructions"
    user_id = Column(String, primary_key=True)
    instructions = Column(Text)
