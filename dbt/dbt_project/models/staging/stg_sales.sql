{{ config(
    materialized='table'
) }}

WITH source_data AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_sales') }}
),

numbered_sales AS (
    SELECT
        CAST(sale_id AS STRING) AS sale_id,
        CAST(customer_id AS STRING) AS customer_id,
        CAST(product_id AS STRING) AS product_id,
        CAST(timestamp AS TIMESTAMP) AS order_timestamp,
        CAST(quantity AS INT) AS quantity,
        CAST(unit_price AS DECIMAL(10, 2)) AS unit_price,
        CAST(quantity * unit_price AS DECIMAL(10, 2)) AS total_line,
        ingested_at AS raw_ingested_at,
        CURRENT_TIMESTAMP() AS processed_at,
        -- funcion de ventana para capturar duplicados
        ROW_NUMBER() OVER (
            PARTITION BY sale_id 
            ORDER BY ingested_at DESC, timestamp DESC
        ) AS row_num
    FROM source_data
)

-- Eliminamos duplicados (el primero de la ventana)
SELECT
    sale_id,
    customer_id,
    product_id,
    order_timestamp,
    quantity,
    unit_price,
    total_line,
    raw_ingested_at,
    processed_at
FROM numbered_sales
WHERE row_num = 1