import unittest, os
import app as application
from app import app, db

class UserModelCase(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(app.config['BASE_PATH'], 'testdb.sqlite')
        self.app = app.test_client()
        db.create_all()
        # register dummy user
        application.register("user","password", True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register(self):
        # register a new user with username not taken
        username = "test1"
        password = "password"
        admin = True
        application.register(username, password, admin)
        result = application.User.query.filter_by(username=username).first()
        self.assertIsNotNone(result)

    def test_register_taken(self):
        # register a new user with username already taken
        username = "user"
        password = "password"
        admin = True
        # test registration will not proceed if username taken
        self.assertFalse(application.register(username, password, admin))

class Question_SetModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(app.config['BASE_PATH'], 'testdb.sqlite')
        self.app = app.test_client()
        db.create_all()
        # register dummy question set
        qs = application.Question_Set(1, 1, True, "Countries", 5)
        db.session.add(qs)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_delete(self):
        # delete dummy question set from database
        application.delete_quiz([1])
        result = application.Question_Set.query.filter_by(qs_id=1).first()
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
