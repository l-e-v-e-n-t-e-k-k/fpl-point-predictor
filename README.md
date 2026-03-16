# fpl-points-predictor
PostreSQL - docker exec -it fpl_postgres psql -U mluser -d fpldb
S4 - docker build -t fpl-s4 -f src/S4/Dockerfile .
        
S1 – Data Ingestion

fpl_api.py
download_players.py

S2 – Data Transformation Service

build_dataset_pandas.py
merge_difficulty.py
add_target.py
build_dataset_multiseason.py

S3 – Model Service

features.py
model.py
train_and_evaluate.py

S4 – Application Service

app.py

1 Ingestion Service (stateless)
Típus: Stateless microservice
Kubernetes objektum: Deployment

        Felelősség:

                Kulso FPL API lekerdezese HTTPS-en

                Nyers JSON/CSV adat validálása

                Raw adat perzisztálása megosztott tárolóra (PVC vagy objektumtár)

2 Transformation Service (batch job)
Típus: Batch microservice
Kubernetes objektum: CronJob

        Felelősség:

                Raw adatok beolvasasa

                Strukturalt adatta alakitas

                Target változó generalas

                Strukturalt adatok betoltese PostgreSQL adatbazisba

3 Model Service (stateless)
Típus: Stateless compute microservice
Kubernetes objektum: Deployment (+ opcionálisan HPA)

        Felelősség:

                Modell betoltese indulaskor

                Feature adatok lekérdezése DB-ből

                Rolling feature-ok keszitese

                Predikció generálása

                REST API endpoint biztosítása

4 Application / API Service
Típus: Public API gateway microservice
Kubernetes objektum: Deployment + Service + Ingress

        Felelősség:

                HTTP keresek fogadasa

                Request validacio

                Model Service hivasa

                Response aggregalasa

5 Database (stateful)
        Típus: Stateful komponens
        Kubernetes objektum: StatefulSet + PVC

        Felelősség:

                Strukturalt dataset tarolasa

                final_dataset tabla biztositasa

                Indexelt lekerdezések tamogatasa


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
                       raw data files ( PVC )
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

Service	        K8s Object	        Skálázás
S1	        Deployment	        horizontális
S2	        CronJob	                batch
Postgres        StatefulSet	        nem skálázott
S3	        Deployment + HPA	horizontális
S4	        Deployment	        opcionális


TRANFORMATION PIPELINE: 
--------------------------
1. build_dataset_pandas
2. merge_difficulty
3. add_target
4. build_dataset_multiseason
=====================

## Running scripts

The project uses the `src` directory as the Python module root.

Before running scripts locally, set the `PYTHONPATH`:

```bash
export PYTHONPATH=src