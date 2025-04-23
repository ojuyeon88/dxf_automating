import pickle
import pandas as pd
import pymysql

csv_path = "AI/data/text_category_all.csv"
vectorizer_path = "model/vectorizer.pkl"
model_path = "model/model.pkl"

USE_DATABASE = True

db_config = {
    "host": "localhost",
    "port": 3305,
    "user": "root",
    "password": "0000",
    "database": "forTest",
    "charset": "utf8"
}

with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)

with open(model_path, "rb") as f:
    model = pickle.load(f)

df = pd.read_csv(csv_path)
X = vectorizer.transform(df["text"])
preds = model.predict(X)
df["predicted_category"] = preds

print("[✔] 예측 결과 예시:")
print(df[["text", "category", "predicted_category"]].head())

if USE_DATABASE:
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            sql = """
                INSERT INTO poi (name, category, center_x, center_y, floor)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                row["text"],
                row["predicted_category"],
                None,  # 좌표 미지정 상태
                None,
                row["floor"]
            ))

        conn.commit()
        cursor.close()
        conn.close()
        print("[✔] DB 저장 완료")
    except Exception as e:
        print(f"[❌] DB 저장 오류: {e}")
