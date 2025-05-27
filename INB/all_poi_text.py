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
    (이전과 동일한 필터링 로직)
    """
    if not isinstance(text, str):
        return False

    cleaned_text = text.strip()

    if not cleaned_text:
        return False

    # 1. 숫자, 콤마가 포함된 숫자, 호실 번호 패턴 제거
    numeric_or_room_check_text = cleaned_text.replace(",", "").replace(" ", "")
    
    if re.fullmatch(r'^\d+$', numeric_or_room_check_text) or \
       re.fullmatch(r'^\d+[A-Za-z]$', numeric_or_room_check_text) or \
       re.fullmatch(r'^[A-Za-z]\d+$', numeric_or_room_check_text):
        return False
    
    try:
        float(numeric_or_room_check_text)
        return False
    except ValueError:
        pass

    # 2. 축 라벨, 도면 참조 코드, 짧은 특수문자열 필터링
    if re.fullmatch(r'^[XY]\d+[-_]?$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]\d+-\d+$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]-\d+$', cleaned_text) or \
       re.fullmatch(r'^[A-Z]$', cleaned_text) or \
       (len(cleaned_text) <= 3 and not re.search(r'[가-힣a-zA-Z0-9]', cleaned_text)):
        return False

    # 3. 사람 이름 필터링 (2~4자 한글)
    if re.fullmatch(r'^[가-힣]{2,4}$', cleaned_text):
        return False 

    # 4. 도면 정보 및 기타 POI가 아닌 정보 필터링
    if (cleaned_text.startswith("[") and cleaned_text.endswith("]")) or \
       cleaned_text.startswith("축척="):
        return False
    
    # 5. 최종 POI 장소명 기준
    if re.search(r'[가-힣a-zA-Z]', cleaned_text):
        return True

    return False

def extract_all_filtered_poi_data(dxf_folder_path):
    """
    지정된 폴더의 모든 DXF 파일에서 유효한 POI 장소명을 추출하고,
    'Floor' 정보를 추가하여 단일 리스트로 반환합니다.
    좌표는 100으로 나눕니다.
    """
    all_combined_pois = []

    if not os.path.exists(dxf_folder_path):
        print(f"오류: DXF 파일 폴더 '{dxf_folder_path}'를 찾을 수 없습니다.")
        return []

    print(f"'{dxf_folder_path}' 폴더의 DXF 파일들을 처리합니다...")
    
    for filename in os.listdir(dxf_folder_path):
        if filename.lower().endswith(".dxf"):
            dxf_full_path = os.path.join(dxf_folder_path, filename)
            
            # 파일명에서 층 정보 추출 (예: "1F-autosync.dxf" -> "1F")
            floor_name = os.path.splitext(filename)[0].replace("-autosync", "").replace("_poi", "").replace("_filtered", "")
            # 필요에 따라 층 정보 추출 로직을 더 정교하게 만들 수 있습니다.
            # 예: "B1F-autosync.dxf" -> "B1F", "1F-autosync.dxf" -> "1F"
            # 여기서는 단순히 '_autosync', '_poi', '_filtered' 접미사를 제거합니다.

            print(f"'{filename}' (층: {floor_name}) 파일 처리 중...")

            try:
                doc = ezdxf.readfile(dxf_full_path)
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
                            all_combined_pois.append({'Text': text_content, 'X': x, 'Y': y, 'Z': z, 'Floor': floor_name})

            except ezdxf.DXFError as e:
                print(f"오류: '{os.path.basename(dxf_full_path)}' DXF 파일을 읽는 중 오류가 발생했습니다: {e}")
            except Exception as e:
                print(f"오류: '{os.path.basename(dxf_full_path)}' 처리 중 예기치 않은 오류가 발생했습니다: {e}")
    
    return all_combined_pois

if __name__ == "__main__":
    # 대상 DXF 파일들이 있는 폴더 경로
    dxf_folder_path = r"C:\Users\user\Documents\GitHub\dxf_automating\INB\dxf"
    # CSV 파일을 저장할 폴더 경로 (INB 폴더)
    output_csv_folder_path = r"C:\Users\user\Documents\GitHub\dxf_automating\INB"

    # 출력 폴더가 존재하지 않으면 생성
    if not os.path.exists(output_csv_folder_path):
        os.makedirs(output_csv_folder_path)
        print(f"출력 폴더 '{output_csv_folder_path}'를 생성했습니다.")

    # 모든 POI 데이터 추출
    combined_poi_data = extract_all_filtered_poi_data(dxf_folder_path)

    if combined_poi_data:
        df = pd.DataFrame(combined_poi_data)
        # 단일 CSV 파일로 저장
        output_csv_filename = "All_POIs_Scaled.csv"
        output_csv_full_path = os.path.join(output_csv_folder_path, output_csv_filename)
        try:
            df.to_csv(output_csv_full_path, index=False, encoding='utf-8-sig')
            print(f"\n모든 필터링된 POI 데이터가 '{output_csv_full_path}' 파일에 성공적으로 저장되었습니다.")
            print(f"총 {len(combined_poi_data)}개의 POI가 추출되었습니다.")
        except Exception as e:
            print(f"오류: '{output_csv_full_path}' CSV 파일을 저장하는 중 오류가 발생했습니다: {e}")
    else:
        print("\nDXF 파일에서 유효한 POI 장소명을 찾을 수 없거나 처리 중 오류가 발생했습니다.")
        print("CSV 파일이 생성되지 않았습니다.")