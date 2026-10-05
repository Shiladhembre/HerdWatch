import os
from uuid import uuid4
import pytest,pytest_asyncio,httpx
from sqlalchemy import text
from sqlalchemy.engine import make_url
from app.database import SessionLocal,engine,get_db
from app.models import User
from app.main import app
from app.core.security import hash_password

@pytest_asyncio.fixture
async def db():
    assert make_url(os.environ['DATABASE_URL']).database.endswith('_test'), 'Integration tests require a dedicated *_test database.'
    async with SessionLocal() as session:
        await session.execute(text('SELECT 1 FROM alembic_version'))
        yield session
        await session.rollback()
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db):
    async def override(): yield db
    app.dependency_overrides[get_db]=override
    transport=httpx.ASGITransport(app=app,raise_app_exceptions=False,client=(uuid4().hex,12345))
    async with httpx.AsyncClient(transport=transport,base_url='http://test') as client: yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def users(db):
    result={}
    for i,role in enumerate(['FARMER','FIELD_WORKER','VETERINARIAN','DISTRICT_OFFICER','ADMIN']):
        u=User(full_name=f'Test {role}',email=f'{uuid4().hex}@example.com',mobile=f'+91{str(uuid4().int)[:10]}',password_hash=hash_password('Testing-password-123'),role=role,state='Maharashtra',district='Pune',village='Test Village',is_verified=True)
        db.add(u);await db.flush();result[role]=u
    other=User(full_name='Other farmer',email=f'{uuid4().hex}@example.com',mobile=f'+91{str(uuid4().int)[:10]}',password_hash=hash_password('Testing-password-123'),role='FARMER',state='Maharashtra',district='Satara',village='Other Village')
    db.add(other);await db.flush();result['OTHER']=other
    return result

async def login(client,user):
    response=await client.post('/api/v1/auth/login',json={'identifier':user.email,'password':'Testing-password-123'})
    assert response.status_code==200,response.text
    data=response.json()['data'];return {'Authorization':'Bearer '+data['access_token']},data
