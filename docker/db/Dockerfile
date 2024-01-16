FROM mysql:5.7

#ADD ./mysql-init-files /docker-entrypoint-initdb.d
ENV MYSQL_DATABASE=fastapi
ENV MYSQL_ROOT_PASSWORD=fastapi
EXPOSE 3306
CMD ["mysqld"]