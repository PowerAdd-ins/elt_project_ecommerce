{{ config(
    materialized='table',
    schema='ecommerce_gold'
) }}

WITH sales_validated AS (
    SELECT * FROM {{ ref('int_sales_validated') }}
),
customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
)

SELECT
    c.customer_id,
    c.city,
    c.segment,
    c.signup_date,
    -- Características calculadas requeridas para el análisis y ML (Features)
    COUNT(DISTINCT s.sale_id) AS total_orders,
    SUM(s.quantity) AS total_items_purchased,
    SUM(s.total_line) AS total_spend,
    AVG(s.total_line) AS avg_order_value,
    MAX(s.order_timestamp) AS last_purchase_timestamp,
    CURRENT_TIMESTAMP() AS gold_updated_at
FROM customers c
LEFT JOIN sales_validated s ON c.customer_id = s.customer_id
GROUP BY 1, 2, 3, 4
