FROM python:3.11

ENV APP_HOME /usr/src/app

WORKDIR $APP_HOME

COPY . $APP_HOME

EXPOSE 3000

ENTRYPOINT ["python", "main.py"]
