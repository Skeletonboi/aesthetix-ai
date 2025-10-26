FROM python:3.10

WORKDIR /repo
COPY ./requirements_api.txt /repo/requirements_api.txt
RUN pip install -r requirements_api.txt

COPY ./migrations /repo/migrations
COPY ./alembic.ini /repo/alembic.ini
COPY ./src /repo/src

CMD ["fastapi", "dev", "/repo/src/main.py", "--port", "8000"]