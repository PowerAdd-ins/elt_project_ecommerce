# ml/train_model.py

import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql.functions import current_timestamp, lit

# 1. INICIALIZAR ENTORNO Y TRAZABILIDAD. PODEMOS OMITIR XQ EN LAS VERSIONES NUEVA DE SPARK ES AUTOMATICO
spark = SparkSession.builder.appName("EcomMLTraining").getOrCreate()

# Habilitar el autologging de MLflow para registrar parámetros y curvas automáticamente
mlflow.autolog()

# Definimos el experimento en el espacio de Databricks
mlflow.set_experiment("/Shared/ecommerce_churn_high_value")

# 2. CONSUMIR DATASET DE LA CAPA GOLD (PROCESADO POR dbt)
catalog_name = "catalog_prueba_adls"
schema_name  = "ecommerce_gold"
table_name   = "customer_360"

print(f"Cargando datos desde {catalog_name}.{schema_name}.{table_name}...")
df_gold = spark.table(f"{catalog_name}.{schema_name}.{table_name}")

# =====================================================================
# FEATURE ENGINEERING & PREPARACIÓN (PIPELINE SPARK ML)
# =====================================================================
# Transformar variables categóricas (texto) a índices numéricos
indexer_city = StringIndexer(inputCol="city", outputCol="city_index", handleInvalid="keep")
indexer_segment = StringIndexer(inputCol="segment", outputCol="segment_index", handleInvalid="keep")
indexer_category = StringIndexer(inputCol="preferred_category", outputCol="category_index", handleInvalid="keep")

df_transformed = indexer_city.fit(df_gold).transform(df_gold)
df_transformed = indexer_segment.fit(df_transformed).transform(df_transformed)
df_transformed = indexer_category.fit(df_transformed).transform(df_transformed)

# Lista de variables predictoras seleccionadas (Features requeridas)
feature_cols = [
    "customer_tenure_days", "frequency", "monetary_value", 
    "average_ticket", "total_products", "days_since_last_purchase",
    "purchase_frequency_30d", "purchase_frequency_90d",
    "city_index", "segment_index", "category_index"
]

# Para Spark ML se requiere que todos los predictores se agrupen en un único vector llamado 'features'
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
df_ml_ready = assembler.transform(df_transformed).select("features", "is_high_value_customer")

# =====================================================================
# SEPARACIÓN ESTRICTA DE DATOS (TRAIN / TEST SPLIT)
# =====================================================================
# Separación del 80% para entrenamiento y 20% para evaluación con semilla fija
train_df, test_df = df_ml_ready.randomSplit([0.8, 0.2], seed=42)
print(f"Datos de Entrenamiento: {train_df.count()} | Datos de Validación: {test_df.count()}")


# =====================================================================
# CONFIGURACIÓN OBLIGATORIA DE VOLUMEN PARA UNITY CATALOG
# =====================================================================
# Le decimos a MLflow que use el volumen como carpeta temporal de almacenamiento
import os
os.environ['MLFLOW_DFS_TMP'] = "/Volumes/catalog_prueba_adls/ecommerce_gold/mlflow_artifacts/tmp"


# =====================================================================
# ENTRENAMIENTO Y TRAZABILIDAD CON MLFLOW
# =====================================================================
with mlflow.start_run(run_name="Logistic_Regression_Base") as run:
    
    # Parámetros del algoritmo simple (Regresión Logística)
    max_iter_val = 10
    reg_param_val = 0.1
    
    # Inicializar clasificador
    lr = LogisticRegression(
        featuresCol="features", 
        labelCol="is_high_value_customer", 
        maxIter=max_iter_val, 
        regParam=reg_param_val
    )
    
    print("Entrenando el modelo...")
    model_lr = lr.fit(train_df)
    
    # Realizar predicciones sobre el set de prueba segregado (Validation)
    predictions = model_lr.transform(test_df)
    
    # EVALUACIÓN DE MÉTRICAS (Métrica elegida: Área bajo la curva ROC - AUC)
    evaluator = BinaryClassificationEvaluator(
        rawPredictionCol="rawPrediction", 
        labelCol="is_high_value_customer", 
        metricName="areaUnderROC"
    )
    
    auc_metric = evaluator.evaluate(predictions)
    print(f"Resultado de Evaluación -> Área bajo la curva (AUC-ROC): {auc_metric:.4f}")
    
    # REGISTRO MANUAL DE TRAZABILIDAD ADICIONAL (Auditoría)
    mlflow.log_param("dataset_version", "2026-03-01_v1")
    mlflow.log_param("predictor_count", len(feature_cols))
    mlflow.log_metric("auc_roc_validation", auc_metric)
    
    # Guardar y registrar el modelo entrenado en el MLflow Artifact Store de Azure
    mlflow.spark.log_model(model_lr, "logistic_regression_model")
    
    run_id = run.info.run_id
    print(f"¡Experimento finalizado con éxito! Run ID de MLflow: {run_id}")

# =====================================================================
# CONSUMO ANALÍTICO: GUARDAR LA TABLA DE PREDICCIONES FINAL
# =====================================================================
# Tomamos las predicciones finales, limpiamos columnas internas y las guardamos como la tabla final de consumo
df_final_consumption = predictions.select(
    "features", 
    "is_high_value_customer", 
    "prediction", 
    "probability"
).withColumn("prediction_timestamp", current_timestamp())

df_final_consumption.write.mode("overwrite").format("delta") \
    .saveAsTable(f"{catalog_name}.{schema_name}.final_predictions_ml")

print(f"Tabla final de consumo guardada con éxito en: {catalog_name}.{schema_name}.final_predictions_ml")
