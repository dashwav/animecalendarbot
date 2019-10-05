FROM python:3.7-slim as base

FROM base as builder

RUN mkdir /build
WORKDIR /build

COPY requirements.txt /

RUN pip install --prefix=/build -r /requirements.txt

FROM base

COPY --from=builder /build /usr/local
COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
COPY . /app
WORKDIR /app

# ENTRYPOINT [ "tail", "-f", "/dev/null" ]
ENTRYPOINT [ "python", "src/main.py" ]