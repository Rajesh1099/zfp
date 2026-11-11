
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app


test_database_url = settings.database_url


@pytest.fixture(scope="session")
def test_engine():
    from sqlalchemy.engine import make_url

    database_url = make_url(test_database_url).set(
        database="zfp_test"
    )

    engine = create_engine(database_url)

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
    )

    db = TestingSessionLocal()

    yield db

    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
