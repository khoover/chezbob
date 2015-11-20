 -- "django" schema
CREATE SCHEMA django;
SET search_path = django, pg_catalog;
SET default_with_oids = false;

CREATE TABLE auth_group (
    id serial NOT NULL,
    name character varying(80) NOT NULL
);

CREATE TABLE auth_group_permissions (
    id serial NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);

CREATE TABLE auth_message (
    id serial NOT NULL,
    user_id integer NOT NULL,
    message text NOT NULL
);

CREATE TABLE auth_permission (
    id serial NOT NULL,
    name character varying(50) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);

CREATE TABLE auth_user (
    id serial NOT NULL,
    username character varying(30) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(75) NOT NULL,
    "password" character varying(128) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    last_login timestamp with time zone NOT NULL,
    date_joined timestamp with time zone NOT NULL
);

CREATE TABLE auth_user_groups (
    id serial NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);

CREATE TABLE auth_user_user_permissions (
    id serial NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);

CREATE TABLE cashout_cashcount (
    id serial NOT NULL,
    cashout_id integer NOT NULL,
    entity_id integer NOT NULL,
    memo character varying(256) NOT NULL,
    bill100 integer NOT NULL,
    bill50 integer NOT NULL,
    bill20 integer NOT NULL,
    bill10 integer NOT NULL,
    bill5 integer NOT NULL,
    bill1 integer NOT NULL,
    coin100 integer NOT NULL,
    coin50 integer NOT NULL,
    coin25 integer NOT NULL,
    coin10 integer NOT NULL,
    coin5 integer NOT NULL,
    coin1 integer NOT NULL,
    other numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL
);

CREATE TABLE cashout_cashout (
    id serial NOT NULL,
    datetime timestamp with time zone NOT NULL,
    notes text NOT NULL
);

CREATE TABLE cashout_entity (
    id serial NOT NULL,
    name character varying(256) NOT NULL
);

CREATE TABLE cashout_transaction (
    id serial NOT NULL,
    datetime timestamp with time zone NOT NULL,
    notes text NOT NULL
);

CREATE TABLE django_admin_log (
    id serial NOT NULL,
    action_time timestamp with time zone NOT NULL,
    user_id integer NOT NULL,
    content_type_id integer,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);

CREATE TABLE django_content_type (
    id serial NOT NULL,
    name character varying(100) NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);

 -- default schema
SET search_path = public, pg_catalog;
SET default_with_oids = true;

CREATE VIEW aggregate_purchases AS
    SELECT
        date(xacttime) AS date,
        transactions.barcode AS barcode,
        count(*) AS quantity,
        CAST ( -1 * sum(xactvalue) AS numeric(12,2)) AS price,
        bulkid AS bulkid
    FROM transactions
        INNER JOIN products
            ON products.barcode = transactions.barcode
    WHERE
        bulkid IS NOT NULL
        AND transactions.barcode IS NOT NULL
    GROUP BY transactions.barcode, date(xacttime), bulkid;

CREATE SEQUENCE transactions_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE TABLE transactions (
    xacttime timestamp with time zone NOT NULL,
    userid integer NOT NULL,
    xactvalue numeric(12,2) NOT NULL,
    xacttype character varying NOT NULL,
    barcode character varying,
    source character varying,
    id integer DEFAULT nextval('transactions_id_seq'::regclass) NOT NULL,
    finance_trans_id integer
);

SET default_with_oids = false;

CREATE TABLE users (
    userid integer NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    nickname character varying,
    pwd text,
    balance numeric(12,2) DEFAULT 0.00 NOT NULL,
    disabled boolean DEFAULT false NOT NULL,
    last_purchase_time timestamp with time zone,
    last_deposit_time timestamp with time zone,
    pref_auto_logout boolean DEFAULT false NOT NULL,
    pref_speech boolean DEFAULT false NOT NULL,
    pref_forget_which_product boolean DEFAULT false NOT NULL,
    pref_skip_purchase_confirm boolean DEFAULT false NOT NULL,
    CONSTRAINT valid_email CHECK (((email)::text ~~ '%@%'::text))
);

CREATE VIEW balances_check AS
    SELECT u.userid, u.balance, s.xactbalance FROM (users u LEFT JOIN (SELECT transactions.userid, (sum(transactions.xactvalue))::numeric(12,2) AS xactbalance FROM transactions GROUP BY transactions.userid) s USING (userid));

CREATE TABLE products (
    barcode character varying NOT NULL,
    name character varying NOT NULL,
    phonetic_name character varying NOT NULL,
    price numeric(12,2) NOT NULL,
    bulkid integer,
    coffee boolean DEFAULT false NOT NULL
);

CREATE VIEW bulk_aggregate_purchases AS
    SELECT p.bulkid, ap.date, sum(ap.quantity) AS quantity FROM (aggregate_purchases ap JOIN products p ON ((ap.barcode = (p.barcode)::text))) GROUP BY p.bulkid, ap.date;

CREATE TABLE bulk_items (
    bulkid serial NOT NULL,
    description text NOT NULL,
    price numeric(12,2) NOT NULL,
    taxable boolean NOT NULL,
    quantity integer NOT NULL,
    updated date DEFAULT now(),
    crv numeric(12,2),
    crv_taxable boolean NOT NULL,
    source integer DEFAULT 0 NOT NULL,
    reserve integer DEFAULT 0 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    floor_location integer NOT NULL,
    product_id text,
    crv_per_unit numeric(12,2)
);

CREATE TABLE order_items (
    id serial NOT NULL,
    order_id integer NOT NULL,
    bulk_type_id integer NOT NULL,
    quantity integer NOT NULL,
    number integer NOT NULL,
    case_cost numeric(12,2) DEFAULT 0.00 NOT NULL,
    crv_per_unit numeric(12,2) DEFAULT 0.00 NOT NULL,
    is_cost_taxed boolean DEFAULT false NOT NULL,
    is_crv_taxed boolean DEFAULT false NOT NULL,
    is_cost_migrated boolean DEFAULT false NOT NULL
);

CREATE TABLE orders (
    id serial NOT NULL,
    date date NOT NULL,
    description character varying(256) NOT NULL,
    amount numeric(12,2) NOT NULL,
    tax_rate numeric(6,4) NOT NULL
);

CREATE VIEW daily_units_delta AS
    SELECT CASE WHEN (ap.date IS NULL) THEN o.date ELSE ap.date END AS date, CASE WHEN (ap.bulkid IS NULL) THEN oi.bulk_type_id ELSE ap.bulkid END AS bulkid, CASE WHEN (oi.quantity IS NULL) THEN (- ap.quantity) WHEN (ap.quantity IS NULL) THEN ((oi.quantity * oi.number))::bigint ELSE ((oi.quantity * oi.number) - ap.quantity) END AS delta FROM (bulk_aggregate_purchases ap FULL JOIN (orders o JOIN order_items oi ON ((o.id = oi.order_id))) ON (((ap.date = o.date) AND (oi.bulk_type_id = ap.bulkid))));

CREATE TABLE inventory (
    date date NOT NULL,
    bulkid integer NOT NULL,
    units integer NOT NULL,
    cases double precision,
    loose_units integer,
    case_size integer NOT NULL
);

CREATE VIEW inventory_checkpoints AS
    SELECT id.date, i.date AS "checkpoint", i.units, i.bulkid FROM ((SELECT DISTINCT aggregate_purchases.date FROM aggregate_purchases WHERE (aggregate_purchases.date >= '2007-11-01'::date) ORDER BY aggregate_purchases.date) id LEFT JOIN inventory i ON (((i.date < id.date) AND (NOT (EXISTS (SELECT ii.date, ii.bulkid, ii.units FROM inventory ii WHERE (((ii.date > i.date) AND (ii.date < id.date)) AND (ii.bulkid = i.bulkid))))))));

CREATE VIEW expected_inventory AS
    SELECT ic.date, ic.bulkid, CASE WHEN (sum(dud.delta) IS NULL) THEN (ic.units)::numeric ELSE ((ic.units)::numeric + sum(dud.delta)) END AS expected_units, p.price AS unit_price, CASE WHEN (sum(dud.delta) IS NULL) THEN (0)::numeric ELSE (((ic.units)::numeric + sum(dud.delta)) * p.price) END AS total_expected_value FROM ((inventory_checkpoints ic LEFT JOIN daily_units_delta dud ON ((((dud.date <= ic.date) AND (dud.date > ic."checkpoint")) AND (dud.bulkid = ic.bulkid)))) JOIN (SELECT products.bulkid, min(products.price) AS price FROM products GROUP BY products.bulkid) p ON ((p.bulkid = ic.bulkid))) GROUP BY ic.date, ic.bulkid, ic.units, p.price;

CREATE TABLE finance_accounts (
    id serial NOT NULL,
    "type" character varying(1) NOT NULL,
    name character varying(256) NOT NULL
);

CREATE TABLE finance_deposit_summary (
    date date NOT NULL,
    positive numeric(12,2) NOT NULL,
    negative numeric(12,2) NOT NULL
);

CREATE TABLE finance_inventory_summary (
    date date NOT NULL,
    value numeric(12,2),
    shrinkage numeric(12,2)
);

CREATE TABLE finance_splits (
    id serial NOT NULL,
    transaction_id integer NOT NULL,
    account_id integer NOT NULL,
    amount numeric(12,2) NOT NULL,
    memo character varying(256) NOT NULL
);

CREATE TABLE finance_transactions (
    id serial NOT NULL,
    date date NOT NULL,
    description text NOT NULL,
    auto_generated boolean NOT NULL
);

CREATE TABLE floor_locations (
    id integer NOT NULL,
    name text NOT NULL,
    markup double precision NOT NULL
);

CREATE TABLE historic_prices (
    bulkid integer NOT NULL,
    date date NOT NULL,
    price numeric(12,2) NOT NULL
);

CREATE VIEW loss_report AS
    SELECT ei.bulkid, ei.date, (ei.expected_units - (ai.units)::numeric) AS losses, ((ei.expected_units - (ai.units)::numeric) * ei.unit_price) AS value_loss FROM (expected_inventory ei JOIN inventory ai ON (((ei.bulkid = ai.bulkid) AND (ei.date = ai.date))));

CREATE TABLE messages (
    msgid integer NOT NULL,
    msgtime timestamp with time zone NOT NULL,
    userid integer,
    message character varying NOT NULL
);

CREATE SEQUENCE msgid_seq
    INCREMENT BY 1
    MAXVALUE 2147483647
    NO MINVALUE
    CACHE 1;

CREATE VIEW order_purchases_summary AS
    SELECT o.date, i.bulk_type_id AS bulkid, (i.quantity * i.number) AS quantity, ((((i.number)::numeric * (CASE WHEN i.is_cost_taxed THEN ((1)::numeric + o.tax_rate) ELSE 1.0 END * i.case_cost)) + (((i.quantity * i.number))::numeric * (CASE WHEN i.is_crv_taxed THEN ((1)::numeric + o.tax_rate) ELSE 1.0 END * i.crv_per_unit))) + 0.000000) AS cost FROM (orders o JOIN order_items i ON ((o.id = i.order_id)));

CREATE TABLE product_source (
    sourceid serial NOT NULL,
    source_description character varying(50)
);

CREATE TABLE profiles (
    userid integer NOT NULL,
    property character varying NOT NULL,
    setting integer NOT NULL
);

CREATE TABLE userbarcodes (
    userid integer NOT NULL,
    barcode text NOT NULL
);

CREATE SEQUENCE userid_seq
    INCREMENT BY 1
    MAXVALUE 2147483647
    NO MINVALUE
    CACHE 1;

SET search_path = django, pg_catalog;

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);
ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_key UNIQUE (group_id, permission_id);
ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_message
    ADD CONSTRAINT auth_message_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_key UNIQUE (content_type_id, codename);
ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_key UNIQUE (user_id, group_id);
ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_key UNIQUE (user_id, permission_id);
ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);
ALTER TABLE ONLY cashout_cashcount
    ADD CONSTRAINT cashout_cashcount_pkey PRIMARY KEY (id);
ALTER TABLE ONLY cashout_cashout
    ADD CONSTRAINT cashout_cashout_pkey PRIMARY KEY (id);
ALTER TABLE ONLY cashout_entity
    ADD CONSTRAINT cashout_entity_pkey PRIMARY KEY (id);
ALTER TABLE ONLY cashout_transaction
    ADD CONSTRAINT cashout_transaction_pkey PRIMARY KEY (id);
ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);
ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_key UNIQUE (app_label, model);
ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);
ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);

SET search_path = public, pg_catalog;
ALTER TABLE ONLY bulk_items
    ADD CONSTRAINT bulk_items_pkey PRIMARY KEY (bulkid);
ALTER TABLE ONLY finance_accounts
    ADD CONSTRAINT finance_accounts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY finance_deposit_summary
    ADD CONSTRAINT finance_deposit_summary_pkey PRIMARY KEY (date);
ALTER TABLE ONLY finance_inventory_summary
    ADD CONSTRAINT finance_inventory_summary_pkey PRIMARY KEY (date);
ALTER TABLE ONLY finance_splits
    ADD CONSTRAINT finance_splits_pkey PRIMARY KEY (id);
ALTER TABLE ONLY finance_transactions
    ADD CONSTRAINT finance_transactions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY floor_locations
    ADD CONSTRAINT floor_locations_pkey PRIMARY KEY (id);
ALTER TABLE ONLY messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (msgid);
ALTER TABLE ONLY order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);
ALTER TABLE ONLY orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);
ALTER TABLE ONLY product_source
    ADD CONSTRAINT product_source_pkey PRIMARY KEY (sourceid);
ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (barcode);
ALTER TABLE ONLY transactions
    ADD CONSTRAINT transactions_id_key UNIQUE (id);
ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);

CREATE INDEX finance_splits_account_index ON finance_splits USING btree (account_id);
CREATE INDEX finance_splits_transaction_index ON finance_splits USING btree (transaction_id);
CREATE UNIQUE INDEX inventory_index ON inventory USING btree (date, bulkid);
CREATE INDEX profiles_index ON profiles USING btree (userid);
CREATE INDEX transactions_time_index ON transactions USING btree (xacttime);
CREATE INDEX transactions_user_index ON transactions USING btree (userid);
CREATE UNIQUE INDEX users_username_index ON users USING btree (username);

SET search_path = django, pg_catalog;
ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_fkey FOREIGN KEY (group_id) REFERENCES auth_group(id);
ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id);
ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id) REFERENCES auth_group(id);
ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);
ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id);
ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);
ALTER TABLE ONLY cashout_cashcount
    ADD CONSTRAINT cashout_cashcount_cashout_id_fkey FOREIGN KEY (cashout_id) REFERENCES cashout_cashout(id);
ALTER TABLE ONLY cashout_cashcount
    ADD CONSTRAINT cashout_cashcount_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES cashout_entity(id);
ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT content_type_id_referencing_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id);
ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT content_type_id_referencing_django_content_type_id_1 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id);
ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT user_id_referencing_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id);
ALTER TABLE ONLY auth_message
    ADD CONSTRAINT user_id_referencing_auth_user_id_1 FOREIGN KEY (user_id) REFERENCES auth_user(id);

SET search_path = public, pg_catalog;
ALTER TABLE ONLY products
    ADD CONSTRAINT "$1" FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid);
ALTER TABLE ONLY userbarcodes
    ADD CONSTRAINT barcode_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid);
ALTER TABLE ONLY bulk_items
    ADD CONSTRAINT bulk_items_floor_location_fkey FOREIGN KEY (floor_location) REFERENCES floor_locations(id);
ALTER TABLE ONLY transactions
    ADD CONSTRAINT finance_fk FOREIGN KEY (finance_trans_id) REFERENCES finance_transactions(id);
ALTER TABLE ONLY finance_splits
    ADD CONSTRAINT finance_splits_account_id_fkey FOREIGN KEY (account_id) REFERENCES finance_accounts(id);
ALTER TABLE ONLY finance_splits
    ADD CONSTRAINT finance_splits_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES finance_transactions(id);
ALTER TABLE ONLY historic_prices
    ADD CONSTRAINT historic_prices_bulkid_fkey FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid);
ALTER TABLE ONLY inventory
    ADD CONSTRAINT inventory2_bulkid_fkey FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid);
ALTER TABLE ONLY order_items
    ADD CONSTRAINT order_id_referencing_orders_id FOREIGN KEY (order_id) REFERENCES orders(id);
ALTER TABLE ONLY order_items
    ADD CONSTRAINT order_items_bulk_type_id_fkey FOREIGN KEY (bulk_type_id) REFERENCES bulk_items(bulkid);
