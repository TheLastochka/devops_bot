FROM postgres:latest

ARG PGUSER
ARG DB_PORT

RUN mkdir /db_logs
RUN chown -R postgres:postgres /db_logs

RUN echo "#!/bin/bash" > /usr/local/bin/init.sh && \
    echo "rm -rf /var/lib/postgresql/data/*" >> /usr/local/bin/init.sh && \
    echo "until pg_basebackup -R -h db -p $DB_PORT -D /var/lib/postgresql/data -U ${PGUSER} -vP -w; do" >> /usr/local/bin/init.sh && \
    echo "  echo 'Replica not ready, trying again...'" >> /usr/local/bin/init.sh && \
    echo "  sleep 1" >> /usr/local/bin/init.sh && \
    echo "done" >> /usr/local/bin/init.sh && \
    echo "echo 'Backup done, starting replica...'" >> /usr/local/bin/init.sh && \
    echo "chown -R postgres:postgres /var/lib/postgresql/data" >> /usr/local/bin/init.sh && \
    echo "chmod 700 /var/lib/postgresql/data" >> /usr/local/bin/init.sh && \
    echo "su - postgres -c '/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data'" >> /usr/local/bin/init.sh
    
RUN chmod +x /usr/local/bin/init.sh

CMD ["/usr/local/bin/init.sh"]
