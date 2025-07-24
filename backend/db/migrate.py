from models import Base
from db import engine
Base.metadata.create_all(bind=engine)
print("SQLAlchemy models created (metadata.create_all)")

from ..agent import across_thread_memory
across_thread_memory.setup()
print("PostgresStore setup completed")