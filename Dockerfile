FROM python:3.10.14-slim-bookworm
WORKDIR /capstone
COPY ./requirements.txt /capstone
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
CMD [ "python3", "-m" , "flask", "run", "--host", "0.0.0.0"]