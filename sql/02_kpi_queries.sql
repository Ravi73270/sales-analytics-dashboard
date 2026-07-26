-- Sales KPI Dashboard queries (PostgreSQL)

-- 1. Monthly revenue & profit trend
SELECT
    to_char(order_date, 'YYYY-MM') AS month,
    SUM(sales)  AS revenue,
    SUM(profit) AS profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS profit_margin_pct
FROM fact_sales
GROUP BY month
ORDER BY month;

-- 2. Month-over-month growth (window function: LAG)
WITH monthly AS (
    SELECT
        to_char(order_date, 'YYYY-MM') AS month,
        SUM(sales) AS revenue
    FROM fact_sales
    GROUP BY month
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
        / LAG(revenue) OVER (ORDER BY month), 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- 3. Year-over-year growth by month
WITH monthly AS (
    SELECT
        EXTRACT(YEAR FROM order_date)::INT AS yr,
        EXTRACT(MONTH FROM order_date)::INT AS mo,
        SUM(sales) AS revenue
    FROM fact_sales
    GROUP BY yr, mo
)
SELECT
    yr, mo, revenue,
    LAG(revenue) OVER (PARTITION BY mo ORDER BY yr) AS prev_year_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (PARTITION BY mo ORDER BY yr)) * 100.0
        / LAG(revenue) OVER (PARTITION BY mo ORDER BY yr), 2
    ) AS yoy_growth_pct
FROM monthly
ORDER BY mo, yr;

-- 4. Average Order Value (AOV) by month
SELECT
    to_char(order_date, 'YYYY-MM') AS month,
    ROUND(SUM(sales) * 1.0 / COUNT(DISTINCT order_id), 2) AS aov
FROM fact_sales
GROUP BY month
ORDER BY month;

-- 5. Running total of revenue (cumulative sum window function)
WITH monthly AS (
    SELECT to_char(order_date, 'YYYY-MM') AS month, SUM(sales) AS revenue
    FROM fact_sales GROUP BY month
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (ORDER BY month) AS cumulative_revenue
FROM monthly
ORDER BY month;

-- 6. Repeat purchase rate
WITH order_counts AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS n_orders
    FROM fact_sales
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repeat_rate_pct
FROM order_counts;

-- 7. Revenue & profit by region and segment
SELECT
    c.region,
    c.segment,
    SUM(f.sales) AS revenue,
    SUM(f.profit) AS profit,
    ROUND(SUM(f.profit) * 100.0 / SUM(f.sales), 2) AS margin_pct
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.region, c.segment
ORDER BY revenue DESC;

-- 8. Discount impact on margin
SELECT
    discount,
    COUNT(*) AS n_line_items,
    ROUND(AVG(profit), 2) AS avg_profit_per_line,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS margin_pct
FROM fact_sales
GROUP BY discount
ORDER BY discount;

-- 9. Top 10 customers by lifetime revenue
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    ROUND(SUM(f.sales), 2) AS lifetime_revenue,
    COUNT(DISTINCT f.order_id) AS n_orders
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment
ORDER BY lifetime_revenue DESC
LIMIT 10;

-- 10. Product performance: revenue rank within category
SELECT * FROM (
    SELECT
        p.category,
        p.product_name,
        SUM(f.sales) AS revenue,
        RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.sales) DESC) AS rank_in_category
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY p.category, p.product_name
) ranked
WHERE rank_in_category <= 5
ORDER BY category, rank_in_category;
