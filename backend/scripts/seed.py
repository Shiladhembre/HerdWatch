import asyncio, os, getpass
from datetime import date
from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import User, Animal, Herd, Case, Vaccination, Alert, LabReferral
from app.core.security import hash_password
from app.services.animal_service import point


async def main():
    settings = get_settings()
    if settings.app_env == "production" or not settings.allow_demo_seed:
        raise SystemExit("Set ALLOW_DEMO_SEED=true in development to seed explicitly synthetic records.")
    password = os.environ.get("DEMO_SEED_PASSWORD") or getpass.getpass("Password for demo accounts (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    roles = ["FARMER", "FIELD_WORKER", "VETERINARIAN", "DISTRICT_OFFICER"]
    async with SessionLocal.begin() as db:
        users = []
        for index, role in enumerate(roles):
            email = f"demo.{role.lower()}@example.com"
            user = await db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    full_name=f"Demo {role.replace('_', ' ').title()}",
                    email=email,
                    mobile=f"+91900000010{index}",
                    password_hash=hash_password(password),
                    role=role,
                    state="Maharashtra",
                    district="Pune",
                    block="Demo block",
                    village="Demo Village A",
                    is_verified=True,
                )
                db.add(user)
                await db.flush()
            users.append(user)
        farmer, field, vet, officer = users
        if await db.scalar(select(Animal.id).where(Animal.animal_tag == "DEMO-CATTLE-001")):
            print("Demo seed already present. Existing records and passwords preserved.")
            return
        animal = Animal(
            owner_id=farmer.id,
            animal_tag="DEMO-CATTLE-001",
            species="Cattle",
            breed="Demo breed",
            sex="Female",
            approximate_age=4,
            state="Maharashtra",
            district="Pune",
            block="Demo block",
            village="Demo Village A",
            latitude=18.66,
            longitude=73.92,
            geom=point(18.66, 73.92),
            created_by=farmer.id,
        )
        herd = Herd(
            owner_id=farmer.id,
            herd_name="DEMO cattle herd",
            species="Cattle",
            animal_count=10,
            state="Maharashtra",
            district="Pune",
            block="Demo block",
            village="Demo Village A",
        )
        db.add_all([animal, herd])
        await db.flush()
        case = Case(
            case_reference="DEMO-HW-0001",
            reporter_id=farmer.id,
            owner_id=farmer.id,
            animal_id=animal.id,
            species="Cattle",
            state="Maharashtra",
            district="Pune",
            block="Demo block",
            village="Demo Village A",
            latitude=18.66,
            longitude=73.92,
            geom=point(18.66, 73.92),
            symptom_started_on=date.today(),
            affected_count=1,
            death_count=0,
            observed_symptoms="Synthetic observation for a development workflow.",
            severity="URGENT",
            risk_level="HIGH",
            status="UNDER_REVIEW",
            assigned_veterinarian_id=vet.id,
            notes="DEMO: fictional location and case. No clinical diagnosis.",
        )
        db.add(case)
        await db.flush()
        db.add(
            Vaccination(
                animal_id=animal.id,
                owner_id=farmer.id,
                district="Pune",
                village="Demo Village A",
                vaccine_name="DEMO record — unspecified vaccine",
                disease_target="Not specified",
                dose_number=1,
                administered_on=date.today(),
                administered_by=vet.id,
                notes="Synthetic entry; no official schedule.",
            )
        )
        db.add(
            LabReferral(
                sample_reference="DEMO-LAB-001",
                case_id=case.id,
                animal_id=animal.id,
                owner_id=farmer.id,
                district="Pune",
                requested_by=vet.id,
                sample_type="Veterinarian to specify",
                laboratory_name="DEMO laboratory",
                status="REQUESTED",
                notes="No clinical result is fabricated.",
            )
        )
        db.add(
            Alert(
                type="SYSTEM",
                severity="INFO",
                title="DEMO workspace seeded",
                message="All DEMO records and coordinates are fictional development data.",
                district="Pune",
                created_by=officer.id,
            )
        )
    print("Development seed complete. Accounts: " + ", ".join(f"demo.{r.lower()}@example.com" for r in roles))


if __name__ == "__main__":
    asyncio.run(main())
