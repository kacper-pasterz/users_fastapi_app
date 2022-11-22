import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from .main import app, get_session, delete, User
import redis


def test_redis_connection():
    redis_host = "redis://redis:6379"
    r = redis.from_url(redis_host)
    print(r.ping())


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def generate():
    return {"email": "john.smith@mail.com",
            "nickname": "Johny"}


def test_create_user(client: TestClient):
    response = client.post(
        "/users",
        json=generate()
    )
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "john.smith@mail.com"
    assert data["nickname"] == "Johny"


def test_create_user_invalid(client: TestClient):
    # given data type/format doesn't match up
    response = client.post(
        "/users",
        json={
            "email": "john.smith@mail.com",
            "nickname": {"message": "You can call me Smith, John Smith"},
        },
    )
    assert response.status_code == 422


def test_get_user_existing_user(session: Session, client: TestClient):
    user_1 = User(email="john.smith@mail.com", nickname="Johny")
    session.add(user_1)
    session.commit()

    response = client.get(f"/users/{user_1.id}")
    assert response.status_code == 200
    assert response.json() == {"email": "john.smith@mail.com",
                               "nickname": "Johny",
                               "id": user_1.id}


def test_get_user_not_existing_user(session: Session, client: TestClient):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == "User not found"


def test_update_user_existing_user(session: Session, client: TestClient):
    user_2 = User(email="john.smith@mail.com", nickname="Johny")
    session.add(user_2)
    session.commit()

    response = client.put(
        f"/users/{user_2.id}",
        json=generate()
    )
    assert response.status_code == 200
    assert response.json() == {"email": "john.smith@mail.com",
                               "nickname": "Johny",
                               "id": user_2.id}


def test_update_user_not_existing_user(session: Session, client: TestClient):
    response = client.put(
        "/users/999",
        json=generate()
    )
    assert response.status_code == 404
    assert response.json() == "User not found"


def test_delete_user_existing_user(session: Session, client: TestClient):
    user_3 = User(email="john.smith@mail.com", nickname="Johny")
    session.add(user_3)
    session.commit()

    response = client.delete(f"/users/{user_3.id}")
    assert response.status_code == 200
    assert response.json() == "User deleted"


def test_delete_user_not_existing_user(session: Session, client: TestClient):
    response = client.delete("/users/999")
    assert response.status_code == 404
    assert response.json() == "User not found"


def test_rabbitmq(rabbitmq):
    """Checks a single, def rabbitmq."""
    channel = rabbitmq.channel()
    assert channel.state == channel.OPEN


if __name__ == '__main__':
    pytest.main()
    delete()
