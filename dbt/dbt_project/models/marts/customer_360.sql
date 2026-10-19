{{ config(
    materialized='table',
    schema='ecommerce_gold'
) }}

WITH sales_validated AS (
    SELECT * FROM {{ ref('int_sales_validated') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

customer_metrics AS (
    SELECT
        customer_id,
        -- 1. Métricas Base (RFM)
        COUNT(DISTINCT sale_id) AS frequency,
        SUM(total_line) AS monetary_value,
        AVG(total_line) AS average_ticket,
        SUM(quantity) AS total_products_purchased,
        COUNT(DISTINCT product_id) AS number_of_distinct_products,
        
        -- 2. Recency (Días desde la última compra basándonos en el día de la corrida: 2026-03-01)
        MAX(order_timestamp) AS last_purchase_timestamp,
        DATEDIFF(CAST('2026-03-01' AS DATE), CAST(MAX(order_timestamp) AS DATE)) AS days_since_last_purchase,
        
        -- 3. Frecuencias temporales acotadas
        COUNT(DISTINCT CASE WHEN order_timestamp >= CAST('2026-02-01' AS DATE) THEN sale_id END) AS purchase_frequency_30d,
        COUNT(DISTINCT CASE WHEN order_timestamp >= CAST('2026-01-01' AS DATE) THEN sale_id END) AS purchase_frequency_90d
    FROM sales_validated
    GROUP BY 1
),

preferred_category_calc AS (
    -- Calculamos la categoría favorita de cada cliente (la que tiene más cantidad comprada)
    SELECT customer_id, category AS preferred_category FROM (
        SELECT 
            s.customer_id,
            p.category,
            SUM(s.quantity) as total_qty,
            ROW_NUMBER() OVER (PARTITION BY s.customer_id ORDER BY SUM(s.quantity) DESC) as rn
        FROM sales_validated s
        INNER JOIN {{ ref('stg_products') }} p ON s.product_id = p.product_id
        GROUP BY 1, 2
    ) WHERE rn = 1
)

SELECT
    c.customer_id,
    c.city,
    c.segment,
    -- 4. Antigüedad del cliente en meses (Customer Tenure) desde su registro hasta la corrida
    DATEDIFF(CAST('2026-03-01' AS DATE), c.signup_date) AS customer_tenure_days,
    
    -- Unimos las variables calculadas controlando los nulos para clientes nuevos sin compras
    COALESCE(m.frequency, 0) AS frequency,
    COALESCE(m.monetary_value, 0.0) AS monetary_value,
    COALESCE(m.average_ticket, 0.0) AS average_ticket,
    COALESCE(m.total_products_purchased, 0) AS total_products,
    COALESCE(m.days_since_last_purchase, 999) AS days_since_last_purchase, -- 999 significa que nunca compró
    COALESCE(m.purchase_frequency_30d, 0) AS purchase_frequency_30d,
    COALESCE(m.purchase_frequency_90d, 0) AS purchase_frequency_90d,
    COALESCE(pc.preferred_category, 'No Purchase') AS preferred_category,
    
    -- VARIABLE OBJETIVO (Target para el Modelo ML de Clasificación): 
    -- 1 si el cliente es de "Alto Valor" (gastó más de 1,500 USD o compra seguido), 0 si no.
    CASE WHEN m.monetary_value > 1500.0 OR m.frequency >= 5 THEN 1 ELSE 0 END AS is_high_value_customer,
    CURRENT_TIMESTAMP() AS gold_updated_at
FROM customers c
LEFT JOIN customer_metrics m ON c.customer_id = m.customer_id
LEFT JOIN preferred_category_calc pc ON c.customer_id = pc.customer_id
