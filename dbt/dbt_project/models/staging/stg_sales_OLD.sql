{{ config(
    materialized='table'
) }}

WITH source_data AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_sales') }}
)

SELECT
    CAST(sale_id AS STRING) AS sale_id,
    CAST(customer_id AS STRING) AS customer_id,
    CAST(product_id AS STRING) AS product_id,
    CAST(timestamp AS TIMESTAMP) AS order_timestamp,
    CAST(quantity AS INT) AS quantity,
    CAST(unit_price AS DECIMAL(10, 2)) AS unit_price,
    CAST(quantity * unit_price AS DECIMAL(10, 2)) AS total_line,
    ingested_at AS raw_ingested_at,
    CURRENT_TIMESTAMP() AS processed_at
FROM source_data