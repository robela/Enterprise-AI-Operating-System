"""Initialize chat database tables and seed dislike reasons."""
import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from backend.core.database.session import init_db, AsyncSessionLocal
from backend.infrastructure.persistence.models import DislikeReasonModel


async def seed_dislike_reasons(tenant_id: str = "default-tenant"):
    """Seed default dislike reason options."""
    reasons = [
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Too long",
            "category": "length",
            "description": "Response was too verbose",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Too short",
            "category": "length",
            "description": "Response lacked detail",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Inaccurate",
            "category": "accuracy",
            "description": "Information was incorrect",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Outdated",
            "category": "accuracy",
            "description": "Information is no longer current",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Unclear",
            "category": "clarity",
            "description": "Hard to understand",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Confusing",
            "category": "clarity",
            "description": "Content was confusing",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Poor translation",
            "category": "translation",
            "description": "Translation quality was poor",
        },
        {
            "dislike_reason_id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": "Not relevant",
            "category": "relevance",
            "description": "Didn't answer my question",
        },
    ]

    async with AsyncSessionLocal() as session:
        # Check if reasons already exist
        query = select(DislikeReasonModel).where(
            DislikeReasonModel.tenant_id == tenant_id
        )
        result = await session.execute(query)
        existing = result.scalars().first()

        if existing:
            print(f"⚠️  Dislike reasons already exist for tenant {tenant_id}")
            return

        # Insert new reasons
        for reason in reasons:
            model = DislikeReasonModel(
                dislike_reason_id=reason["dislike_reason_id"],
                tenant_id=reason["tenant_id"],
                name=reason["name"],
                category=reason["category"],
                description=reason["description"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(model)

        await session.commit()
        print(f"✅ Seeded {len(reasons)} dislike reasons for tenant {tenant_id}")


async def main():
    """Initialize database and seed data."""
    print("🚀 Initializing chat database...\n")

    # Create all tables
    print("📋 Creating database tables...")
    await init_db()
    print("✅ Database tables created\n")

    # Seed dislike reasons
    print("🌱 Seeding dislike reasons...")
    await seed_dislike_reasons("default-tenant")
    print("\n✨ Chat database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
