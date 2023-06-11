FROM python:3.10.7-bullseye
RUN pip install --upgrade pip
RUN apt update

WORKDIR /app

COPY ./src /app
RUN pip install -r requirements.txt

EXPOSE 5000
EXPOSE 27017

ENV FLASK_APP=front
ENV FLASK_ENV=development

#CMD ["sleep", "infinity"]
CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]
