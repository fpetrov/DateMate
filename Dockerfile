FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# COPY pyproject.toml README.md ./
# RUN pip install --upgrade pip && pip install .

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "datemate.main"]