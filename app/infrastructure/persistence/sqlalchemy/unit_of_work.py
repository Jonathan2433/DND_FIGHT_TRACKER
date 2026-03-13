"""SQLAlchemy Unit of Work implementation."""

from app.extensions import db

class SqlAlchemyUnitOfWork:
    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()

    def flush(self):
        db.session.flush()
