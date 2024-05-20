FROM postgres:latest

ARG REPL_USER
ARG REPL_PASSWORD
ARG DB_NAME
ARG DB_PORT

RUN apt update && apt install gettext-base
COPY init.sql /init_template.sql

RUN REPL_USER=$REPL_USER \
    REPL_PASSWORD=$REPL_PASSWORD \
    DB_NAME=$DB_NAME \
    envsubst < /init_template.sql > /docker-entrypoint-initdb.d/init.sql

RUN mkdir /db_logs
RUN chown -R postgres:postgres /db_logs

RUN echo "port = $DB_PORT" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "max_wal_senders = 10" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "wal_level = replica" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "wal_log_hints = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "hot_standby = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "max_replication_slots = 10" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "hot_standby_feedback = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_replication_commands = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "archive_mode = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "archive_command = 'cp %p /oracle/pg_data/archive/%f'" >> /usr/share/postgresql/postgresql.conf.sample

RUN echo "logging_collector = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_statement = 'all'" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_directory = '/db_logs'" >> /usr/share/postgresql/postgresql.conf.sample
