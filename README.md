# fpl-points-predictor
S1 – Data Ingestion

fpl_api.py
download_players.py

S2 – Data Transformation Service

build_dataset_pandas.py
merge_difficulty.py
add_target.py
align_current_season.py
build_dataset_multiseason.py
clean_multiseason.py
build_final_dataset.py

S3 – Model Service

features.py
model.py
train_and_evaluate.py

S4 – Application Service

app.py

1 Ingestion Service (stateless)

        API hívás

       // adat mentés DB-be

        Kubernetes Deployment

        horizontálisan skálázható

2 Transformation Service (batch job)

        Raw → structured

        futtatható CronJob-ként

        adatbázisba ír

3 Model Service (stateless)

        DB-ből olvas

        betölti a modellt

        predikció generál

        FastAPI

        /predict

        /health

4 Application / API Service

        FastAPI

        külső endpoint

        UI / public API

        S3-at hívja REST-en keresztül

5 Database (stateful)

        PostgreSQL

        StatefulSet

        PersistentVolume

        PersistentVolumeClaim

                          ┌──────────────────────┐
                          │   External FPL API   │
                          └───────────┬──────────┘
                                      │ HTTPS
                                      ▼
                ┌────────────────────────────────┐
                │ S1 – Data Ingestion Service   │
                │ (Stateless)                   │
                │ fpl_api.py                    │
                │ download_players.py           │
                └───────────┬────────────────────┘
                            │ file write (JSON/CSV)
                            ▼
                       raw data files
                            │
                            ▼
                ┌────────────────────────────────┐
                │ S2 – Data Transformation Svc  │
                │ (Batch)                       │
                │ build + merge + target        │
                └───────────┬────────────────────┘
                            │ SQL INSERT
                            ▼
                ┌────────────────────────────────┐
                │         PostgreSQL DB         │
                │   final_dataset table         │
                │ (Stateful + PVC)              │
                └───────────┬────────────────────┘
                            │ SQL SELECT
                            ▼
                ┌────────────────────────────────┐
                │ S3 – Model Service (FastAPI)  │
                │ reads from DB                 │
                │ exposes /predict              │
                └───────────┬────────────────────┘
                            │ REST (internal)
                            ▼
                ┌────────────────────────────────┐
                │ S4 – Application Service      │
                │ (FastAPI, Public API)         │
                └───────────┬────────────────────┘
                            │ HTTP
                            ▼
                         Client

Namespace: fpl-system

Deployments:
  ingestion-deployment
  model-deployment
  api-deployment

StatefulSet:
  postgres

PVC:
  postgres-pvc

Services:
  postgres-service
  api-service

TRANFORMATION PIPELINE: 
--------------------------
1. download_players.py
2. build_dataset_pandas
3. merge_difficulty
4. add_target
5. align_current_season
+++++++++++++++++++++++
1. build_dataset_multiseason
2. clean_multiseason
=====================
build_final_dataset