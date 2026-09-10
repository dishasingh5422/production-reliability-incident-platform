import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test-reliability.db"
os.environ["ENABLE_FAULT_INJECTION"] = "true"
os.environ["FAULT_ADMIN_TOKEN"] = "test-admin-token"
os.environ["RECOVERY_SUCCESS_THRESHOLD"] = "2"
os.environ["INCIDENT_PROVIDER"] = "mock"

from app.core.faults import fault_controller  # noqa: E402
from app.db.base import Base, SessionLocal, engine  # noqa: E402
from app.db.models import CorrectiveAction, DeploymentEvent, Incident, ServiceCheck  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        session.execute(delete(CorrectiveAction))
        session.execute(delete(Incident))
        session.execute(delete(DeploymentEvent))
        session.execute(delete(ServiceCheck))
        session.commit()
    fault_controller.recover()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
