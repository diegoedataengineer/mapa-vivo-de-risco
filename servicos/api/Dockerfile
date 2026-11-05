FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
RUN pip install -q --no-cache-dir .
COPY mvr_api ./mvr_api
RUN useradd -r -u 10001 mvr
USER mvr
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude')" || exit 1
CMD ["uvicorn", "mvr_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
