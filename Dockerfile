# pull official base image
FROM python:3.9-buster

ARG REQUIREMENTS_FILE

WORKDIR /app
EXPOSE 80
ENV PYTHONUNBUFFERED 1

RUN set -x && \
	apt-get update && \
	apt -f install	&& \
	apt-get -qy install netcat && \
	rm -rf /var/lib/apt/lists/* && \
	wget -O /wait-for https://raw.githubusercontent.com/eficode/wait-for/master/wait-for && \
	chmod +x /wait-for

COPY ./docker/ /

COPY ./requirements/ ./requirements
RUN pip install -r ./requirements/prod.txt

COPY . ./

CMD python manage.py collectstatic --no-input && python manage.py migrate && python manage.py runserver 0.0.0.0:8000

