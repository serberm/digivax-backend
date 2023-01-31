FROM amazonlinux:latest

RUN amazon-linux-extras install python3.8 -y
RUN yum install -y openssl

COPY ./requirements.txt /home/requirements.txt
COPY ./static/fonts/ArialNarrow.ttf /home/static/fonts/ArialNarrow.ttf
COPY ./static/fonts/code128.ttf /home/static/fonts/code128.ttf

WORKDIR /home

RUN pip3.8 install -r requirements.txt

COPY . /home

EXPOSE 5000

WORKDIR /home/api

CMD ["python3.8", "run.py"]

# CMD ["/usr/local/bin/flask","run","--host","0.0.0.0"]
# ENTRYPOINT [ "bash" ]
# CMD [ "python3.8" ]
