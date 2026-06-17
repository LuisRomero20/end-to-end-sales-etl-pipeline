import pandas as pd
import random
from datetime import datetime, timedelta

print("Generando dataset premium de 2000 filas...")

productos = [
    ("Laptop Pro", 1200), ("Monitor 27\"", 300), 
    ("Teclado Mecanico", 85), ("Mouse Inalambrico", 45), 
    ("Docking Station", 150), ("Cable HDMI", 15)
]
clientes = ["Empresa A", "Empresa B", "Juan Perez", "Maria Gomez", "Carlos Ruiz", "Startup Tech", "Consultora X"]
estados = ["Completado", "Completado", "Completado", "Pendiente", "Cancelado"]

data = []
fecha_inicio = datetime(2025, 11, 1)

for i in range(2000):
    id_transaccion = 1000 + i
    # Generar fecha aleatoria en los últimos 6 meses
    dias_random = random.randint(0, 180)
    fecha = fecha_inicio + timedelta(days=dias_random)
    
    # Formatos de fecha sucios aleatorios
    formato = random.choice(['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y'])
    fecha_str = fecha.strftime(formato)
    
    producto, precio = random.choice(productos)
    cantidad = random.choices([1, 2, 3, 5, -1, None], weights=[60, 20, 10, 5, 2, 3])[0]
    cliente = random.choice(clientes)
    estado = random.choice(estados)
    
    data.append([id_transaccion, fecha_str, producto, cantidad, precio, cliente, estado])

df = pd.DataFrame(data, columns=['id_transaccion', 'fecha', 'producto', 'cantidad', 'precio_unitario', 'cliente', 'estado'])

# Guardar el archivo sucio masivo
ruta = 'data/ventas_crudas_semestre.csv'
df.to_csv(ruta, index=False)
print(f"¡Listo! Archivo {ruta} generado con éxito. Ejecuta tu ETL ahora.")