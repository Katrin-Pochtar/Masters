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

alter table transaction
alter column transaction_date type date
	using to_date(transaction_date,
'DD.MM.YYYY');


-- Вывести распределение (количество) клиентов по сферам деятельности, отсортировав результат по убыванию количества
select
	job_industry_category,
	COUNT(customer_id) as customer_count
from
	customer
group by
	job_industry_category
order by
	customer_count desc;

	
-- Найти сумму транзакций за каждый месяц по сферам деятельности, отсортировав по месяцам и по сфере деятельности
	
select
	date_part('month',
	transaction_date) as transaction_month,
	customer.job_industry_category,
	SUM(list_price) as total_transaction
from
	transaction
inner join 
    customer on
	transaction.customer_id = customer.customer_id
group by
	transaction_month,
	customer.job_industry_category
order by
	transaction_month,
	customer.job_industry_category;



-- Вывести количество онлайн-заказов для всех брендов в рамках подтвержденных заказов клиентов из сферы IT.

select
    t.brand,
    count(*) as online_order_count
from
    transaction t
inner join customer c on t.customer_id = c.customer_id
where
    t.order_status = 'Approved'
    and t.online_order = 'True'
    and c.job_industry_category = 'IT'
group by
    t.brand;

-- Найти по всем клиентам сумму всех транзакций (list_price), максимум, минимум и количество транзакций, отсортировав результат по убыванию суммы транзакций и количества клиентов. Выполните двумя способами: используя только group by и используя только оконные функции. Сравните результат.
	
	
select
	customer_id,
	SUM(list_price) as total_sum,
	MAX(list_price) as max_price,
	MIN(list_price) as min_price,
	COUNT(*) as transaction_count
from
	transaction
group by
	customer_id
order by
	total_sum desc,
	transaction_count desc;

select
	customer_id,
	total_sum,
	max_price,
	min_price,
	transaction_count
from
	(
	select
		customer_id,
		SUM(list_price) over (partition by customer_id) as total_sum,
		MAX(list_price) over (partition by customer_id) as max_price,
		MIN(list_price) over (partition by customer_id) as min_price,
		COUNT(*) over (partition by customer_id) as transaction_count,
		row_number() over (partition by customer_id
	order by
		transaction_id) as rn
	from
		transaction
) sub
where
	rn = 1
order by
	total_sum desc,
	transaction_count desc;

-- Найти имена и фамилии клиентов с минимальной/максимальной суммой транзакций за весь период (сумма транзакций не может быть null). Напишите отдельные запросы для минимальной и максимальной суммы.

select
	c.first_name,
	c.last_name,
	t.total_sum
from
	(
	select
		customer_id,
		SUM(list_price) as total_sum
	from
		transaction
	where
		list_price is not null
	group by
		customer_id
) t
join customer c on
	t.customer_id = c.customer_id
where
	t.total_sum = (
	select
		MIN(total_sum)
	from
		(
		select
			customer_id,
			SUM(list_price) as total_sum
		from
			transaction
		where
			list_price is not null
		group by
			customer_id
    ) s
);


select
	c.first_name,
	c.last_name,
	t.total_sum
from
	(
	select
		customer_id,
		SUM(list_price) as total_sum
	from
		transaction
	where
		list_price is not null
	group by
		customer_id
) t
join customer c on
	t.customer_id = c.customer_id
where
	t.total_sum = (
	select
		MAX(total_sum)
	from
		(
		select
			customer_id,
			SUM(list_price) as total_sum
		from
			transaction
		where
			list_price is not null
		group by
			customer_id
    ) s
);


-- Вывести только самые первые транзакции клиентов. Решить с помощью оконных функций.

select
	*
from
	(
	select
		t.*,
		row_number() over (partition by customer_id
	order by
		transaction_date) as rn
	from
		transaction t
) sub
where
	rn = 1;




-- Вывести имена, фамилии и профессии клиентов, между транзакциями которых был максимальный интервал (интервал вычисляется в днях)

with client_intervals as (
select
	customer_id,
	transaction_date - lag(transaction_date) over (partition by customer_id
order by
	transaction_date) as gap
from
	transaction
),
client_max_gap as (
select
	customer_id,
	MAX(gap) as max_gap
from
	client_intervals
where
	gap is not null
group by
	customer_id
),
overall_max as (
select
	MAX(max_gap) as overall_max_gap
from
	client_max_gap
)
select
	c.first_name,
	c.last_name,
	c.job_title,
	cmg.max_gap as max_interval_in_days
from
	customer c
join client_max_gap cmg on
	c.customer_id = cmg.customer_id
join overall_max om on
	cmg.max_gap = om.overall_max_gap;


