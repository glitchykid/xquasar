FROM python:3.15.2-slim-trixie
RUN apt-get update \
    && apt-get install --yes --no-install-recommends flatpak \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 quasar
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1
COPY xquasar/ xquasar/
COPY tests/ tests/
USER quasar
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
