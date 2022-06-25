FROM snakepacker/python:3.8

# install system-wide deps for python and node
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip
RUN pip install --upgrade pip

# copy our application code
COPY . .

RUN pip install -r requirements.txt

RUN cd Code

# expose port
EXPOSE 80

# start app
CMD [ "python3", "-m", "app" ]