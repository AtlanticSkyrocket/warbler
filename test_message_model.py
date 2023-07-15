"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from datetime import datetime

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app since that will have already
# connected to the database)
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app

with app.app_context():
    db.drop_all()
    db.create_all()
class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        self.app_context = app.app_context()
        self.app_context.push()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        
        db.session.commit()
        
        # Create sample user
        user = User.signup(username="testuser2",
                           email="test2@test.com",
                           password="testpassword",
                           image_url=None)

        db.session.add(user)
        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """Clean up any fouled transactions."""
        db.session.rollback()
        self.app_context.pop()

    def test_message_model(self):
        """Does basic model work?"""
        # Create a message
        message = Message(
            text="Test message",
            timestamp=datetime.utcnow(),
            user_id=self.user_id
        )

        db.session.add(message)
        db.session.commit()

        # Check that the message was created successfully
        self.assertEqual(len(Message.query.all()), 1)
        self.assertEqual(message.text, "Test message")
        self.assertEqual(message.timestamp.date(), datetime.utcnow().date())
        self.assertEqual(message.user_id, self.user_id)
        self.assertIsInstance(message.user, User)

    def test_get_top_messages_for_user(self):
        """Does get_top_messages_for_user method return correct messages?"""
        # Create test users
        user1 = User.signup(username="user1",
                            email="user1@test.com",
                            password="testpassword1",
                            image_url=None)

        user2 = User.signup(username="user2",
                            email="user2@test.com",
                            password="testpassword2",
                            image_url=None)
        user3 = User.signup(username="user3",
                    email="user3@test.com",
                    password="testpassword3",
                    image_url=None)

        db.session.add_all([user1, user2, user3])
        db.session.commit()

        # Create messages for users
        message1 = Message(text="Message 1", timestamp=datetime.utcnow(), user_id=user1.id)
        message2 = Message(text="Message 2", timestamp=datetime.utcnow(), user_id=user2.id)
        message3 = Message(text="Message 3", timestamp=datetime.utcnow(), user_id=user1.id)
        message4 = Message(text="Message 4", timestamp=datetime.utcnow(), user_id=user3.id)

        db.session.add_all([message1, message2, message3, message4])
        db.session.commit()

        # User1 follows User2
        follow = Follows(user_being_followed_id=user2.id, user_following_id=user1.id)
        db.session.add(follow)
        db.session.commit()

        # Retrieve top messages for User1 (including their own messages and messages from User2)
        top_messages = Message.get_top_messages_for_user(user1)

        # Check that the correct messages are returned
        self.assertEqual(len(top_messages), 3)
        self.assertIn(message1, top_messages)
        self.assertIn(message2, top_messages)
        self.assertIn(message3, top_messages)
