from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from contextlib import contextmanager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barky.db'
db = SQLAlchemy(app)

# Domain Model
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200))

# Repository Layer
class SQLAlchemyRepository:
    def __init__(self, model):
        self.model = model

    def add(self, entity):
        db.session.add(entity)

    def delete(self, entity):
        db.session.delete(entity)

    def update(self, entity):
        pass  # The session will track changes to the objects

    def list(self):
        return self.model.query.all()

    def find_by_criteria(self, criteria):
        search = "%{}%".format(criteria)
        return self.model.query.filter(self.model.title.like(search)).all()

# Unit of Work
class UnitOfWork:
    @contextmanager
    def start(self):
        try:
            yield
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.close()

# Service Layer
class BookmarkService:
    def __init__(self, repository, unit_of_work):
        self.repository = repository
        self.unit_of_work = unit_of_work

    def add_bookmark(self, title, url, description):
        with self.unit_of_work.start():
            bookmark = Bookmark(title=title, url=url, description=description)
            self.repository.add(bookmark)
            return bookmark

    def delete_bookmark(self, bookmark_id):
        with self.unit_of_work.start():
            bookmark = Bookmark.query.get(bookmark_id)
            if bookmark:
                self.repository.delete(bookmark)

    def edit_bookmark(self, bookmark_id, title, url, description):
        with self.unit_of_work.start():
            bookmark = Bookmark.query.get(bookmark_id)
            if bookmark:
                bookmark.title = title
                bookmark.url = url
                bookmark.description = description
                # No need to call update explicitly as SQLAlchemy tracks changes

    def list_bookmarks(self):
        with self.unit_of_work.start():
            return self.repository.list()

    def search_bookmarks(self, criteria):
        with self.unit_of_work.start():
            return self.repository.find_by_criteria(criteria)

# Instantiating the service with SQLAlchemy repository and unit of work
bookmark_repository = SQLAlchemyRepository(Bookmark)
unit_of_work = UnitOfWork()
bookmark_service = BookmarkService(bookmark_repository, unit_of_work)

# Flask API aka Presentation Layer
# The Flask routes remain the same, however the service methods would now manage the transactions

if __name__ == '__main__':
    app.run(debug=True)
