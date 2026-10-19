{{ config(
    materialized='table'
) }}

WITH sales AS (
    -- Reutilizamos el stg_sales que creamos en el paso anterior
    SELECT * FROM {{ ref('stg_sales') }}
),
customers AS (
    SELECT customer_id FROM {{ ref('stg_customers') }}
),
products AS (
    SELECT product_id FROM {{ ref('stg_products') }}
)

SELECT 
    s.*
FROM sales s
-- Forzamos integridad referencial cruzada (Maestros válidos)
INNER JOIN customers c ON s.customer_id = c.customer_id
INNER JOIN products p ON s.product_id = p.product_id
