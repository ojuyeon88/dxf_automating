import ezdxf
import re

# 필터링 기준
KEYWORDS = ['호', '실', '강의실', '계단', '화장실', '세미나', '회의', '휴게', '엘리베이터', '전기', '기계']

def is_meaningful(text):
    text = text.strip()

    # 1. 글자 수 너무 짧으면 제외
    if len(text) < 2:
        return False

    # 2. 특수기호만 있는 경우 제외
    if re.fullmatch(r'[\W_]+', text):
        return False

    # 3. 숫자만 있는 경우 제외 (ex: 6000, 4500)
    if re.fullmatch(r'\d{3,5}', text):
        return False

    # 4. 키워드 포함 여부
    for kw in KEYWORDS:
        if kw in text:
            return True

    # 5. 숫자+한글 조합 (예: 101호, 201호실 등)
    if re.search(r'\d+[가-힣]+', text):
        return True

    return False

doc = ezdxf.readfile("files/dxf/3F-autosync.dxf")
msp = doc.modelspace()

print("[✔] 의미 있는 텍스트 추출 결과:")

for entity in msp.query("TEXT MTEXT"):
    try:
        if entity.dxftype() == "TEXT":
            content = entity.dxf.text
        elif entity.dxftype() == "MTEXT":
            content = entity.plain_text()
        else:
            continue

        if is_meaningful(content):
            print(f"  → {content.strip()}")

    except Exception as e:
        print(f"❌ 오류: {e}")
