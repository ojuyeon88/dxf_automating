import pandas as pd
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# 학습용 CSV 경로
csv_path = "AI/data/text_category_all.csv"

# 데이터 불러오기
df = pd.read_csv(csv_path)
X_text = df["text"]
y_label = df["category"]

# 벡터라이저 + 분류기 학습
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(X_text)

clf = MultinomialNB()
clf.fit(X, y_label)

# 디렉토리 없으면 생성
import os
os.makedirs("model", exist_ok=True)

# 모델 저장
with open("model/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open("model/model.pkl", "wb") as f:
    pickle.dump(clf, f)

print("[✔] 모델 학습 및 저장 완료")
