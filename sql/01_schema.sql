-- Star schema for the Sales Analytics Dashboard.
-- Written for PostgreSQL. Run this against your local Postgres instance
-- (you already have PostgreSQL set up from your other projects).

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;

CREATE TABLE dim_customer (
    customer_id   VARCHAR(15) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    segment       VARCHAR(30),
    region        VARCHAR(30),
    state         VARCHAR(50),
    signup_date   DATE
);

CREATE TABLE dim_product (
    product_id    VARCHAR(15) PRIMARY KEY,
    product_name  VARCHAR(150) NOT NULL,
    category      VARCHAR(50),
    sub_category  VARCHAR(50),
    unit_cost     NUMERIC(10,2),
    unit_price    NUMERIC(10,2)
);

CREATE TABLE fact_sales (
    order_id     VARCHAR(15),
    order_date   DATE NOT NULL,
    ship_date    DATE,
    customer_id  VARCHAR(15) REFERENCES dim_customer(customer_id),
    product_id   VARCHAR(15) REFERENCES dim_product(product_id),
    quantity     INT,
    discount     NUMERIC(4,2),
    sales        NUMERIC(12,2),
    cost         NUMERIC(12,2),
    profit       NUMERIC(12,2),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_fact_sales_date ON fact_sales(order_date);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);

-- Load data (run from psql with \copy, since COPY needs server-side access
-- and \copy reads from your local client machine instead):
-- \copy dim_customer FROM 'data/customers.csv' DELIMITER ',' CSV HEADER;
-- \copy dim_product  FROM 'data/products.csv'  DELIMITER ',' CSV HEADER;
-- \copy fact_sales    FROM 'data/orders.csv'    DELIMITER ',' CSV HEADER;
