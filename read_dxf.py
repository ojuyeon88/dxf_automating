import ezdxf
import os

# DXF 파일들이 들어있는 폴더 경로
input_folder = "files/dxf"

# [폴더 내 모든 DXF 파일 처리 - 기본 동작]
filenames = [f for f in os.listdir(input_folder) if f.lower().endswith(".dxf")]

# 파일 리스트 순회
for filename in filenames:
    dxf_path = os.path.join(input_folder, filename)
    txt_name = os.path.splitext(filename)[0] + ".txt"
    output_path = os.path.join(input_folder, txt_name)

    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 좌표 저장할 리스트 초기화
        lines = [] #기본선들
        polylines = [] #폴리건 선들
        stair_points = [] #계단 좌표들
        door_points = [] #문 좌표들
        hole_points = [] #뚫린 바닥 좌표들

        # DXF 파일에서 Line, Polyline, Point 좌표 추출
        for entity in msp.query("LWPOLYLINE POLYLINE LINE POINT"):
            if entity.dxftype() == "LINE":
                start = entity.dxf.start
                end = entity.dxf.end
                lines.append(f"{start.x},{start.y},{end.x},{end.y}")

            elif entity.dxftype() == "LWPOLYLINE":
                points = [(p[0], p[1]) for p in entity]
                polylines.append(points)

            elif entity.dxftype() == "POLYLINE":
                poly_points = [v.dxf.location for v in entity.vertices]
                polylines.append([(p.x, p.y) for p in poly_points])

            elif entity.dxftype() == "POINT":
                layer = entity.dxf.layer.lower()
                point = entity.dxf.location
                if "stair" in layer:
                    stair_points.append(f"{point.x},{point.y}")
                elif "door" in layer:
                    door_points.append(f"{point.x},{point.y}")
                elif "hole" in layer:
                    hole_points.append(f"{point.x},{point.y}")

        # 좌표 데이터를 텍스트 파일로 저장
        with open(output_path, "w") as f:
            f.write("LINES\n")
            f.write("\n".join(lines) + "\n")
            f.write("POLYLINES\n")
            for poly in polylines:
                f.write(",".join([f"{p[0]},{p[1]}" for p in poly]) + "\n")
            f.write("STAIRS\n")
            f.write("\n".join(stair_points) + "\n")
            f.write("DOORS\n")
            f.write("\n".join(door_points) + "\n")
            f.write("HOLES\n")
            f.write("\n".join(hole_points) + "\n")

        print(f"✅ {filename} 처리 완료 → {txt_name}")

    except Exception as e:
        print(f"❌ {filename} 처리 실패: {e}")
