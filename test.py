import firebase_admin
from firebase_admin import credentials, firestore
import os
import time

cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/your/firebase-credentials.json")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")
    else:
        print("Firebase already initialized")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    exit(1)

db = firestore.client()

print("Querying users collection...")

try:
    start = time.time()
    docs = db.collection("users").limit(1).get()
    end = time.time()
    print(f"Query took {end - start:.2f} seconds")
    for doc in docs:
        print(f"Document ID: {doc.id}, Data: {doc.to_dict()}")
except Exception as e:
    print(f"Firestore query error: {e}")
