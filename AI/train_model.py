# 사용할 파일: text_category_all.csv
# 학습 후: model.pkl, vectorizer.pkl 저장

import pandas as pd
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# 학습 데이터 로드
df = pd.read_csv("AI/data/text_category_all.csv")

# 벡터화 및 학습
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df["text"])
y = df["category"]

clf = MultinomialNB()
clf.fit(X, y)

# 모델 저장
with open("AI/model/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open("AI/model/model.pkl", "wb") as f:
    pickle.dump(clf, f)

print("[✔] 모델 학습 및 저장 완료!")
