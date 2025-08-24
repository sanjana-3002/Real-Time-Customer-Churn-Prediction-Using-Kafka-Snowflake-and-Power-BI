
# Real-Time Customer Churn Prediction (Kafka → Snowflake → Power BI)

An end-to-end, **streaming** churn-risk pipeline: **Kafka** ingests live events, **Snowflake** handles storage, feature engineering, and model inference, and **Power BI** surfaces **interactive churn dashboards** (risk, drivers, next-best actions).

---

## ✨ Highlights
- **Live ingestion** of customer activity via Kafka topics.
- **Snowflake schemas** for `RAW_DATA` → `FEATURES` → `PREDICTIONS`.
- **XGBoost + SHAP** for explainable churn scoring.
- **Power BI (DirectQuery)** for real-time KPIs (churn rate, revenue at risk, cohorts).
- **Modular, scalable** design—swap data sources or models with minimal changes.

---

## 🔧 Architecture

```

\[Producers]
→ \[Kafka Topic: customer\_events]
→ \[Kafka Connect Snowflake Sink / Snowpipe]
→ \[Snowflake: RAW\_DATA]
→ Transform/FE → \[FEATURES]
→ ML Inference (XGBoost + SHAP)
→ \[PREDICTIONS] ↔ (DirectQuery) ↔ \[Power BI Dashboards]

````

---

## 🧱 Tech Stack
- **Data & Infra:** Apache Kafka, Kafka Connect / Snowpipe, Snowflake
- **ML:** Python, Pandas, XGBoost, SHAP (optional: Snowpark)
- **BI:** Power BI (DirectQuery / Live Connection)

---

## 🚀 Quick Start

### 1) Kafka (local)
```bash
# Start Kafka (example uses docker-compose)
docker-compose up -d

# Create events topic
kafka-topics --create --topic customer_events --bootstrap-server localhost:9092
````

### 2) Kafka → Snowflake Connector (Sink)

Create a Snowflake sink connector (Confluent/Kafka Connect). Example config:

```json
{
  "name": "snowflake-sink",
  "config": {
    "connector.class": "com.snowflake.kafka.connector.SnowflakeSinkConnector",
    "tasks.max": "1",
    "topics": "customer_events",

    "snowflake.url.name": "<ACCOUNT>.snowflakecomputing.com",
    "snowflake.user.name": "<USER>",
    "snowflake.password": "<PASSWORD>",
    "snowflake.database.name": "CHURN_ANALYSIS",
    "snowflake.schema.name": "RAW_DATA",
    "snowflake.role.name": "<ROLE>",
    "snowflake.warehouse": "<WAREHOUSE>",

    "buffer.count.records": "2000",
    "buffer.flush.time": "60",
    "buffer.size.bytes": "5000000"
  }
}
```

> Use secrets/variables (not plaintext) in real deployments.

### 3) Snowflake Setup

```sql
CREATE DATABASE IF NOT EXISTS CHURN_ANALYSIS;
CREATE SCHEMA   IF NOT EXISTS CHURN_ANALYSIS.RAW_DATA;
CREATE SCHEMA   IF NOT EXISTS CHURN_ANALYSIS.FEATURES;
CREATE SCHEMA   IF NOT EXISTS CHURN_ANALYSIS.PREDICTIONS;

-- Example RAW landing table (adjust to your events)
CREATE OR REPLACE TABLE RAW_DATA.TELCO_CUSTOMER_CHURN (
  CUSTOMERID          STRING,
  EVENT_TS            TIMESTAMP_NTZ,
  TENURE              NUMBER,
  MONTHLYCHARGES      NUMBER,
  CONTRACT_TYPE       STRING,
  SUPPORT_TICKETS_30D NUMBER,
  LAST_LOGIN_DAYS     NUMBER,
  LABEL               NUMBER    -- optional (for offline training)
);

-- Simple feature view (example only)
CREATE OR REPLACE VIEW FEATURES.CHURN_FEATURES AS
SELECT
  CUSTOMERID,
  TENURE,
  MONTHLYCHARGES,
  IFF(CONTRACT_TYPE='Month-to-month',1,0) AS IS_MTM,
  NVL(SUPPORT_TICKETS_30D,0)              AS TICKETS_30D,
  NVL(LAST_LOGIN_DAYS,999)                AS LAST_LOGIN_DAYS
FROM RAW_DATA.TELCO_CUSTOMER_CHURN;

-- Predictions table
CREATE OR REPLACE TABLE PREDICTIONS.CHURN_PREDICTIONS (
  CUSTOMERID        STRING,
  PREDICTION_TS     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  CHURN_FLAG        NUMBER(1,0),
  CHURN_PROBABILITY FLOAT,
  RISK_FACTORS      VARIANT   -- e.g., top SHAP features
);
```

### 4) Model Training & Inference (Python)

```bash
# (optional) venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` (minimal):

```
pandas
xgboost
scikit-learn
shap
snowflake-connector-python
python-dotenv
```

**Workflow (pseudo):**

```python
# load features from Snowflake → train → save model → score → write back to PREDICTIONS
# 1) offline train (batch) using historical labeled data
# 2) periodic/streaming scoring: pull FEATURES, predict, compute SHAP, upsert predictions
```

> For low-latency **in-DB** scoring, consider **Snowpark UDFs** or Snowflake Tasks/Streams.

### 5) Power BI (DirectQuery)

1. Connect to **Snowflake** (DirectQuery).
2. Point to `PREDICTIONS.CHURN_PREDICTIONS` (+ any supporting views).
3. Build visuals: churn rate, revenue at risk, top risk factors, cohort trends, drill-through to customer.

---

## 🧪 Sample Producer (optional)

```bash
python src/ingest/produce_events.py --topic customer_events --rate 20
```

Emits synthetic customer events to help you test end-to-end.

---

## 📂 Repository Structure

```
.
├── docker/                      # Kafka/ZooKeeper (compose)
├── sql/                         # Snowflake DDLs & views
├── src/
│   ├── ingest/                  # Kafka producers
│   ├── features/                # Feature engineering helpers
│   ├── ml/                      # Train/infer, SHAP, write-back
│   └── utils/                   # Config, Snowflake I/O
├── powerbi/                     # .pbix files or templates
├── requirements.txt
└── README.md
```

---

## 🔍 Outputs

* **`CHURN_FLAG`** (0/1) – binary churn prediction
* **`CHURN_PROBABILITY`** (0.0–1.0) – churn likelihood
* **`RISK_FACTORS`** – JSON with top SHAP features per prediction

---

## 🛡️ Security & Ops Notes

* Keep **credentials** in secrets managers / `.env` (never commit).
* Add **DLT/PII handling** if events contain sensitive data.
* Monitor: Kafka lag, Snowflake load errors, scoring freshness SLAs.
* Testing: unit tests for FE and scoring; golden datasets for drift checks.

---

## 🗺️ Roadmap

* Snowpark UDFs for **in-Snowflake** real-time scoring
* **Snowpipe Streaming** to cut end-to-end latency
* **Alerting** to CRM (Salesforce/HubSpot) for retention playbooks
* Model registry + CI/CD for versioned deploys
