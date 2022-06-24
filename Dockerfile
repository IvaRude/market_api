FROM snakepacker/python:3.8

# install system-wide deps for python and node
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip
RUN pip install --upgrade pip
#  python-dev

# copy our application code
COPY . .
# Без этих пакетов не устанавливается psycopg2
RUN apt-get -yqq install gcc g++ build-essential
RUN apt-get -yqq install python3-dev
RUN apt-get -yqq install libpq-dev

RUN pip install -r requirements.txt

RUN cd Code

# expose port
EXPOSE 80

# start app
CMD [ "python3", "-m", "app" ]