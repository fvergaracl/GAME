FROM tiangolo/uvicorn-gunicorn:python3.11

COPY . /home

# show all files in /home
RUN ls -la /home

WORKDIR /home
ENV ENV=dev
RUN pip install "poetry==1.7.1"
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN chmod +x /home/docker/api/startup.sh
ENTRYPOINT /home/docker/api/startup.sh