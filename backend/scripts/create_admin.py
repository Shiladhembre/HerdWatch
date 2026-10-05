import asyncio, getpass
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.core.security import hash_password
from app.schemas.auth import RegisterInput
from app.core.constants import Role


async def main():
    payload = RegisterInput(
        full_name=input("Full name: ").strip(),
        email=input("Email: ").strip(),
        mobile=input("Mobile with country code: ").strip(),
        password=getpass.getpass("Password (12+ characters): "),
        state=input("State: ").strip(),
        district=input("District: ").strip(),
        role=Role.ADMIN,
    )
    async with SessionLocal.begin() as db:
        if await db.scalar(select(User.id).where(User.email == payload.email)):
            raise SystemExit("Account already exists. No changes made.")
        db.add(
            User(
                **payload.model_dump(exclude={"password"}),
                password_hash=hash_password(payload.password),
                is_verified=True,
            )
        )
    print("Administrator created. No credentials were logged.")


if __name__ == "__main__":
    asyncio.run(main())
