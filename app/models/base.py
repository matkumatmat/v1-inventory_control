from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Create a declarative base which all models will inherit from
Base = declarative_base()

# Define a BaseModel with common columns to keep the code DRY (Don't Repeat Yourself)
# This is an abstract class; it won't be created as a table itself.
class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)