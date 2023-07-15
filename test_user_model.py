"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        
        self.app_context = app.app_context()
        self.app_context.push()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        db.session.commit()
        
        u1 = User.signup("testuser", "test@test.com", "password", None)
        u2 = User.signup("testuser2", "test2@test.com", "password", None)
        
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        f = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)

        db.session.add(f)
        db.session.commit()
        
        self.u1 = u1
        self.u2 = u2
        self.client = app.test_client()

    def tearDown(self):
        """ Clean up any fouled transactions and pop app context."""
        
        db.session.rollback()
        self.app_context.pop()
        
    def test_user_model(self):
        """Does basic model work?"""
        # User should have no messages & no followers
        
        self.assertEqual(len(self.u1.messages), 0)
        self.assertEqual(len(self.u1.followers), 0)

    def test_repr(self):
        """Does the repr method work as expected?"""
        
        self.assertEqual(repr(self.u1), f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_user_signup(self):
        """Does User.create successfully create a new user given valid credentials?"""

        test_user = User.signup("testuser3", "test3@test.com", "password", None)

        db.session.commit()
        
        self.assertEqual(test_user.username, "testuser3")
        self.assertEqual(test_user.email, "test3@test.com")
        self.assertNotEqual(test_user.password, "password")

    def test_invalid_user_signup(self):
        """Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""
        
        invalid_user = User.signup(None, "test@test.com", "password", None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""
            
        user = User.authenticate(self.u1.username, "password")
        self.assertEqual(user.id, self.u1.id)

    def test_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        
        self.assertFalse(User.authenticate("invalid_username", "password"))

    def test_wrong_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?""" 
        
        self.assertFalse(User.authenticate(self.u1.username, "wrong_password"))


