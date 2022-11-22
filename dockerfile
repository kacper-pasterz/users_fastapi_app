FROM python:alpine

WORKDIR /container_app

RUN apk add --no-cache gcc linux-headers musl-dev g++ && pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install

EXPOSE 4001

ENV PYTHONUNBUFFERED=1

COPY ./app ./

CMD ["uvicorn","main:app","--reload","--host","0.0.0.0","--port","4001"]
