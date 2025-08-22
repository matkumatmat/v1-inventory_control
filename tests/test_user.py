import pytest
from app.models.user import User
from app import db

def test_create_user():
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.check_password("password123") is True