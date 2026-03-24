import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

USERS_CSV = os.path.join(DATA_DIR, "users.csv")
ADMIN_CSV = os.path.join(DATA_DIR, "admin.csv")
VULN_CSV = os.path.join(DATA_DIR, "vulnerabilities.csv")
