FROM python:3.12

WORKDIR /code

# COPY ./requirements.txt /code/requirements.txt
COPY ./requirements_lock.txt /code/requirements_lock.txt

RUN pip install --no-cache-dir  -r /code/requirements_lock.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
