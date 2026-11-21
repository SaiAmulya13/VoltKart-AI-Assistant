
from pathlib import Path
import pandas as pd

# Folder where project data is stored
data_folder = Path("data")

csv_files = list(data_folder.rglob("*.csv"))

if not csv_files:
    print("No CSV files found inside the data folder.")

for file_path in csv_files:
    try:
        df = pd.read_csv(file_path, nrows=5)

        print("\n" + "=" * 60)
        print("File:", file_path.name)
        print("Path:", file_path)
        print("Columns:", list(df.columns))

    except Exception as e:
        print("Could not read:", file_path.name)
        print("Error:", e)
