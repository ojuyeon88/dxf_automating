import ezdxf

# === 사용자 입력 ===
dxf_path = "files/dxf/files/dxf/1F-autosync.dxf"  # DXF 파일 경로
output_path = "converted_coords.txt"  # 저장할 좌표 파일
reference_point = (31500, 18500)  # ⊕ 마크 중심 좌표 (mm 단위)
unit_scale = 1 / 1000  # mm → m 변환

# === DXF 읽기 ===
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# === 결과 저장 리스트 ===
converted_lines = []

# === LINE 객체 처리 ===
for entity in msp.query("LINE"):
    start = entity.dxf.start
    end = entity.dxf.end

    # 기준점 기준으로 이동 + 단위 환산
    x1 = (start.x - reference_point[0]) * unit_scale
    y1 = (start.y - reference_point[1]) * unit_scale
    x2 = (end.x - reference_point[0]) * unit_scale
    y2 = (end.y - reference_point[1]) * unit_scale

    converted_lines.append(f"{x1:.3f},{y1:.3f},{x2:.3f},{y2:.3f}")

# === LWPOLYLINE 객체 처리 ===
for entity in msp.query("LWPOLYLINE"):
    points = entity.get_points()
    converted_points = [
        ((x - reference_point[0]) * unit_scale, (y - reference_point[1]) * unit_scale)
        for x, y, *_ in points
    ]
    coord_str = ",".join([f"{x:.3f},{y:.3f}" for x, y in converted_points])
    converted_lines.append(coord_str)

# === 결과 저장 ===
with open(output_path, "w") as f:
    for line in converted_lines:
        f.write(line + "\n")

print(f"좌표 변환 및 기준점 보정 완료: {output_path}")
