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
        """Clean up fouled transactions."""
        db.session.rollback()
        self.app_context.pop()
        
    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_messages_show(self):
        """Test showing a message."""

        message = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            response = client.get(f"/messages/{message.id}")
            html = response.get_data(as_text=True)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertIn("Test Message", html)
            self.assertIn(f'href="/users/{self.testuser.id}"', html)

    def test_messages_destroy(self):
        """Test deleting a message."""

        message = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = client.post(f"/messages/{message.id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("Test Message", html)
            self.assertIn(f'href="/users/{self.testuser.id}"', html)

    def test_messages_add_requires_login(self):
        """Test that adding a message requires a logged-in user."""

        with self.client as client:
            response = client.post("/messages/new", data={"text": "Test Message"}, follow_redirects=True)
            html = response.get_data(as_text=True)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertIn("You must be logged in to add a new message", html)
            self.assertNotIn("Test Message", html)

    def test_messages_destroy_requires_login(self):
        """Test that deleting a message requires a logged-in user."""

        message = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            response = client.post(f"/messages/{message.id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertIn("You must be logged in to delete messages", html)
            self.assertIn(f'<h2 class="join-message">Welcome back.</h2>', html)

    def test_messages_destroy_requires_authorization(self):
        """Test that deleting a message requires authorization."""

        message = Message(text="Test Message", user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        unauthorized_user = User.signup(username="unauthorizeduser",
                                        email="unauthorized@test.com",
                                        password="testpassword",
                                        image_url=None)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = unauthorized_user.id

            response = client.post(f"/messages/{message.id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            self.assertIn(f"href=\"/users/{unauthorized_user.id}\"", html)