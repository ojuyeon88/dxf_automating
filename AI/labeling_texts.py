import ezdxf
import re
import csv
import os

# === 설정 ===
dxf_folder = "files/dxf"
output_csv = "AI/data/text_category_all.csv"

# === 의미 있는 텍스트 필터링 키워드 ===
KEYWORDS = ['호', '실', '강의실', '계단', '화장실', '세미나', '회의', '휴게', '엘리베이터', '전기', '기계']

# === 카테고리 키워드 사전 ===
CATEGORY_KEYWORDS = {
    "lecture": ["강의실", "계단강의실"],
    "restroom": ["화장실", "남자화장실", "여자화장실", "장애인화장실"],
    "stair": ["계단실", "계단"],
    "elevator": ["ELEV", "ELEV실", "엘리베이터"],
    "ps": ["PS실", "전기", "기계실", "기계"],
    "office": ["교수연구실", "부원장실", "행정실", "부속실"],
    "seminar": ["세미나실", "회의실", "세미나", "회의"],
    "lab": ["연구실", "실험실", "실습실", "Testbed", "시스템", "CAD", "로봇", "분석실"],
    "lounge": ["휴게실", "숙직실", "독서실", "휴게"],
    "misc": []
}

# === 의미 있는 텍스트 판단 함수 ===
def is_meaningful(text):
    text = text.strip()
    if len(text) < 2:
        return False
    if re.fullmatch(r'[\W_]+', text):
        return False
    if re.fullmatch(r'\d{3,5}', text):
        return False
    for kw in KEYWORDS:
        if kw in text:
            return True
    if re.search(r'\d+[가-힣]+', text):
        return True
    return False

# === 카테고리 자동 분류 함수 ===
def categorize(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "misc"

# === 결과 저장 리스트
all_results = []

# === 폴더 내 모든 dxf 파일 처리
for filename in os.listdir(dxf_folder):
    if filename.lower().endswith(".dxf"):
        filepath = os.path.join(dxf_folder, filename)
        print(f"[📂] 처리 중: {filename}")
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()

            for entity in msp.query("TEXT MTEXT"):
                try:
                    if entity.dxftype() == "TEXT":
                        content = entity.dxf.text
                    elif entity.dxftype() == "MTEXT":
                        content = entity.plain_text()
                    else:
                        continue

                    content = content.strip()
                    if not is_meaningful(content):
                        continue

                    category = categorize(content)
                    all_results.append((filename, content, category))

                except Exception as e:
                    print(f"  └ 텍스트 처리 오류: {e}")
        except Exception as e:
            print(f"[❌] {filename} 읽기 실패: {e}")

# === CSV로 저장
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "text", "category"])
    writer.writerows(all_results)

print(f"\n[✔] 전체 결과 저장 완료: {output_csv}")
