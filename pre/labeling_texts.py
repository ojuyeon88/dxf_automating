# === labeling_texts.py (수정 완료) ===
import ezdxf
import re
import csv
import os
from shapely.geometry import Polygon, Point
from collections import defaultdict

# 설정
dxf_folder = "files/dxf"
output_csv = "pre/data/text_category_all.csv"
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

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

def clean_text(text):
    text = re.sub(r"\d+(\.\d+)?㎡", "", text)
    text = re.sub(r"[A-Z]*\d{2,4}(-\d+)?호실?", "", text)
    IGNORE_KEYWORDS = ["도면", "평면도", "창의관", "지하", "전용면적", "㎡"]
    for kw in IGNORE_KEYWORDS:
        if kw in text:
            return ""
    return text.strip()

def categorize(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "misc"

def normalize_floor(floor_str):
    floor_str = floor_str.upper().replace("F", "")
    if floor_str.startswith("B"):
        return -int(floor_str.replace("B", ""))
    return int(floor_str)

raw_results = []

for filename in os.listdir(dxf_folder):
    if filename.lower().endswith(".dxf"):
        filepath = os.path.join(dxf_folder, filename)
        print(f"[📂] 처리 중: {filename}")
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()
            floor = filename.split("-")[0]

            polygon_centers = []
            for entity in msp.query("LWPOLYLINE POLYLINE"):
                try:
                    if entity.dxftype() == "LWPOLYLINE":
                        points = [(p[0], p[1]) for p in entity]
                    else:
                        points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices()]
                    if len(points) < 3:
                        continue
                    polygon = Polygon(points)
                    if polygon.is_valid and polygon.area > 1000:
                        center = polygon.centroid
                        polygon_centers.append(center)
                except Exception as e:
                    print(f"  └ 폴리라인 처리 오류: {e}")

            for entity in msp.query("TEXT MTEXT"):
                try:
                    if entity.dxftype() == "TEXT":
                        content = entity.dxf.text
                        insert = entity.dxf.insert
                    elif entity.dxftype() == "MTEXT":
                        content = entity.plain_text()
                        insert = entity.dxf.insert
                    else:
                        continue

                    content = content.strip()
                    cleaned = clean_text(content)
                    if not cleaned or not is_meaningful(cleaned):
                        continue

                    category = categorize(cleaned)
                    tx, ty = insert.x, insert.y
                    text_point = Point(tx, ty)

                    min_dist = float('inf')
                    nearest_cx, nearest_cy = None, None
                    for center in polygon_centers:
                        dist = text_point.distance(center)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_cx, nearest_cy = center.x, center.y

                    if min_dist < 5000:
                        raw_results.append((filename, floor, cleaned, category, round(nearest_cx, 2), round(nearest_cy, 2)))

                except Exception as e:
                    print(f"  └ 텍스트 처리 오류: {e}")
        except Exception as e:
            print(f"[❌] {filename} 읽기 실패: {e}")

# 병합 로직 (좌표 반올림 기반)
clusters = defaultdict(list)
for row in raw_results:
    key = (row[0], normalize_floor(row[1]), row[3], round(row[4], -1), round(row[5], -1))
    clusters[key].append(row[2])

all_results = []
for (filename, floor, category, cx, cy), texts in clusters.items():
    merged_text = " ".join(sorted(set(texts)))
    all_results.append((filename, floor, merged_text, category, cx, cy))

print(f"[✔] 총 {len(all_results)}건 저장 예정")

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "floor", "text", "category", "center_x", "center_y"])
    writer.writerows(all_results)

print(f"\n[✔] 전체 결과 저장 완료: {output_csv}")