# Registro de Decisiones de Arquitectura

Este documento detalla las justificaciones de ingeniería de datos aplicadas para el desarrollo y diseño del pipeline de e-commerce.

## 1. Servicios y herramientas seleccionadas para el proyecto
*   **Decisión:** Se eligió los servicios de Azure como: ADLS, Azure Data Factory y Azure Databricks, debido a los tech skill del Data Engineer sobre estas herramientas. Se configuró un budget en Azure para no tener costos altos ya que la suscripción usada es de pago. Adicionalmente, se usó dbt core, configurado en el equipo local y enlazado al workspace y cluster de Databricks (mediante JBDC).

En escenarios productivos la decisión de una arquitectura de datos pasa por evaluar varios aspectos como los técnicos (team técnico calificado), soluciones on-premise actualmente usadas (servers, base de datos, etc.), compatibilidad con plataformas/servicios/herramientas, costos de almacenaje y procesamiento en nube entre otros. Para este caso de uso puntual la decisión se tomó basado en lo indicado anteriormente. 


## 2. Implementación de una Cuarentena Bloqueante en la Capa RAW (PySpark)
*   **Decisión:** Diseñar un filtro explícito en Spark SQL dentro de la fase de ingesta para desviar registros inválidos (cantidades nulas o menores/iguales a cero y precios negativos) hacia la tabla `ecommerce_raw.quarantine_sales`.
*   **Justificación:** Cumple con la regla obligatoria de calidad analítica. Al detener los datos corruptos en el origen, evitamos desperdiciar créditos de cómputo en transformaciones posteriores y protegemos a los modelos de machine learning de sesgos introducidos por datos erróneos.

## 3. Desacoplamiento de la Tabla de Consumo de Machine Learning
*   **Decisión:** Crear una tabla final separada llamada `final_predictions_ml_analytics` que consume de la tabla técnica base del modelo.
*   **Justificación:** Spark ML genera vectores densos y dispersos nativos que son incompatibles y causan errores de parseo en herramientas de BI como Power BI. Al desempaquetar estos vectores mediante PySpark en strings y flotantes tradicionales, optimizamos el rendimiento de los reportes gerenciales.