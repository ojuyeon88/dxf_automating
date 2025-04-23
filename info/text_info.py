import ezdxf

# DXF 파일 경로 설정
dxf_path = "files/dxf/1F-autosync.dxf"

# 도면 불러오기
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# 텍스트 추출 및 로그 출력
for entity in msp.query("TEXT MTEXT"):
    try:
        if entity.dxftype() == "TEXT":
            content = entity.dxf.text
            insert = entity.dxf.insert
        elif entity.dxftype() == "MTEXT":
            content = entity.plain_text()
            insert = entity.dxf.insert

        print(f"[{entity.dxftype()}] '{content.strip()}' → 위치: X={insert.x:.3f}, Y={insert.y:.3f}")
    
    except Exception as e:
        print(f"❌ 텍스트 추출 오류: {e}")
