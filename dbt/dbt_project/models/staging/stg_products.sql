WITH source AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_products') }}
),
cleaned AS (
    SELECT
        CAST(product_id AS STRING) AS product_id,
        TRIM(CAST(category AS STRING)) AS category,
        TRIM(CAST(brand AS STRING)) AS brand,
        TRIM(CAST(description AS STRING)) AS description,
        CAST(price AS DECIMAL(10,2)) AS price,
        ingested_at AS raw_ingested_at,
        CURRENT_TIMESTAMP() AS processed_at
    FROM source
)
SELECT * FROM cleaned