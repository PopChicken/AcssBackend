FROM python:3.10.5-bullseye

COPY requirements.txt /acss_backend/
WORKDIR /acss_backend/
RUN pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

FROM python:3.10.5-alpine3.16

COPY . /acss_backend/
WORKDIR /acss_backend/

COPY --from=0 /usr/local/lib/python3.10/site-packages/ \
    /usr/local/lib/python3.10/site-packages/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]