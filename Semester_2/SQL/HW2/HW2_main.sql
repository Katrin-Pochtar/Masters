CREATE TABLE customer(
    customer_id int4,
    first_name varchar(50),
    last_name varchar(50),
    gender varchar(30),
    dob varchar(50),
    job_title varchar(50),
    job_industry_category varchar(50),
    wealth_segment varchar(50),
    deceased_indicator varchar(50),
    owns_car varchar(30),
    address varchar(50),
    postcode varchar(30),
    state varchar(30),
    country varchar(30),
    property_valuation int4
);

CREATE TABLE transaction(
    transaction_id int4,
    product_id int4,
    customer_id int4,
    transaction_date varchar(30),
    online_order varchar(30),
    order_status varchar(30),
    brand varchar(30),
    product_line varchar(30),
    product_class varchar(30),
    product_size varchar(30),
    list_price float4,
    standard_cost float4
);

-- Вывести все уникальные бренды, у которых стандартная стоимость выше 1500 долларов.
select
	distinct brand
from
	transaction
where
  standard_cost > 1500


 -- Вывести все подтвержденные транзакции за период '2017-04-01' по '2017-04-09' включительно.
select
	*
from
	transaction
where
	order_status = 'Approved'
	and to_date(transaction_date,
	'DD.MM.YYYY') between '2017-04-01'
  and '2017-04-09'
  
-- Вывести все профессии у клиентов из сферы IT или Financial Services, которые начинаются с фразы 'Senior'.
select
	distinct job_title
from
	customer
where
	(job_industry_category = 'Financial Services'
		or job_industry_category = 'IT')
	and job_title like 'Senior%'
	
-- Вывести все бренды, которые закупают клиенты, работающие в сфере Financial Services
select
	distinct brand
from
	transaction
inner join customer
on
	transaction.customer_id = customer.customer_id
where
	job_industry_category = 'Financial Services'
	
-- Вывести 10 клиентов, которые оформили онлайн-заказ продукции из брендов 'Giant Bicycles', 'Norco Bicycles', 'Trek Bicycles'.

select
	distinct c.customer_id,
	c.first_name,
	c.last_name
from
	transaction t
inner join customer c on
	t.customer_id = c.customer_id
where
	t.online_order = 'True'
	and t.brand in ('Giant Bicycles', 'Norco Bicycles', 'Trek Bicycles')
limit 10;

	
-- Вывести всех клиентов, у которых нет транзакций.
select
	distinct c.customer_id,
	c.first_name,
	c.last_name
from
	customer c
left join transaction t on
	c.customer_id = t.customer_id
where
	t.transaction_id is null;


-- Вывести всех клиентов из IT, у которых транзакции с максимальной стандартной стоимостью.
select
	distinct c.customer_id,
	c.first_name,
	c.last_name
from
	customer c
join transaction t on
	c.customer_id = t.customer_id
where
	c.job_industry_category = 'IT'
	and t.standard_cost = (
	select
		MAX(standard_cost)
	from
		transaction);


	
-- Вывести всех клиентов из сферы IT и Health, у которых есть подтвержденные транзакции за период '2017-07-07' по '2017-07-17'.
select
	distinct c.customer_id,
	c.first_name,
	c.last_name
from
	customer c
join transaction t on
	c.customer_id = t.customer_id
where
	c.job_industry_category in ('IT', 'Health')
	and t.order_status = 'Approved'
	and to_date(t.transaction_date,
	'DD.MM.YYYY') between '2017-07-07' and '2017-07-17';
