FROM python:3.13-slim

WORKDIR /foodgram

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/foodgram/ ./
COPY data/ /data/
COPY docs/ /docs/

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi:application"]
