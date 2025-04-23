import ezdxf
import re
import csv
import os

# 설정
dxf_folder = "files/dxf"
output_csv = "AI/data/text_category_all.csv"

# 키워드
KEYWORDS = ['호', '실', '강의실', '계단', '화장실', '세미나', '회의', '휴게', '엘리베이터', '전기', '기계']
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

def is_meaningful(text):
    text = text.strip()
    if len(text) < 2: return False
    if re.fullmatch(r'[\W_]+', text): return False
    if re.fullmatch(r'\d{3,5}', text): return False
    if any(kw in text for kw in KEYWORDS): return True
    if re.search(r'\d+[가-힣]+', text): return True
    return False

def categorize(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "misc"

all_results = []

for filename in os.listdir(dxf_folder):
    if filename.lower().endswith(".dxf"):
        filepath = os.path.join(dxf_folder, filename)
        print(f"[📂] 처리 중: {filename}")
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()
            floor = filename.split("-")[0]

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
                    all_results.append((filename, floor, content, category))

                except Exception as e:
                    print(f"  └ 텍스트 처리 오류: {e}")
        except Exception as e:
            print(f"[❌] {filename} 읽기 실패: {e}")

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "floor", "text", "category"])
    writer.writerows(all_results)

print(f"\n[✔] 전체 결과 저장 완료: {output_csv}")
