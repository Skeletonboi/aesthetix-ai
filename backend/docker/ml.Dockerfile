FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.10 python3-pip git

WORKDIR /repo
COPY ./requirements_ml.txt /repo/requirements_ml.txt
RUN pip install -r requirements_ml.txt
RUN playwright install

COPY ./migrations /repo/migrations
COPY ./alembic.ini /repo/alembic.ini
COPY ./src /repo/src

CMD ["fastapi", "dev", "/repo/src/chat/chat_app.py", "--port", "8001"]