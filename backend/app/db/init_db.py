from app.db.database import engine, Base
from app.models import user, interview, cv  # noqa: F401 – import models to register them


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")
