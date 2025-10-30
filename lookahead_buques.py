import pandas as pd
import matplotlib.pyplot as plt

# === 1. CONFIGURACIÓN ===
# Cambia el nombre del archivo Excel según corresponda:
archivo = "buques.xlsx"

# Duración de la ventana de lookahead (en horas)
lookahead_h = 24

# Intervalo de análisis (cada cuántas horas revisar)
intervalo_h = 6


# === 2. LECTURA DEL EXCEL ===
df = pd.read_excel(archivo)

# Unir día + hora (reales)
df["arrival"] = pd.to_datetime(df["Arrival day"].astype(str) + " " + df["Arrival time"].astype(str))
df["departure"] = pd.to_datetime(df["Departure day"].astype(str) + " " + df["Departure time"].astype(str))

# Si la columna de muelle se llama diferente (por ejemplo “Arrival” o “Muelle”), ajústalo aquí:
df.rename(columns={"Arrival": "Muelle"}, inplace=True)

# Mostrar primeras filas para verificar
print("Datos cargados correctamente:\n", df[["SHIP", "Muelle", "arrival", "departure"]].head(), "\n")


# === 3. FUNCIÓN DE OCUPACIÓN POR MUELLE ===
def ocupacion(df, tiempo_actual, lookahead_h):
    fin_ventana = tiempo_actual + pd.Timedelta(hours=lookahead_h)
    activos = df[(df["arrival"] <= fin_ventana) & (df["departure"] >= tiempo_actual)]
    return activos.groupby("Muelle")["SHIP"].count()


# === 4. GENERAR LÍNEA DE TIEMPO ===
timeline = pd.date_range(df["arrival"].min(), df["departure"].max(), freq=f"{intervalo_h}H")

# === 5. CALCULAR OCUPACIÓN PARA CADA TIEMPO ===
resultados = []
for t in timeline:
    ocup = ocupacion(df, t, lookahead_h)
    ocup.name = t
    resultados.append(ocup)

# Unir resultados en una sola tabla
ocup_df = pd.DataFrame(resultados).fillna(0).astype(int)
ocup_df.index.name = "Tiempo"

print("Ocupación por muelle (buques simultáneos dentro del lookahead):\n")
print(ocup_df.head())


# === 6. GRÁFICO DE OCUPACIÓN ===
ocup_df.plot(figsize=(10, 5))
plt.title(f"Ocupación de muelles con ventana de lookahead = {lookahead_h} h")
plt.xlabel("Tiempo")
plt.ylabel("Número de buques en puerto")
plt.legend(title="Muelle")
plt.grid(True)
plt.tight_layout()
plt.show()