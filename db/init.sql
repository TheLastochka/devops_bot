SELECT 'CREATE DATABASE ${DB_NAME}' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

SELECT $$ CREATE USER ${REPL_USER} WITH REPLICATION ENCRYPTED PASSWORD '${REPL_PASSWORD}'$$
WHERE NOT EXISTS (SELECT FROM pg_user WHERE usename = '${REPL_USER}')\gexec

\c ${DB_NAME};
CREATE TABLE IF NOT EXISTS emails (
    id serial PRIMARY KEY,
    email VARCHAR(50) NOT NULL
);
CREATE TABLE IF NOT EXISTS phones (
    id serial PRIMARY KEY,
    phone VARCHAR(50) NOT NULL
);

INSERT INTO emails (email)
    SELECT * FROM (
        SELECT 'first@gmail.com' UNION 
        SELECT 'second@gmail.com'
    )
    WHERE NOT EXISTS (SELECT * FROM emails);

INSERT INTO phones (phone)
    SELECT * FROM (
        SELECT '89215551212' UNION 
        SELECT '+79215551212'
    )
    WHERE NOT EXISTS (SELECT * FROM phones);
    