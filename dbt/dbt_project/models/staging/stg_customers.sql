WITH source AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_customers') }}
),
cleaned AS (
    SELECT
        CAST(customer_id AS STRING) AS customer_id,
        CAST(signup_date AS DATE) AS signup_date,
        TRIM(CAST(city AS STRING)) AS city,
        TRIM(CAST(segment AS STRING)) AS segment,
        ingested_at AS raw_ingested_at,
        CURRENT_TIMESTAMP() AS processed_at
    FROM source
)
SELECT * FROM cleaned