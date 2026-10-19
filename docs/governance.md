# Modelo de Gobierno y Control de Calidad de Datos

Este documento describe las políticas implementadas para garantizar la completitud, validez, unicidad e integridad referencial dentro de nuestra arquitectura Medallion.

## 1. Control de Calidad en Ingesta (Filtro Técnico)
*   **Mecanismo:** Validación condicional nativa en PySpark ejecutada por Azure Data Factory.
*   **Regla Bloqueante:** Si un registro de ventas no cuenta con un `sale_id` válido, o si la columna `quantity` es menor o igual a cero, la fila completa es catalogada como corrupta y aislada de forma inmediata a la zona de cuarentena. El pipeline continúa procesando los registros sanos de forma segura (Aislamiento Batch).

## 2. Matriz de Pruebas de Calidad dbt Core (Auditoría Analítica)
Las pruebas automáticas integradas en el archivo `schema.yml` ejecutan consultas SQL de control cada vez que el pipeline corre, garantizando el éxito del negocio:

1.  **Prueba de Unicidad (`unique`):** Monitorea la columna `sale_id` en `stg_sales`. Si dbt detecta claves duplicadas, arroja una alerta de fallo. En nuestra arquitectura, esta regla de calidad se resolvió de forma proactiva aplicando una ventana analítica avanzada de deduplicación (`ROW_NUMBER() OVER PARTITION BY sale_id ORDER BY ingested_at DESC`) para limpiar la data en Silver.
2.  **Prueba de Completitud (`not_null`):** Aplicada estrictamente sobre las claves primarias y foráneas (`sale_id`, `customer_id`, `product_id`). Certifica que no existan registros vacíos o huérfanos que rompan las uniones lógicas.
3.  **Prueba de Integridad Referencial (`relationships`):** Ejecutada sobre la capa de validación intermedia. Asegura de forma matemática que el 100% de los identificadores de cliente y producto transaccionados en ventas existan de forma real dentro de las tablas maestras de Clientes y Productos de la empresa.

## 3. Evidencia de Éxito y Gestión de Fallas
*   **Trazabilidad local:** dbt compila y almacena las consultas de auditoría en formato estructurado dentro de la carpeta `target/`.
*   **Persistencia de Fallas:** Al ejecutar el comando con el parámetro `--store-failures`, dbt genera automáticamente tablas físicas de auditoría de errores (como `ecommerce_silver.unique_stg_sales_sale_id`) dentro del Unity Catalog. Esto permite que el equipo de gobierno de datos examine directamente las filas corruptas, manteniendo una bitácora histórica transparente de la degradación de calidad de la fuente.