import psycopg
from sqlalchemy.engine import make_url
from app.config import get_settings

def main():
    url=make_url(get_settings().database_url)
    with psycopg.connect(host=url.host,port=url.port or 5432,user=url.username,password=url.password,dbname='postgres',autocommit=True) as db:
        if not db.execute("SELECT 1 FROM pg_database WHERE datname='livestock_test'").fetchone(): db.execute('CREATE DATABASE livestock_test')
    print('Disposable database livestock_test is ready. No existing database was removed.')

if __name__=='__main__': main()
