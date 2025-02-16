CREATE TABLE customer (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender VARCHAR(10),
    dob DATE,
    job_title VARCHAR(100),
    job_industry_category VARCHAR(100),
    wealth_segment VARCHAR(50),
    deceased_indicator CHAR(1),
    owns_car VARCHAR(10),
    address VARCHAR(200),
    postcode INT,
    state VARCHAR(50),
    country VARCHAR(50),
    property_valuation INT
);


CREATE TABLE product (
    custom_product_id VARCHAR(100) PRIMARY KEY,
    product_id INT,                       
    brand VARCHAR(100) NOT NULL,
    product_line VARCHAR(50),
    product_class VARCHAR(50),
    product_size VARCHAR(50),
    list_price NUMERIC(10,2),
    standard_cost NUMERIC(10,2)
);


CREATE TABLE transaction (
    transaction_id INT PRIMARY KEY,
    custom_product_id VARCHAR(100) NOT NULL,
    customer_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    online_order VARCHAR(10),
    order_status VARCHAR(50)
);