import os,sys,asyncio
from pathlib import Path
from dotenv import dotenv_values

settings=dotenv_values(Path(__file__).parents[1]/'.env')
default_url=settings.get('DATABASE_URL','postgresql+psycopg://test:test@localhost:5432/livestock_db')
os.environ['DATABASE_URL']=os.environ.get('TEST_DATABASE_URL',default_url.rsplit('/',1)[0]+'/livestock_test')
os.environ['JWT_SECRET_KEY']='unit-test-secret-only-not-a-deployment-key-0000000000'
os.environ['APP_ENV']='test'
os.environ['REDIS_URL']=''
if sys.platform=='win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
