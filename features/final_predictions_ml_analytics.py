from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, udf, round, row_number, lit
from pyspark.sql.window import Window
from pyspark.ml.functions import vector_to_array

###spark = SparkSession.builder.appName("EcomMLAnalyticsFix").getOrCreate()

# Variables para Unity Catalog
catalog_name = "catalog_prueba_adls"
schema_name  = "ecommerce_gold"

print("Cargando y preparando los conjuntos de datos...")
# 1. Leer las tablas existentes
df_predictions_tecnica = spark.table(f"{catalog_name}.{schema_name}.final_predictions_ml")
df_gold_original = spark.table(f"{catalog_name}.{schema_name}.customer_360")

# =====================================================================
# PASO CRÍTICO: REPLICAR EL SPLIT PARA ASOCIAR LOS IDs REALES
# =====================================================================
# Replicamos exactamente la misma división del 20% con la semilla 42 
# para aislar las mismas 74 filas de validación con sus IDs intactos
_, df_test_con_ids = df_gold_original.randomSplit([0.8, 0.2], seed=42)

# Añadimos un índice por número de fila a ambos DataFrames para poder hacer el join
window_spec = Window.orderBy(lit(1))
df_pred_indexed = df_predictions_tecnica.withColumn("row_idx", row_number().over(window_spec))
df_ids_indexed = df_test_con_ids.withColumn("row_idx", row_number().over(window_spec))

# Unimos ambas tablas temporalmente usando el índice secuencial corregido
df_joined_raw = df_pred_indexed.join(df_ids_indexed, on="row_idx", how="inner")

# =====================================================================
# TRANSFORMACIÓN Y TRADUCCIÓN DE VECTORES
# =====================================================================
print("Traduciendo vectores y limpiando columnas de negocio...")

# Convertimos el vector nativo de probabilidad en un Array común de Spark
df_with_array = df_joined_raw.withColumn("prob_array", vector_to_array("probability"))

# Extraemos el índice 1 (Probabilidad de ser VIP) y lo convertimos a porcentaje limpio
df_friendly = df_with_array.withColumn(
    "score_certeza_vip_porcentaje", 
    round(col("prob_array")[1] * 100, 2)
)

# Mapeamos la predicción numérica (0.0 o 1.0) a un texto entendible por el negocio
df_friendly = df_friendly.withColumn(
    "segmento_predicho",
    udf(lambda p: "Cliente VIP (Alto Valor)" if p == 1.0 else "Cliente Regular / En Riesgo")("prediction")
)

# Seleccionamos las columnas finales limpias para el reporte de BI
df_final_analytics = df_friendly.select(
    col("customer_id").alias("ID_Cliente"),
    col("city").alias("Ciudad"),
    col("segment").alias("Segmento_Original"),
    col("frequency").alias("Compras_Realizadas"),
    col("monetary_value").alias("Monto_Total_Gastado"),
    col("average_ticket").alias("Ticket_Promedio"),
    col("days_since_last_purchase").alias("Dias_Desde_Ultima_Compra"),
    col("segmento_predicho").alias("Prediccion_IA"),
    col("score_certeza_vip_porcentaje").alias("Certeza_Prediccion_Porcentaje"),
    current_timestamp().alias("Fecha_Ejecucion_Pipeline")
)

# 2. Guardamos nueva tabla analítica de consumo
new_table_name = "final_predictions_ml_analytics"
df_final_analytics.write.mode("overwrite").format("delta") \
    .saveAsTable(f"{catalog_name}.{schema_name}.{new_table_name}")

print(f"Tabla de negocio se creó correctamente en: {catalog_name}.{schema_name}.{new_table_name}")
