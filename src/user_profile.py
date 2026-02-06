from dataclasses import dataclass, asdict
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.engine import Engine

from src.database.utils import get_engine
from src.database.models import user_profiles


@dataclass
class UserProfile:
    name: str

    # User ID - automatically assigned by database
    id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any], id: Optional[int] = None) -> "UserProfile":
        return cls(**data, id=id)

    def save(self, engine: Engine | None = None) -> int:
        engine = engine or get_engine()
        with engine.begin() as conn:
            if self.id is None:
                result = conn.execute(user_profiles.insert().values(data=self.to_dict()))
                inserted = result.inserted_primary_key
                if not inserted:
                    raise RuntimeError("Failed to insert user profile")
                self.id = inserted[0]
            else:
                conn.execute(
                    user_profiles.update()
                    .where(user_profiles.c.id == self.id)
                    .values(data=self.to_dict())
                )
        return self.id

    @classmethod
    def load(cls, profile_id: int) -> "UserProfile":
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                select(user_profiles.c.data).where(user_profiles.c.id == profile_id)
            ).one_or_none()
            if row is None:
                raise KeyError(f"No profile with id={profile_id}")
            return cls.from_dict(row.data, id=profile_id)
