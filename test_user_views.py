"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        self.app_context = app.app_context()
        self.app_context.push()
        
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
        
    def tearDown(self):
        """Remove any fouled transaction."""
        db.session.rollback()
        self.app_context.pop()
        
    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                self.testuser = db.session.merge(self.testuser)
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_unauthenticated(self):
        """Is user prohibited from adding a message when not authenticated?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            # Expecting a 302 redirect to the login page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/login")

    def test_delete_own_message(self):
        """Can user delete their own message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                self.testuser = db.session.merge(self.testuser)
                sess[CURR_USER_KEY] = self.testuser.id

            # Create a test message
            message = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(message)
            db.session.commit()

            # Send a DELETE request to delete the message
            resp = c.post(f"/messages/{message.id}/delete")

            # Expecting a 302 redirect to the user's page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{self.testuser.id}")
            
            # Check that the message is deleted from the database
            deleted_message = db.session.get(Message, message.id)
            self.assertIsNone(deleted_message)

    def test_delete_other_user_message(self):
        """Is user prohibited from deleting another user's message?"""

        # Create another user
        other_user = User.signup(username="otheruser", email="other@test.com", password="otheruser", image_url=None)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                self.testuser = db.session.merge(self.testuser)
                sess[CURR_USER_KEY] = self.testuser.id

            # Create a test message owned by the other user
            message = Message(text="Test message", user_id=other_user.id)
            db.session.add(message)
            db.session.commit()

            # Send a DELETE request to delete the message
            resp = c.post(f"/messages/{message.id}/delete")

            # Expecting a 401 Unauthorized status code
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

            # Check that the message is not deleted from the database
            existing_message = db.session.get(Message, message.id)
            self.assertIsNotNone(existing_message)

    def test_delete_message_unauthenticated(self):
        """Is user prohibited from deleting a message when not authenticated?"""

        with self.client as c:
            # Create a test message
            message = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(message)
            db.session.commit()

            # Send a DELETE request to delete the message
            resp = c.post(f"/messages/{message.id}/delete")

            # Expecting a 302 redirect to the login page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/login")

    def test_view_followers_authenticated(self):
        """Can user view the followers page when authenticated?"""

        with self.client as c:
            with c.session_transaction() as sess:
                self.testuser = db.session.merge(self.testuser)
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")

            # Expecting a 200 OK response
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.location, None)

    def test_view_followers_unauthenticated(self):
        """Is user prohibited from viewing the followers page when not authenticated?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers")

            # Expecting a 302 redirect to the login page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/login")

    def test_view_following_authenticated(self):
        """Can user view the following page when authenticated?"""

        with self.client as c:
            with c.session_transaction() as sess:
                self.testuser = db.session.merge(self.testuser)
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/following")

            # Expecting a 200 OK response
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.location, None)

    def test_view_following_unauthenticated(self):
        """Is user prohibited from viewing the following page when not authenticated?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following")

            # Expecting a 302 redirect to the login page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/login")



