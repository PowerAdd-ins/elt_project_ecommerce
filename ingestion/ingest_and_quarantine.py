# Databricks notebook source
# ingestion/ingest_and_quarantine.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

spark = SparkSession.builder.appName("EcomExternalIngestion").getOrCreate()

# =====================================================================
# CONFIGURACIÓN DE PATH EN ADLS
# =====================================================================
STORAGE_ACCOUNT = "saelv001"
BASE_URL = f"abfss://proyecto1@{STORAGE_ACCOUNT}.dfs.core.windows.net"

# Rutas de Lectura (Archivos fuente en carpeta temp)
sales_src    = f"{BASE_URL}/raw/temp/sales.csv"
customers_src = f"{BASE_URL}/raw/temp/customers.csv"
products_src  = f"{BASE_URL}/raw/temp/products.csv"

# Path para el table location
path_raw_sales        = f"{BASE_URL}/raw/data/raw_sales"
path_quarantine_sales = f"{BASE_URL}/raw/data/quarantine_sales"
path_raw_customers    = f"{BASE_URL}/raw/data/raw_customers"
path_raw_products     = f"{BASE_URL}/raw/data/raw_products"

# Variables para Unity Catalog
catalog_name = "catalog_prueba_adls"
schema_name  = "ecommerce_raw"

print("Leyendo archivos CSV crudos de ADLS Gen2...")
df_sales_raw     = spark.read.option("header", "true").option("inferSchema", "true").csv(sales_src)
df_customers_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(customers_src)
df_products_raw  = spark.read.option("header", "true").option("inferSchema", "true").csv(products_src)

# Trazabilidad / Campo tecnico de fecha de ingesta
df_sales_raw     = df_sales_raw.withColumn("ingested_at", current_timestamp())
df_customers_raw = df_customers_raw.withColumn("ingested_at", current_timestamp())
df_products_raw  = df_products_raw.withColumn("ingested_at", current_timestamp())

# =====================================================================
# REGLA DE CALIDAD OBLIGATORIA (BLOQUEANTE - CUARENTENA)
# =====================================================================
condicion_valida = (
    col("sale_id").isNotNull() & (col("sale_id") != "") & 
    col("quantity").isNotNull() & (col("quantity") > 0) & 
    col("unit_price").isNotNull() & (col("unit_price") >= 0)
)

df_sales_validos    = df_sales_raw.filter(condicion_valida)
df_sales_cuarentena = df_sales_raw.filter(~condicion_valida)

# =====================================================================
# ESCRITURA COMO TABLAS EXTERNAS
# =====================================================================
print("Escribiendo tablas externas en Unity Catalog...")

# Guardar Ventas Válidas externas
df_sales_validos.write.mode("overwrite").format("delta") \
    .option("path", path_raw_sales) \
    .saveAsTable(f"{catalog_name}.{schema_name}.raw_sales")

# Guardar Ventas Corruptas externas (Cuarentena)
df_sales_cuarentena.write.mode("overwrite").format("delta") \
    .option("path", path_quarantine_sales) \
    .saveAsTable(f"{catalog_name}.{schema_name}.quarantine_sales")

# Guardar Clientes Maestros externos
df_customers_raw.write.mode("overwrite").format("delta") \
    .option("path", path_raw_customers) \
    .saveAsTable(f"{catalog_name}.{schema_name}.raw_customers")

# Guardar Productos externos
df_products_raw.write.mode("overwrite").format("delta") \
    .option("path", path_raw_products) \
    .saveAsTable(f"{catalog_name}.{schema_name}.raw_products")

print("¡Tablas Externas RAW registradas con éxito en el storage!")
