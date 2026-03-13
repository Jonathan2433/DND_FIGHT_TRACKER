"""SQLAlchemy repository implementations."""

from typing import Any, Iterable

class SqlAlchemyRepository:
    def __init__(self, model):
        self.model = model

    def get(self, entity_id: Any):
        return self.model.query.get(entity_id)

    def get_or_404(self, entity_id: Any):
        return self.model.query.get_or_404(entity_id)

    def add(self, entity):
        from app.extensions import db
        db.session.add(entity)

    def remove(self, entity):
        from app.extensions import db
        db.session.delete(entity)

    def list(self, **filters: Any) -> Iterable[Any]:
        return self.model.query.filter_by(**filters).all()

class UserRepository(SqlAlchemyRepository):
    pass

class CampaignRepository(SqlAlchemyRepository):
    pass

class CharacterRepository(SqlAlchemyRepository):
    pass

class CombatRepository(SqlAlchemyRepository):
    pass
