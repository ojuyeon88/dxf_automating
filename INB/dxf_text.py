import pandas as pd
import os
import re

try:
    import ezdxf
except ImportError:
    print("ezdxf 라이브러리가 설치되어 있지 않습니다. 다음 명령으로 설치하세요:")
    print("pip install ezdxf")
    exit()

try:
    import pandas as pd
except ImportError:
    print("pandas 라이브러리가 설치되어 있지 않습니다. 다음 명령으로 설치하세요:")
    print("pip install pandas")
    exit()

def is_valid_poi_name(text):
    """
    주어진 텍스트가 네비게이션 POI 장소명으로 유효한지 판단합니다.
    - 순수 숫자, 콤마가 포함된 숫자, 호실 번호, 축 라벨, 도면 참조 코드, 짧은 특수문자열 제외.
    - 사람 이름 제외.
    - 대괄호 포함 도면 개요, 축척 정보 제외.
    - 장소명을 포함하는 한글/영문 텍스트를 우선적으로 통과시킵니다.
    """
    if not isinstance(text, str):
        return False

    cleaned_text = text.strip()

    if not cleaned_text: # 비어 있거나 공백만 있는 경우
        return False

    # 1. 숫자, 콤마가 포함된 숫자, 호실 번호 패턴 제거
    # "17,900" -> "17900", "2,500 2,500" -> "25002500", "164" -> "164", "101B" -> "101B"
    numeric_or_room_check_text = cleaned_text.replace(",", "").replace(" ", "")
    
    # 순수 숫자 (예: "164") 또는 숫자 뒤에 알파벳이 오는 호실 (예: "101B", "995B")
    # ^\d+$ : 순수 숫자 (164)
    # ^\d+[A-Za-z]$ : 숫자+알파벳 (101B)
    # ^[A-Za-z]\d+$ : 알파벳+숫자 (B201)
    if re.fullmatch(r'^\d+$', numeric_or_room_check_text) or \
       re.fullmatch(r'^\d+[A-Za-z]$', numeric_or_room_check_text) or \
       re.fullmatch(r'^[A-Za-z]\d+$', numeric_or_room_check_text):
        return False
    
    # 실수 포함 (예: "123.45")
    try:
        float(numeric_or_room_check_text)
        return False
    except ValueError:
        pass

    # 2. 축 라벨, 도면 참조 코드, 짧은 특수문자열 필터링
    # (예: "X5", "Y10", "X5-", "A2-201", "B-01", "-", "---", "A")
    # ^[XY]\d+[-_]?$  -> X나 Y로 시작하고 숫자가 1개 이상 오며, 선택적으로 하이픈이나 언더스코어가 오는 패턴 (X5, Y10)
    # ^[A-Z]\d+-\d+$ -> 알파벳으로 시작하고 숫자, 하이픈, 숫자가 오는 패턴 (A2-201)
    # ^[A-Z]-\d+$ -> 알파벳-하이픈-숫자 (B-01)
    # ^[A-Z]$ -> 단일 알파벳 (A)
    if re.fullmatch(r'^[XY]\d+[-_]?$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]\d+-\d+$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]-\d+$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]$', cleaned_text) or \
       (len(cleaned_text) <= 3 and not re.search(r'[가-힣a-zA-Z0-9]', cleaned_text)): # 짧은 특수문자 (-, --)
        return False

    # 3. 사람 이름 필터링 (한글 이름에 특화)
    # 2~4자 한글 (일반적인 이름 길이), 직책 등이 없는 순수 이름 필터링
    if re.fullmatch(r'^[가-힣]{2,4}$', cleaned_text):
        # 제외할 가능성이 있는 이름 패턴 (예: "김철수", "이영희", "송용남")
        # 실제 장소명과 겹칠 수 있으므로, 신중하게 적용해야 합니다.
        # 예외: '사무실', '강의실' 등은 3글자 한글이지만 POI.
        # 이 필터링은 너무 공격적일 수 있으므로, 필요하다면 제외하거나 패턴을 더 정교하게 다듬어야 합니다.
        # 현재는 '교수연구실' 등 장소명에 직책이 붙은 경우는 통과, 순수 이름은 제외하는 방향.
        return False # 사람 이름으로 판단하여 POI에서 제외

    # 4. 도면 정보 및 기타 POI가 아닌 정보 필터링
    if cleaned_text.startswith("[") and cleaned_text.endswith("]"): # 대괄호로 둘러싸인 텍스트 (예: "[지하3층,지상7층]")
        return False
    if cleaned_text.startswith("축척="): # 축척 정보 (예: "축척=A1:1/200, A3:1/400")
        return False
    
    # 5. 최종 POI 장소명 기준: 위에 모든 필터링을 통과하고 한글/영문이 포함된 경우
    if re.search(r'[가-힣a-zA-Z]', cleaned_text):
        return True

    return False

def extract_filtered_poi_data(dxf_filepath):
    """
    DXF 파일에서 유효한 POI 장소명만 추출하고, 좌표를 100으로 나눕니다.
    """
    final_pois = []

    try:
        doc = ezdxf.readfile(dxf_filepath)
        msp = doc.modelspace()

        for entity in msp:
            text_content = ""
            insert_point = None

            if entity.dxftype() == 'TEXT':
                try:
                    text_content = entity.dxf.text
                    insert_point = entity.dxf.insert
                except AttributeError:
                    continue
            elif entity.dxftype() == 'MTEXT':
                try:
                    text_content = entity.dxf.text
                    insert_point = entity.dxf.insert
                except AttributeError:
                    continue
            
            if text_content and insert_point:
                if is_valid_poi_name(text_content):
                    # 좌표값을 100으로 나눔
                    x = insert_point[0] / 100.0
                    y = insert_point[1] / 100.0
                    z = insert_point[2] / 100.0
                    final_pois.append({'Text': text_content, 'X': x, 'Y': y, 'Z': z})

    except ezdxf.DXFError as e:
        print(f"오류: '{os.path.basename(dxf_filepath)}' DXF 파일을 읽는 중 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"오류: '{os.path.basename(dxf_filepath)}' 처리 중 예기치 않은 오류가 발생했습니다: {e}")
    return final_pois

if __name__ == "__main__":
    # 대상 DXF 파일들이 있는 폴더 경로
    dxf_folder_path = r"C:\Users\user\Documents\GitHub\dxf_automating\INB\dxf"
    # CSV 파일을 저장할 폴더 경로 (INB 폴더)
    output_csv_folder_path = r"C:\Users\user\Documents\GitHub\dxf_automating\INB"

    # 출력 폴더가 존재하지 않으면 생성
    if not os.path.exists(output_csv_folder_path):
        os.makedirs(output_csv_folder_path)
        print(f"출력 폴더 '{output_csv_folder_path}'를 생성했습니다.")

    if not os.path.exists(dxf_folder_path):
        print(f"오류: DXF 파일 폴더 '{dxf_folder_path}'를 찾을 수 없습니다.")
    else:
        print(f"'{dxf_folder_path}' 폴더의 DXF 파일들을 처리합니다...")
        processed_count = 0
        for filename in os.listdir(dxf_folder_path):
            if filename.lower().endswith(".dxf"):
                dxf_full_path = os.path.join(dxf_folder_path, filename)
                print(f"'{filename}' 파일 처리 중...")

                poi_data = extract_filtered_poi_data(dxf_full_path)

                if poi_data:
                    df = pd.DataFrame(poi_data)
                    csv_filename = os.path.splitext(filename)[0] + "_poi.csv" # 최종 필터링된 POI를 나타내기 위해 접미사 변경
                    output_csv_full_path = os.path.join(output_csv_folder_path, csv_filename)
                    try:
                        df.to_csv(output_csv_full_path, index=False, encoding='utf-8-sig')
                        print(f"-> 최종 필터링된 POI 장소명 데이터가 '{os.path.basename(output_csv_full_path)}'에 성공적으로 저장되었습니다.")
                        processed_count += 1
                    except Exception as e:
                        print(f"오류: '{os.path.basename(output_csv_full_path)}' CSV 파일을 저장하는 중 오류가 발생했습니다: {e}")
                else:
                    print(f"-> '{filename}' 파일에서 유효한 POI 장소명을 찾을 수 없거나 처리 중 오류가 발생했습니다.")
        
        print(f"\n총 {processed_count}개의 DXF 파일이 성공적으로 처리되었습니다.")
        if processed_count == 0:
            print("처리된 DXF 파일이 없습니다. 경로를 확인하거나 파일에 유효한 POI 장소명 엔티티가 있는지 확인하세요.")