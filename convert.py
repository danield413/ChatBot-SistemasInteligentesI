import csv
import json
import os

# Rutas de archivos
CSV_FILE = "./csv/gold_set.csv"
JSON_FILE = "./json/gold_set.json"

try:
    # Leer el archivo CSV
    with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        gold_set = []
        
        for row in csv_reader:
            gold_set.append({
                "question": row['question'],
                "category": row['category']
            })
    
    # Crear el directorio json si no existe
    os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
    
    # Guardar en formato JSON
    with open(JSON_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(gold_set, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"✅ Conversión exitosa!")
    print(f"   CSV: {CSV_FILE}")
    print(f"   JSON: {JSON_FILE}")
    print(f"   Total de preguntas: {len(gold_set)}")

except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo '{CSV_FILE}'")
except Exception as e:
    print(f"❌ Error durante la conversión: {e}")