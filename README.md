# E-Commerce Data Pipeline & Predictive Analytics System

Este repositorio contiene una solución empresarial **End-to-End** de Ingeniería de Datos y Machine Learning construida sobre la arquitectura **Lakehouse (Medallion)** en **Azure Databricks**, orquestada de forma batch por **Azure Data Factory (ADF)** y transformada analíticamente mediante **dbt Core**.

---

## 🗺️ Arquitectura de la Solución (Data & MLOps Pipeline)

El flujo de datos se procesa de forma robusta a través de las siguientes etapas:

[ ADLS Gen2: fuentes/ ] ──( ADF Copy )──> [ ADLS Gen2: raw/temp/ ]
│
(ADF Pipeline Trigger)
▼
[ Ingestion: PySpark Notebook ]
│
┌──────────────────────────────┴──────────────────────────────┐
▼ (Filtro de Calidad Bloqueante)                             ▼ (Registros Inválidos)
[ ecommerce_raw.raw_sales ]                                    [ ecommerce_raw.quarantine_sales ]
│
( dbt compile & run )
▼
[ ecommerce_silver.stg_sales ] (Deduplicación ROW_NUMBER)
[ ecommerce_silver.stg_customers ] (Table)
[ ecommerce_silver.stg_products ] (Table)
│
( dbt Integrity Test )
▼
[ ecommerce_silver.int_sales_validated ] (Inner Join / Limpieza)
│
( dbt Gold Promotion )
▼
[ ecommerce_gold.customer_360 ] (Feature Store Analítico)
│
( Spark ML Model Run )
▼
[ ecommerce_gold.final_predictions_ml ] ──> [ ecommerce_gold.final_predictions_ml_analytics ]
│
( Power BI / BI Ready )

## 🛠️ Tecnologías Elegidas & Justificación

*   **Azure Data Factory (ADF):** Elegido para la automatización e ingesta controlada de archivos planos hacia zonas seguras de aterrizaje por lotes (*Batch*).
*   **Azure Data Lake Storage (ADLS Gen2):** Sistema de almacenamiento jerárquico de alta disponibilidad para alojar las carpetas físicas externas de las capas Medallion.
*   **Azure Databricks (Single Node Cluster):** Motor de cómputo Spark optimizado para ejecutar cargas de trabajo pesadas de ingesta y modelado analítico a un costo eficiente.
*   **Unity Catalog:** Herramienta centralizada de gobernanza de Azure Databricks utilizada para la gestión de accesos, auditoría de linaje y aislamiento estricto de esquemas.
*   **dbt Core (v1.12):** El cerebro de transformación ELT que abstrae la complejidad de los scripts DDL tradicionales y automatiza las pruebas de calidad de datos mediante SQL modular.
*   **MLflow & Spark ML:** Frameworks utilizados para entrenar modelos predictivos estables y registrar la trazabilidad absoluta del experimento (parámetros, métricas y firmas del modelo).

---

## 🚀 Guía de Despliegue y Ejecución

### 1. Ingesta Inicial con Azure Data Factory
1. ADF monitorea la ruta de origen en el storage.
2. Mediante una actividad de **Copy Data**, ADF extrae los archivos planos diarios y los deposita en la ruta de aterrizaje temporal: `abfss://proyecto1@<storage_account>.dfs.core.windows.net/raw/temp/`.
3. Posteriormente, ADF ejecuta una actividad de tipo **Databricks Notebook** para disparar el script `ingestion/ingest_and_quarantine.py`.

### 2. Procesamiento y Transformación Analítica con dbt Core
Desde la terminal local (dentro del directorio `project/dbt/dbt_project`), ejecuta los siguientes comandos para compilar, transformar y auditar las capas Silver y Gold en Unity Catalog:

```bash
# Limpiar compilaciones anteriores
dbt clean

# Ejecutar transformaciones en orden de linaje de dependencias
dbt run

# Ejecutar auditoría automatizada de las 6 reglas de calidad de datos
dbt test
```

### 3. Modelado Predictivo e Inteligencia de Negocio
Ejecutar el script `ml/train_model.py` en entorno de Databricks para consumir el Mart analítico, entrenar el clasificador e inyectar los resultados limpios traducidos para el usuario final en la tabla definitiva de negocio: `ecommerce_gold.final_predictions_ml_analytics`.

