import csv
import random
from datetime import datetime, timedelta

# 1. GENERAR CLIENTES (500 registros)
customers = []
cities = ['Bogota', 'Medellin', 'Cali', 'Barranquilla', 'Cartagena']
segments = ['Consumer', 'Corporate', 'Home Office']

for i in range(1, 501):
    cust_id = f"CUST_{i:03d}"
    signup_date = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
    city = random.choice(cities)
    segment = random.choice(segments)
    customers.append([cust_id, signup_date, city, segment])

with open('ingestion/customers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'signup_date', 'city', 'segment'])
    writer.writerows(customers)

# 2. GENERAR PRODUCTOS (50 registros)
products = []
categories = ['Electronics', 'Clothing', 'Home', 'Beauty', 'Sports']
brands = ['Brand_A', 'Brand_B', 'Brand_C', 'Brand_D', 'Brand_E']

for i in range(1, 51):
    prod_id = f"PROD_{i:02d}"
    category = random.choice(categories)
    brand = random.choice(brands)
    description = f"Premium item from {category} - {brand}"
    price = round(random.uniform(5.0, 500.0), 2)
    products.append([prod_id, category, brand, description, price])

with open('ingestion/products.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['product_id', 'category', 'brand', 'description', 'price'])
    writer.writerows(products)

# 3. GENERAR VENTAS (1000 registros, incluye duplicados y registros corruptos)
sales = []
start_date = datetime(2026, 1, 1)

for i in range(1, 981):  # 980 registros normales
    sale_id = f"SALE_{i:04d}"
    cust_id = f"CUST_{random.randint(1, 500):03d}"
    prod_id = f"PROD_{random.randint(1, 50):02d}"
    timestamp = (start_date + timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))).strftime('%Y-%m-%d %H:%M:%S')
    quantity = random.randint(1, 10)
    # Buscamos el precio en la lista de productos creados para mantener coherencia básica
    unit_price = [p[4] for p in products if p[0] == prod_id][0]
    sales.append([sale_id, cust_id, prod_id, timestamp, quantity, unit_price])

# Inyectar 10 registros corruptos para probar la CUARENTENA BLOQUEANTE
sales.append(['SALE_981', 'CUST_001', 'PROD_01', '2026-02-01 10:00:00', 0, 50.0])   # Cantidad igual a 0 (Invalido)
sales.append(['SALE_982', 'CUST_002', 'PROD_02', '2026-02-01 11:00:00', -2, 20.0])  # Cantidad negativa (Invalido)
sales.append(['', 'CUST_003', 'PROD_03', '2026-02-01 12:00:00', 1, 10.0])           # sale_id Nulo/Vacío (Invalido)
sales.append(['SALE_984', 'CUST_999', 'PROD_04', '2026-02-01 13:00:00', 1, 15.0])   # Cliente que NO existe (Invalido para dbt test)
sales.append(['SALE_985', 'CUST_004', 'PROD_99', '2026-02-01 14:00:00', 2, 100.0])  # Producto que NO existe (Invalido para dbt test)

# Inyectar 5 duplicados exactos para probar DEDUPLICACIÓN
for _ in range(5):
    sales.append(random.choice(sales[:900]))

with open('ingestion/sales.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['sale_id', 'customer_id', 'product_id', 'timestamp', 'quantity', 'unit_price'])
    writer.writerows(sales)

print("¡Archivos sales.csv, customers.csv y products.csv generados con éxito dentro de ingestion/!")
