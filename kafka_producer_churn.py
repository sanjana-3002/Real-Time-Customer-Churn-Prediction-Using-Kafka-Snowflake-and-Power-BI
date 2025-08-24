from kafka import KafkaProducer
import json
import pandas as pd

# Load CSV or take manual input
df = pd.read_csv("churn_dataset.csv")  # 21 features in this file

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

for _, row in df.iterrows():
    producer.send('churn_input_topic', value=row.to_dict())

producer.flush()
print("✅ Data sent to Kafka topic: churn_input_topic")

