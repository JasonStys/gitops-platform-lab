# Dependency-free adapter of Jason Stys's pinned SRE analyzer; non-root, no credentials.
FROM python:3.14.6-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92
WORKDIR /app
COPY vendor/sre /app/sre
COPY workload /app/workload
COPY LICENSE vendor/LICENSE /app/
RUN apk upgrade --no-cache && python -m pip uninstall --yes pip
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
HEALTHCHECK NONE
ENTRYPOINT ["python", "-m", "workload.server"]
