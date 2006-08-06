-- PostgreSQL Database Schema for Chez Bob

CREATE SEQUENCE msgid_seq START 1;
CREATE SEQUENCE userid_seq START 1001;

CREATE TABLE users (
    userid integer PRIMARY KEY NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    userbarcode character varying,
    nickname character varying,
    CONSTRAINT valid_email CHECK (((email)::text ~~ '%@%'::text))
);

CREATE TABLE pwd (
    userid integer PRIMARY KEY NOT NULL,
    p character varying
);

CREATE TABLE profiles (
    userid integer NOT NULL,
    property character varying NOT NULL,
    setting integer NOT NULL
);

CREATE TABLE balances (
    userid integer PRIMARY KEY NOT NULL,
    balance numeric(12,2) NOT NULL
);

CREATE TABLE last_activity (
    userid integer PRIMARY KEY NOT NULL,
    "time" timestamp with time zone
);

CREATE TABLE transactions (
    xacttime timestamp with time zone NOT NULL,
    userid integer NOT NULL,
    xactvalue numeric(12,2) NOT NULL,
    xacttype character varying NOT NULL
);

CREATE TABLE products (
    barcode character varying PRIMARY KEY NOT NULL,
    name character varying NOT NULL,
    phonetic_name character varying NOT NULL,
    price numeric(12,2) NOT NULL,
    stock integer NOT NULL
);

CREATE TABLE bulk_items (
    bulk_barcode character varying NOT NULL,
    bulk_name character varying NOT NULL,
    item_barcode character varying NOT NULL,
    item_quantity integer NOT NULL
);

CREATE TABLE messages (
    msgid integer PRIMARY KEY NOT NULL,
    msgtime timestamp with time zone NOT NULL,
    userid integer,
    message character varying NOT NULL
);

CREATE TABLE books (
    barcode character varying PRIMARY KEY NOT NULL,
    isbn character varying,
    author character varying NOT NULL,
    title character varying NOT NULL
);

CREATE VIEW num_transactions AS
    SELECT transactions.userid, count(*) AS count FROM transactions
        GROUP BY transactions.userid;

CREATE VIEW balances_check AS
    SELECT userid, balance, xactbalance
    FROM ((SELECT transactions.userid,
                  (sum(transactions.xactvalue))::numeric(12,2) AS xactbalance
           FROM transactions GROUP BY transactions.userid) s
          NATURAL JOIN balances);

CREATE FUNCTION query_uid(character varying) RETURNS integer
    AS 'SELECT userid FROM users WHERE username = $1;'
    LANGUAGE sql;

CREATE INDEX profiles_index ON profiles(userid);
CREATE INDEX transactions_user_index ON transactions(userid);
CREATE INDEX transactions_time_index ON transactions(xacttime);
CREATE UNIQUE INDEX users_barcode_index ON users(userbarcode);
CREATE UNIQUE INDEX users_username_index ON users(username);
