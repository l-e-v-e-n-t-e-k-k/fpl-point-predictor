MLOps Model Serving System (Kubernetes + PVC)
Overview

This project implements a lightweight MLOps pipeline for model versioning and serving using Kubernetes.

The system consists of two services:

s1 (trainer/producer): generates and updates machine learning models
s2 (inference/consumer): dynamically loads the latest model and performs inference

Models are stored on a shared Persistent Volume (PVC) with versioning and atomic updates to ensure consistency.

Architecture
Kubernetes cluster (non-AWS)
Shared Persistent Volume (PVC)
Versioned model storage
Atomic updates using symlinks and metadata file (latest.json)
Key Features
🔄 Dynamic model reloading without restarting services
🧠 Model versioning using timestamp-based versions
⚡ Fast access via shared storage (no network fetch)
🔒 Consistency guarantees using atomic file operations
📦 Separation of concerns (training vs inference)
Storage Structure

/models/
├── v20260321_120000/
│ └── model.pt
├── v20260321_130000/
│ └── model.pt
├── current -> /models/v20260321_130000
└── latest.json

How It Works
s1 generates a new model version
Writes model to a new versioned directory
Atomically updates:
current symlink
latest.json
s2 polls for changes and reloads the model if a new version is available
Tech Stack
Kubernetes
Python
Persistent Volumes (PVC)
File-based coordination (atomic rename, symlinks)
Future Improvements
Event-based reload (file watcher)
S3 integration as backup storage
Model metadata tracking (accuracy, metrics)
Canary deployments for model rollout
Why This Project Matters

This project demonstrates:

Distributed system design
Handling consistency and race conditions
Practical MLOps patterns without heavy frameworks
Production-like architecture using simple components

s3 – modell mentés (helyesen!)
✅ Python példa (atomic + verziózás)
import json
import joblib
import os
import tempfile
from datetime import datetime
from pathlib import Path

MODEL_DIR = Path("/models")


def save_model_atomic(model):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    version_name = f"model_{timestamp}.joblib"

    final_model_path = MODEL_DIR / version_name
    latest_path = MODEL_DIR / "latest.json"

    # 1. ideiglenes fájlba mentés
    with tempfile.NamedTemporaryFile(dir=MODEL_DIR, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        joblib.dump(model, tmp_path)

    # 2. atomic rename (ez garantált Linuxon)
    os.replace(tmp_path, final_model_path)

    # 3. latest.json frissítése (szintén atomic)
    latest_tmp = MODEL_DIR / "latest_tmp.json"
    with open(latest_tmp, "w") as f:
        json.dump({"model_path": version_name}, f)

    os.replace(latest_tmp, latest_path)

    print(f"Saved new model: {version_name}")

2. ☸️ PVC mount (mindkét service-ben)
volumeMounts:
- name: model-volume
  mountPath: /models

volumes:
- name: model-volume
  persistentVolumeClaim:
    claimName: model-pvc

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-pvc
spec:
  accessModes:
    - ReadWriteMany  # fontos: több pod olvashatja
  resources:
    requests:
      storage: 1Gi

3. s4 – modell betöltés + reload
✅ Python példa (poll + cache)
import json
import joblib
import time
from pathlib import Path

MODEL_DIR = Path("/models")
LATEST_FILE = MODEL_DIR / "latest.json"


class ModelService:
    def __init__(self):
        self.model = None
        self.current_model_path = None

    def load_model(self, model_path):
        print(f"Loading model: {model_path}")
        self.model = joblib.load(MODEL_DIR / model_path)
        self.current_model_path = model_path

    def check_for_update(self):
        if not LATEST_FILE.exists():
            return

        with open(LATEST_FILE) as f:
            data = json.load(f)

        new_path = data["model_path"]

        if new_path != self.current_model_path:
            self.load_model(new_path)

    def start_auto_reload(self, interval=10):
        while True:
            try:
                self.check_for_update()
            except Exception as e:
                print(f"Reload error: {e}")
            time.sleep(interval)

🧪 Használat
service = ModelService()

# induláskor load
service.check_for_update()

# háttér reload loop
import threading
threading.Thread(target=service.start_auto_reload, daemon=True).start()