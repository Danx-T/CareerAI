from app.db.database import engine, Base
from app.models import user, interview, cv

__all__ = ["init_db"]
_models = (user, interview, cv)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")
