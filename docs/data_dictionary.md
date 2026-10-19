# Diccionario de Datos del E-Commerce (Esquemas Delta de Unity Catalog)

## 1. Esquema: `catalog_prueba_adls.ecommerce_raw`

### Tabla: `raw_sales`
*   **sale_id** (STRING): Identificador único atómico de la transacción. (Llave Primaria).
*   **customer_id** (STRING): Código único del cliente comprador. (Llave Foránea).
*   **product_id** (STRING): Código único del producto adquirido. (Llave Foránea).
*   **timestamp** (TIMESTAMP): Fecha y hora exacta de la compra en la plataforma.
*   **quantity** (INTEGER): Cantidad total de artículos transaccionados.
*   **unit_price** (DECIMAL): Precio unitario de catálogo del artículo vendido.
*   **ingested_at** (TIMESTAMP): Marca de tiempo del sistema al ingresar a la zona RAW.

---

## 2. Esquema: `catalog_prueba_adls.ecommerce_silver`

### Tabla: `stg_sales`
*   *Hereda las columnas de `raw_sales` aplicando limpieza y tipificación explícita de datos.*
*   **sale_id** (STRING): Identificador único atómico de la transacción. (Llave Primaria).
*   **customer_id** (STRING): Código único del cliente comprador. (Llave Foránea).
*   **product_id** (STRING): Código único del producto adquirido. (Llave Foránea).
*   **timestamp** (TIMESTAMP): Fecha y hora exacta de la compra en la plataforma.
*   **quantity** (INTEGER): Cantidad total de artículos transaccionados.
*   **unit_price** (DECIMAL): Precio unitario de catálogo del artículo vendido.
*   **total_line** (DECIMAL): Campo calculado de negocio (`quantity` × `unit_price`).
*   **raw_ingested_at** (TIMESTAMP): Marca de tiempo del sistema al ingresar a la zona RAW.
*   **processed_at** (TIMESTAMP): Fecha fija de proceso de carga de dbt.

### Tabla: `int_sales_validated`
*   *Mantiene el esquema estructurado de ventas, conteniendo únicamente los registros que superaron con éxito el filtro de integridad referencial cruzada (INNER JOIN de llaves foráneas existentes contra clientes y productos).*
*   **sale_id** (STRING): Identificador único atómico de la transacción.
*   **customer_id** (STRING): Código único del cliente comprador.
*   **product_id** (STRING): Código único del producto adquirido.
*   **timestamp** (TIMESTAMP): Fecha y hora exacta de la compra en la plataforma.
*   **quantity** (INTEGER): Cantidad total de artículos transaccionados.
*   **unit_price** (DECIMAL): Precio unitario de catálogo del artículo vendido.
*   **total_line** (DECIMAL): Campo calculado de negocio (`quantity` × `unit_price`).
*   **raw_ingested_at** (TIMESTAMP): Marca de tiempo del sistema al ingresar a la zona RAW.
*   **processed_at** (TIMESTAMP): Fecha fija de proceso de carga de dbt.

---

## 3. Esquema: `catalog_prueba_adls.ecommerce_gold`

### Tabla: `customer_360` (Feature Store Analítico)
*   **customer_id** (STRING): Código identificador único del cliente.
*   **city** (STRING): Ciudad de residencia del usuario.
*   **segment** (STRING): Segmento corporativo o de consumo del cliente.
*   **customer_tenure_days** (INTEGER): Antigüedad en días desde su registro hasta la corrida.
*   **frequency** (INTEGER): Cantidad total de órdenes distintas ejecutadas en la historia.
*   **monetary_value** (DECIMAL): Gasto total acumulado del usuario en la plataforma.
*   **average_ticket** (DECIMAL): Valor promedio de compra por transacción.
*   **total_products** (INTEGER): Volumen de unidades físicas adquiridas.
*   **days_since_last_purchase** (INTEGER): Métrica de *Recency/Frescura*. Días transcurridos desde su última orden.
*   **purchase_frequency_30d** (INTEGER): Cantidad de órdenes generadas en los últimos 30 días.
*   **purchase_frequency_90d** (INTEGER): Cantidad de órdenes generadas en los últimos 90 días.
*   **preferred_category** (STRING): Categoría de catálogo favorita basada en volumen de compra.
*   **is_high_value_customer** (INTEGER): Variable objetivo (Target ML). 1 si el cliente es VIP, 0 si no.
*   **gold_updated_at** (TIMESTAMP): Marca de tiempo del sistema.

### Tabla: `final_predictions_ml_analytics` (Tabla de Consumo Gerencial)
*   **ID_Cliente** (STRING): Código único del usuario evaluado.
*   **Ciudad** (STRING) / **Segmento_Original** (STRING): Datos demográficos descriptivos.
*   **Compras_Realizadas** (INTEGER) / **Monto_Total_Gastado** (DECIMAL): Resumen de comportamiento.
*   **Ticket_Promedio** (DECIMAL): Valor promedio de compra por transacción. 
*   **Dias_Desde_Ultima_Compra** (INTEGER): Métrica de *Recency/Frescura*. Días transcurridos desde su última orden. 
*   **Prediccion_IA** (STRING): Clasificación ejecutada por el modelo predictivo (`Cliente VIP` o `Cliente Regular / En Riesgo`).
*   **Certeza_Prediccion_Porcentaje** (DOUBLE): Score probabilístico del modelo formateado para analistas de negocio (ej. `96.57%`).
*   **Fecha_Ejecucion_Pipeline** (TIMESTAMP): Auditoría temporal de la corrida analítica predictiva.