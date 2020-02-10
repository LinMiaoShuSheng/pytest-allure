FROM python:3.6.4

WORKDIR /app

COPY . /app

# for java8, need to download the jdk1.8 before docker build
ADD  jdk_1.8.0_201.zip /export/server/
RUN apt-get update \
    && apt-get install -y unzip --assume-yes \
    && apt-get install -y netstat --assume-yes \
    && mkdir -p /export/server/ \
    && unzip -d /export/server /export/server/jdk_1.8.0_201.zip

# set environment variables
ENV JAVA_HOME /export/server/jdk
ENV JRE_HOME ${JAVA_HOME}/jre
ENV CLASSPATH .:${JAVA_HOME}/lib:${JRE_HOME}/lib
ENV PATH ${JAVA_HOME}/bin:$PATH

# for allure, download allure before docker build or by wget
# RUN  wget https://dl.bintray.com/qameta/generic/io/qameta/allure/allure/2.7.0/allure-2.7.0.zip
ADD allure-2.7.0.zip /export/server/
RUN unzip -d /export/server /export/server/allure-2.7.0.zip
ENV PATH /export/icity/allure/allure-2.7.0/bin:$PATH

# install django & pymysql, replace mysqldb with pymysql, comment code, modify decode to encode
RUN pip install --upgrade pip \
    && pip --default-timeout=100 install django==2.2 \
    && pip --default-timeout=100 install django-cors-headers \
    && pip --default-timeout=100 install pymysql \
    && sed -i "s/MySQLdb/pymysql/g" /usr/local/lib/python3.6/site-packages/django/db/backends/mysql/base.py \
    && sed -i "s/MySQLdb/pymysql/g" /usr/local/lib/python3.6/site-packages/django/db/backends/mysql/introspection.py \
    && sed -i "35i '''" /usr/local/lib/python3.6/site-packages/django/db/backends/mysql/base.py \
    && sed -i "38i '''" /usr/local/lib/python3.6/site-packages/django/db/backends/mysql/base.py \
    && sed -i "s/decode/encode/g" /usr/local/lib/python3.6/site-packages/django/db/backends/mysql/operations.py

EXPOSE 8100

CMD nohup sh -c 'python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0:8100'
