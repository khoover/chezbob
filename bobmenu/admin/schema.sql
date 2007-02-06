-- PostgreSQL Database Schema for Chez Bob

CREATE SEQUENCE msgid_seq
    START 1
    INCREMENT BY 1
    MAXVALUE 2147483647
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE userid_seq
    START 1001
    INCREMENT BY 1
    MAXVALUE 2147483647
    NO MINVALUE
    CACHE 1;

CREATE TABLE users (
    userid integer NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    userbarcode character varying,
    nickname character varying,
    CONSTRAINT valid_email CHECK (((email)::text ~~ '%@%'::text))
);

CREATE TABLE balances (
    userid integer NOT NULL,
    balance numeric(12,2) NOT NULL
);

CREATE TABLE messages (
    msgid integer NOT NULL,
    msgtime timestamp with time zone NOT NULL,
    userid integer,
    message character varying NOT NULL
);

CREATE TABLE transactions (
    xacttime timestamp with time zone NOT NULL,
    userid integer NOT NULL,
    xactvalue numeric(12,2) NOT NULL,
    xacttype character varying NOT NULL,
    barcode character varying,
    source character varying
);

CREATE TABLE pwd (
    userid integer NOT NULL,
    p character varying
);

CREATE TABLE books (
    barcode character varying NOT NULL,
    isbn character varying,
    author character varying NOT NULL,
    title character varying NOT NULL
);

CREATE TABLE products (
    barcode character varying NOT NULL,
    name character varying NOT NULL,
    phonetic_name character varying NOT NULL,
    price numeric(12,2) NOT NULL,
    stock integer DEFAULT 0 NOT NULL,
    bulkid integer
);

CREATE TABLE profiles (
    userid integer NOT NULL,
    property character varying NOT NULL,
    setting integer NOT NULL
);

CREATE TABLE last_activity (
    userid integer NOT NULL,
    "time" timestamp with time zone
);

CREATE FUNCTION query_uid(character varying) RETURNS integer
    AS 'SELECT userid FROM users WHERE username = $1;'
    LANGUAGE sql;

CREATE VIEW num_transactions AS
    SELECT transactions.userid, count(*) AS count FROM transactions GROUP BY transactions.userid;


CREATE VIEW balances_check AS
    SELECT userid, balance, xactbalance FROM ((SELECT transactions.userid, (sum(transactions.xactvalue))::numeric(12,2) AS xactbalance FROM transactions GROUP BY transactions.userid) s NATURAL JOIN balances);

CREATE TABLE aggregate_purchases (
    date date NOT NULL,
    barcode text NOT NULL,
    quantity integer NOT NULL
);

CREATE TABLE bulk_items (
    bulkid serial NOT NULL,
    description text NOT NULL,
    price numeric(12,2) NOT NULL,
    taxable boolean NOT NULL,
    quantity integer NOT NULL,
    updated date DEFAULT now()
);

CREATE TABLE old_products (
    barcode text NOT NULL,
    name text NOT NULL,
    phonetic_name text NOT NULL,
    price numeric(12,2) NOT NULL,
    stock integer NOT NULL,
    bulkid integer
);

CREATE VIEW pricing AS
    SELECT s.barcode, s.name, s.bulkid, s.price, s.cost, ((((s.price / s.cost) - 1.0) * (100)::numeric))::numeric(12,1) AS markup_pct, (s.price - s.cost) AS markup_amt FROM (SELECT barcode, name, bulkid, products.price, (((bulk_items.price * CASE WHEN taxable THEN 1.0775 ELSE 1.0 END) / (quantity)::numeric))::numeric(14,4) AS cost FROM (products JOIN bulk_items USING (bulkid))) s;

CREATE INDEX profiles_index ON profiles USING btree (userid);
CREATE INDEX transactions_user_index ON transactions USING btree (userid);
CREATE INDEX transactions_time_index ON transactions USING btree (xacttime);
CREATE UNIQUE INDEX users_username_index ON users USING btree (username);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);
ALTER TABLE ONLY balances
    ADD CONSTRAINT balances_pkey PRIMARY KEY (userid);
ALTER TABLE ONLY messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (msgid);
ALTER TABLE ONLY pwd
    ADD CONSTRAINT pwd_pkey PRIMARY KEY (userid);
ALTER TABLE ONLY books
    ADD CONSTRAINT books_pkey PRIMARY KEY (barcode);
ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (barcode);
ALTER TABLE ONLY last_activity
    ADD CONSTRAINT last_activity_pkey PRIMARY KEY (userid);
ALTER TABLE ONLY bulk_items
    ADD CONSTRAINT bulk_items_pkey PRIMARY KEY (bulkid);
ALTER TABLE ONLY products
    ADD CONSTRAINT "$1" FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid);
