import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

USERS         = os.path.join(DATA_DIR, "users.csv")
ADMIN         = os.path.join(DATA_DIR, "admin.csv")       # matches your admin.csv
VULN          = os.path.join(DATA_DIR, "vulnerabilities.csv")
NOTIFICATIONS = os.path.join(DATA_DIR, "notifications.csv")

def read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)

def write_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)