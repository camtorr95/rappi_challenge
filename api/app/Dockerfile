FROM python:3.8
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
COPY /model/ /code/
COPY /static/ /code/
CMD ["python", "./server.py"]