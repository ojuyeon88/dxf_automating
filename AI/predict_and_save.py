import pickle
import pandas as pd
import pymysql

# === 예측 대상 CSV 경로 ===
csv_path = "AI/data/text_category_all.csv"

# === 훈련된 모델 경로 ===
vectorizer_path = "AI/model/vectorizer.pkl"
model_path = "AI/model/model.pkl"

# === MySQL 설정 ===
USE_DATABASE = True  # True로 바꾸면 DB 저장
db_config = {
    "host": "localhost",
    "port": 3305,
    "user": "root",
    "password": "0000",
    "database": "fortest",
    "charset": "utf8"
}


# === 모델 불러오기 ===
with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)

with open(model_path, "rb") as f:
    model = pickle.load(f)

# === 텍스트 데이터 불러오기 ===
df = pd.read_csv(csv_path)

# === 예측 수행 ===
X = vectorizer.transform(df["text"])
preds = model.predict(X)

df["predicted_category"] = preds

# === 결과 출력 ===
print("[✔] 예측 결과:")
print(df[["text", "category", "predicted_category"]])

# === 선택적으로 DB 저장 ===
if USE_DATABASE:
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            sql = """
                INSERT INTO poi (name, category, center_x, center_y)
                VALUES (%s, %s, NULL, NULL)
            """
            cursor.execute(sql, (row["text"], row["predicted_category"]))

        conn.commit()
        cursor.close()
        conn.close()
        print("[✔] DB 저장 완료")
    except Exception as e:
        print(f"[❌] DB 저장 오류: {e}")
