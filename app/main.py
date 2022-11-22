"""Imported modules"""
from typing import Optional
import redis
from fastapi import FastAPI, Query, Response, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .schemas import User, UserUpdate, UserCreate, UserRead, responses, UserEvent
from sqlmodel import SQLModel, create_engine, Session, select
import os
from fastapi_redis_cache import FastApiRedisCache, cache
import aio_pika
import json

CACHE_PREFIX = 'users_cache'

db_connection_string = f"postgresql://postgres:password@{os.getenv('DATABASE_HOST', 'localhost')}:5432/postgres"
redis_connection_string = 'redis://redis:6379'
engine = create_engine(db_connection_string, pool_pre_ping=True, echo=True)

redis_host = "redis://redis:6379"
r = redis.from_url(redis_host)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


def _invalidate_cache(function_name):
    # "users_cache:main.filter_users(ids=None,email=None,nickname=None)"
    for key in r.scan_iter(f"{CACHE_PREFIX}:main.{function_name}(*"):
        r.delete(key)


async def publish_message(msg):
    connection = await aio_pika.connect('amqp://guest:guest@127.0.0.1')
    async with connection:
        queue_name = "users_queue"

        channel = await connection.channel()
        await channel.declare_queue(queue_name, auto_delete=True)

        message = aio_pika.Message(body=json.dumps(msg.dict()).encode())
        await channel.default_exchange.publish(message, routing_key=queue_name)


@app.on_event("startup")
def app_startup():
    create_tables()
    redis_cache = FastApiRedisCache()
    redis_cache.init(host_url=redis_connection_string,
                     prefix=CACHE_PREFIX, response_header='X-Users-Cache',
                     ignore_arg_types=[Request, Response, Session])
    print("Database connected")


@app.post("/users", response_model=UserRead)
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    """Creates a user with given data"""

    with Session(engine) as session:
        user = User.from_orm(user)
        session.add(user)
        session.commit()
        session.refresh(user)

        _invalidate_cache("filter_users")

        user_event = UserEvent(action_type="create", user=user)

        background_tasks.add_task(publish_message, user_event)

        return user


@app.get("/users/{user_id}", response_model=UserRead)
@cache(expire=30)
def get_user(user_id: int):
    """Gets user's data provided with an ID number"""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            return JSONResponse(status_code=404, content="User not found")

        encoded_user = jsonable_encoder(user)
    return encoded_user


@app.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user: UserUpdate, background_tasks: BackgroundTasks):
    """Overwrites existing user with given data"""
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            return JSONResponse(status_code=404, content="User not found")
        user_data = user.dict(exclude_unset=True)
        for key, value in user_data.items():
            setattr(db_user, key, value)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        _invalidate_cache("filter_users")

        user_event = UserEvent(action_type="update", user=db_user)

        background_tasks.add_task(publish_message, user_event)

        return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, background_tasks: BackgroundTasks):
    """Deletes user's data"""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            return JSONResponse(status_code=404, content="User not found")
        session.delete(user)
        session.commit()

    _invalidate_cache("filter_users")

    user_event = UserEvent(action_type="delete", user=user)

    background_tasks.add_task(publish_message, user_event)

    return JSONResponse(status_code=200, content="User deleted")


@app.get("/users", responses=responses, summary="Pick a filter to search for users with")
@cache(expire=30)
def filter_users(ids: Optional[int] = Query(default=None),
                 email: Optional[str] = Query(default=None),
                 nickname: Optional[str] = Query(default=None)):
    """Gets user's data provided with one of three factors"""

    if (ids and email) or (email and nickname) or (ids and nickname):
        return JSONResponse(status_code=422, content="Invalid parameters")

    if ids:
        with Session(engine) as session:
            statement = select(User).where(User.id == ids)
            user = session.exec(statement).all()
            encoded_user = jsonable_encoder(user)
            return encoded_user

    if email:
        with Session(engine) as session:
            statement = select(User).where(User.email == email)
            user = session.exec(statement).all()
            encoded_user = jsonable_encoder(user)
            return encoded_user

    elif nickname:
        with Session(engine) as session:
            statement = select(User).where(User.nickname == nickname)
            user = session.exec(statement).all()
            encoded_user = jsonable_encoder(user)
            return encoded_user

    else:
        with Session(engine) as session:
            users = session.exec(select(User)).all()
            encoded_users = jsonable_encoder(users)
            return encoded_users


def delete():
    """Deletes all the data"""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            delete_user(user.id)


@app.on_event("shutdown")
def app_shutdown():
    pass
