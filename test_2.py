import requests
import xml.etree.ElementTree as ET
import os
import time
from datetime import datetime
import re
import json
import base64
from bs4 import BeautifulSoup  # 설치 필요: pip install beautifulsoup4

# 저장할 디렉토리 생성
save_dir = os.path.join(os.path.expanduser("~"), "Downloads", "syllabi")
os.makedirs(save_dir, exist_ok=True)

# 디버깅 모드 설정
DEBUG = True


# 시간 기반 키 생성
def generate_key():
    current_time = datetime.now().strftime("%Y%m%d%H%M%S%f")[:19]
    return f"{current_time}_{os.urandom(4).hex()}"


# 응답 저장 함수
def save_response(response, filename):
    if DEBUG:
        path = os.path.join(save_dir, filename)
        try:
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"응답 저장됨: {path}")
        except Exception as e:
            print(f"응답 저장 실패: {e}")


# 강의 목록 가져오기 함수
def fetch_course_list(year, semester_code, entrance_year="2017"):
    # 강의 목록 조회 URL
    url = "https://oasis.jbnu.ac.kr/uni/uni/cour/less/findLessSubjtTblInq.action"

    # 헤더 설정
    headers = {
        "accept": "application/xml, text/xml, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "text/xml",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "Referer": "https://oasis.jbnu.ac.kr/jbnu/sugang/sbjt/sbjt.html",
    }

    # 쿠키 설정
    cookies = {
        "WMONID": "5s6kcMzB_VZ",
        "gvYy": entrance_year,
        "gvShtm": semester_code,
    }

    # 요청 본문 XML 구성 - 공과대학 학부전공 필터링
    xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Root xmlns="http://www.nexacroplatform.com/platform/dataset">
    <Parameters>
        <Parameter id="JSESSIONID" />
        <Parameter id="gvYy">{entrance_year}</Parameter>
        <Parameter id="gvShtm">{semester_code}</Parameter>
        <Parameter id="gvRechPrjtNo" />
        <Parameter id="gvRechDutyr" />
        <Parameter id="WMONID">5s6kcMzB_VZ</Parameter>
        <Parameter id="yy">{year}</Parameter>
        <Parameter id="shtm">{semester_code}</Parameter>
        <Parameter id="fg">1</Parameter>
        <Parameter id="value1">3000000001</Parameter>
        <Parameter id="value2" />
        <Parameter id="value3" />
        <Parameter id="sbjtNm" />
        <Parameter id="profNm" />
        <Parameter id="openLectFg" />
        <Parameter id="entrYy">{entrance_year}</Parameter>
        <Parameter id="sType">EXT1</Parameter>
    </Parameters>
</Root>"""

    try:
        print("강의 목록 요청 보내는 중...")
        if DEBUG:
            print(f"요청 URL: {url}")
            print(f"요청 헤더: {json.dumps(headers, indent=2)}")
            print(f"요청 본문: {xml_body}")

        # 요청 보내기
        response = requests.post(url, headers=headers, cookies=cookies, data=xml_body, timeout=30)

        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")

        # 응답 저장
        save_response(response, "course_list_response.xml")

        if response.status_code == 200:
            try:
                response_text = response.text
                print(f"응답 길이: {len(response_text)} 바이트")
                print(f"응답 미리보기: {response_text[:200]}...")

                # XML 파싱
                root = ET.fromstring(response_text)

                # 네임스페이스 확인 및 설정
                ns = {"nx": "http://www.nexacro.com/platform/dataset"}

                print(f"네임스페이스: {ns}")

                # 강의 데이터 추출
                rows = []

                # Dataset 요소 찾기
                datasets = root.findall(".//nx:Dataset", ns)
                print(f"Dataset 요소 수: {len(datasets)}")

                for dataset in datasets:
                    ds_id = dataset.get("id", "")
                    print(f"Dataset ID: {ds_id}")

                    # GRD_COUR001 ID를 가진 Dataset 확인
                    if ds_id == "GRD_COUR001":
                        # 행(Row) 데이터 추출
                        rows_elem = dataset.find(".//nx:Rows", ns)

                        if rows_elem is not None:
                            row_elems = rows_elem.findall(".//nx:Row", ns)
                            print(f"Row 요소 수: {len(row_elems)}")

                            for row in row_elems:
                                course_data = {}

                                # 각 컬럼 데이터 추출
                                for col in row:
                                    col_id = col.get("id", "")
                                    col_value = col.text if col.text else ""
                                    course_data[col_id] = col_value

                                # 필요한 필드 추출
                                subject_code = course_data.get("SBJTCD", "")
                                class_number = course_data.get("CLSS", "1")
                                subject_name = course_data.get("SBJTNM", "")
                                college = course_data.get("COLG_NM", "")  # 단과대학
                                major = course_data.get("MAJR_NM", "")  # 학과
                                course_type = course_data.get("SBJT_DIV_NM", "")  # 이수구분

                                if subject_code:
                                    rows.append({
                                        "year": year,
                                        "semester_code": semester_code,
                                        "subject_code": subject_code,
                                        "class_number": class_number,
                                        "subject_name": subject_name,
                                        "college": college,
                                        "major": major,
                                        "course_type": course_type
                                    })

                print(f"총 {len(rows)}개 강의 목록을 가져왔습니다.")

                # 데이터가 없는 경우 샘플 강의 코드로 계속
                if not rows:
                    print("강의 목록이 비어있어 샘플 데이터를 추가합니다.")
                    # 테스트용 샘플 과목 추가
                    sample_courses = [
                        {
                            "year": year,
                            "semester_code": semester_code,
                            "subject_code": "0000128578",
                            "class_number": "1",
                            "subject_name": "샘플 강의 1",
                            "college": "공과대학",
                            "major": "컴퓨터공학부",
                            "course_type": "학부전공"
                        }
                    ]
                    rows.extend(sample_courses)

                return rows

            except Exception as e:
                print(f"XML 파싱 중 오류: {e}")
                import traceback
                traceback.print_exc()
                return []
        else:
            print(f"강의 목록 가져오기 실패: 상태 코드 {response.status_code}")
            return []

    except Exception as e:
        print(f"강의 목록 요청 중 오류 발생: {e}")
        return []


# UbiReport PDF 생성 요청 함수
def generate_pdf_from_ubireport(report_key):
    """UbiReport에서 PDF 생성 요청"""
    try:
        url = "https://oasis.jbnu.ac.kr/com/UbiGateway"

        # PDF 내보내기 요청 헤더
        headers = {
            "accept": "*/*",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "Referer": "https://oasis.jbnu.ac.kr/jbnu/sugang/sbjt/sbjt.html",
        }

        # PDF 내보내기 요청 본문
        body = f"reqtype=1&exportid=PDF&key={report_key}"

        # 요청 보내기
        response = requests.post(url, headers=headers, data=body, timeout=30)

        print(f"PDF 내보내기 응답 상태 코드: {response.status_code}")
        print(f"PDF 내보내기 응답 헤더: {dict(response.headers)}")

        # 응답 저장 (디버깅용)
        save_response(response, f"pdf_export_response_{report_key}.bin")

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                return response.content
            else:
                print(f"PDF가 아닌 응답 유형: {content_type}")
                return None
        else:
            print(f"PDF 내보내기 실패: 상태 코드 {response.status_code}")
            return None
    except Exception as e:
        print(f"PDF 생성 요청 중 오류: {e}")
        return None


# UbiReport 시작 함수 (3단계 과정)
def get_syllabus_pdf(year, semester_code, subject_code, class_number, key):
    """UbiReport 프로세스를 사용하여 강의계획서 PDF 생성 (3단계 과정)"""
    try:
        # 1단계: 초기 요청 (보고서 로드)
        print("1단계: 초기 UbiReport 요청 보내는 중...")

        url1 = "https://oasis.jbnu.ac.kr/com/UbiGateway"
        headers1 = {
            "accept": "*/*",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "Referer": "https://oasis.jbnu.ac.kr/jbnu/sugang/sbjt/sbjt.html",
        }

        body1 = (
            f"reqtype=0&imageid=&div=%5Bobject%20HTMLDivElement%5D&key={key}&"
            f"gatewayurl=https%3A%2F%2Foasis.jbnu.ac.kr%2Fcom%2FUbiGateway&printurl=&timeout=60000&"
            f"jrffile=uni%2Fcour%2Fplan%2FLectPlanPrn1.jrf&masterfilename=&resid=UBIAJAX&"
            f"arg=arg_yy%23{year}%23arg_shtm%23{semester_code}%23arg_sbjtCd%23{subject_code}%23arg_clss%23{class_number}%23"
            f"arg_pgmCd%23undefined%23&ismultireport=false&multicount=1&exportseq=&reporttitle=&sheetname=&"
            f"toolbar=true&resource=https%3A%2F%2Foasis.jbnu.ac.kr%2Fcom%2Fubireport%2Fajax%2Fjs4&"
            f"divid=ubiviewer_1&skin=standard&scale=140&userscale=0&isencrypt=false&bgcolor=%23f3f3f3&"
            f"bgimage=&flicking=false&scrollpage=true&isStreaming=true&issvg=false&direction=&language=ko&"
            f"printlimit=20&isexportchartimage=true&exceladjustpage=false&excelExportLineItem=false&"
            f"excelPrintPaperSize=&excelPrintfitWidth=&excelPrintfitHeight=&excelSheetPerReport=false&"
            f"excelSheetPerMasterPage=false&excelSheetPerPage=false&excelSkipMasterItem=false&streamdata=&"
            f"clienttype=nexacro&datasetinfos=&runtimedata=&isvoiceye=false&iswa=false&isredbc=false&"
            f"password=&drmdocnumber=&drmdocname=&drmpagenames=&hmlTableProtect=false&fontElement=&"
            f"daemonid=&userwidth=undefined&userheight=undefined"
        )

        response1 = requests.post(url1, headers=headers1, data=body1, timeout=30)
        print(f"1단계 응답 상태 코드: {response1.status_code}")
        save_response(response1, f"syllabus_step1_{key}.bin")

        if response1.status_code != 200:
            print("1단계 요청 실패")
            return None

        # 응답에서 exportseq 값 추출
        export_seq = response1.headers.get('exportseq', '')
        if not export_seq:
            print("exportseq 값을 찾을 수 없음")
            # XML에서 값 찾기 시도
            seq_match = re.search(r'<exportseq>(.*?)</exportseq>', response1.text, re.IGNORECASE)
            if seq_match:
                export_seq = seq_match.group(1).strip()
                print(f"XML에서 exportseq 값 찾음: {export_seq}")

        print(f"exportseq: {export_seq}")

        # 2단계: 보고서 준비 상태 확인 (선택적)
        time.sleep(1)  # 보고서 준비 대기

        # 3단계: PDF 내보내기 요청
        print("3단계: PDF 내보내기 요청 보내는 중...")
        url3 = "https://oasis.jbnu.ac.kr/com/UbiGateway"
        headers3 = {
            "accept": "*/*",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "Referer": "https://oasis.jbnu.ac.kr/jbnu/sugang/sbjt/sbjt.html",
        }

        # PDF 내보내기 파라미터
        body3 = f"reqtype=1&exportid=PDF&key={key}&gatewayurl=https%3A%2F%2Foasis.jbnu.ac.kr%2Fcom%2FUbiGateway"

        if export_seq:
            body3 += f"&exportseq={export_seq}"

        response3 = requests.post(url3, headers=headers3, data=body3, timeout=30)
        print(f"3단계 응답 상태 코드: {response3.status_code}")
        save_response(response3, f"syllabus_step3_{key}.bin")

        if response3.status_code == 200:
            content_type = response3.headers.get('Content-Type', '')
            print(f"3단계 응답 콘텐츠 유형: {content_type}")

            if 'application/pdf' in content_type:
                print("PDF 응답 성공!")
                return response3.content
            else:
                print("PDF가 아닌 응답 유형")
                # HTML 응답에서 PDF URL 찾기 시도
                try:
                    if 'text/html' in content_type or 'text/xml' in content_type:
                        soup = BeautifulSoup(response3.text, 'html.parser')
                        pdf_link = soup.find('a', href=re.compile(r'\.pdf'))
                        if pdf_link:
                            pdf_url = pdf_link['href']
                            print(f"HTML에서 PDF 링크 발견: {pdf_url}")
                            pdf_response = requests.get(pdf_url)
                            if pdf_response.status_code == 200:
                                return pdf_response.content
                except:
                    pass

                # 다른 방식으로 시도: 직접 PDF URL 구성
                try:
                    pdf_url = f"https://oasis.jbnu.ac.kr/com/UbiGateway?reqtype=1&exportid=PDF&key={key}"
                    print(f"직접 PDF URL 구성 시도: {pdf_url}")
                    pdf_response = requests.get(pdf_url)
                    if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type',
                                                                                                         ''):
                        return pdf_response.content
                except:
                    pass

                return None
        else:
            print("3단계 요청 실패")
            return None

    except Exception as e:
        print(f"PDF 요청 과정 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_bin_file(bin_file_path):
    try:
        with open(bin_file_path, 'rb') as f:
            content = f.read()
        root = ET.fromstring(content)

        syllabus_data = {
            "기본정보": {},
            "평가방법": {},
            "핵심역량": {}
        }
        current_section = "기본정보"

        # 1. 모든 Item을 (y, x, text) 튜플로 추출
        items = []
        for item in root.findall('.//Item'):
            if 'classname' in item.attrib and item.attrib['classname'] == 'UbiTextItem':
                text_elem = item.find('.//Text')
                if text_elem is not None and text_elem.text:
                    text = text_elem.text.strip()
                    x = int(item.attrib.get('x', 0))
                    y = int(item.attrib.get('y', 0))
                    items.append((y, x, text))

        # 2. y값(행) 기준으로 그룹핑 (오차 허용)
        from collections import defaultdict
        row_dict = defaultdict(list)
        y_threshold = 3  # y좌표가 3px 이내면 같은 행으로 간주
        sorted_items = sorted(items)
        prev_y = None
        group_y = None
        for y, x, text in sorted_items:
            if prev_y is None or abs(y - prev_y) > y_threshold:
                group_y = y
            row_dict[group_y].append((x, text))
            prev_y = y

        # 3. 각 행을 x값 오름차순으로 정렬 후 섹션별로 저장
        rows_by_y = [sorted(row) for row in row_dict.values()]
        section_rows = []
        for row in rows_by_y:
            texts = [text for x, text in row]
            section_rows.append(texts)

        def is_percent(val):
            return bool(re.match(r'^[0-9]+%$', val.strip()))

        def is_all_percent(row):
            return all(is_percent(cell) for cell in row if cell.strip())

        def is_all_korean(row):
            return all(re.match(r'^[가-힣/()]+$', cell.strip()) for cell in row if cell.strip())

        i = 0
        prev_row = None
        while i < len(section_rows):
            row = section_rows[i]
            # 섹션 구분
            if any(s in row for s in ["교수정보", "강의정보", "평가방법", "교재정보", "핵심역량"]):
                for s in ["교수정보", "강의정보", "평가방법", "교재정보", "핵심역량"]:
                    if s in row:
                        current_section = s
                        break
                # '평가방법' 표 구조 매핑 (한 행에 key-value 번갈아 있음)
                if current_section == "평가방법":
                    for j in range(0, len(row) - 1, 2):
                        key = row[j]
                        value = row[j + 1]
                        if key != "평가방법":
                            syllabus_data[current_section][key] = value
                    i += 1
                    prev_row = row
                    continue
            # '기본정보' 섹션에서 평가계획 표가 들어온 경우 분리 (다양한 케이스 처리)
            if current_section == "기본정보":
                if any("평가계획" in cell for cell in row):
                    # 다음 행이 존재하고, 현재 행이 항목명, 다음 행이 %면 zip 매핑
                    if i + 1 < len(section_rows) and is_all_korean(row) and is_all_percent(section_rows[i + 1]):
                        keys = row
                        values = section_rows[i + 1]
                        min_len = min(len(keys), len(values))
                        for k, v in zip(keys[:min_len], values[:min_len]):
                            if "평가계획" not in k:
                                syllabus_data["평가방법"][k] = v
                        i += 2
                        prev_row = row
                        continue
                    # 한 행에 key-value 번갈아 있으면 짝수/홀수 매핑
                    elif any(is_percent(cell) for cell in row) and any(
                            re.match(r'^[가-힣/()]+$', cell.strip()) for cell in row):
                        for j in range(0, len(row) - 1, 2):
                            k, v = row[j], row[j + 1]
                            if is_percent(v):
                                syllabus_data["평가방법"][k] = v
                        i += 1
                        prev_row = row
                        continue
                    # 한 행에 값만 있으면 이전 행과 zip 매핑
                    elif is_all_percent(row) and prev_row and is_all_korean(prev_row):
                        keys = prev_row
                        values = row
                        min_len = min(len(keys), len(values))
                        for k, v in zip(keys[:min_len], values[:min_len]):
                            if "평가계획" not in k:
                                syllabus_data["평가방법"][k] = v
                        i += 1
                        prev_row = row
                        continue
            # 일반 key-value 매핑 (2개씩)
            j = 0
            while j + 1 < len(row):
                key = row[j]
                value = row[j + 1]
                if key not in ["교수정보", "강의정보", "평가방법", "교재정보", "핵심역량"] and not (
                        current_section == "기본정보" and "평가계획" in key):
                    syllabus_data[current_section][key] = value
                j += 2
            prev_row = row
            i += 1

        # 세로형 평가계획 표 우선 처리 (보정)
        for row in rows_by_y:
            row = sorted(row)  # x값 기준 정렬
            if len(row) > 3 and '평가계획' in row[0][1]:
                for j in range(1, len(row) - 1, 2):
                    key = row[j][1]
                    value = row[j + 1][1]
                    syllabus_data['평가방법'][key] = value
            elif len(row) > 1 and '평가참고사항' in row[0][1]:
                syllabus_data['평가방법']['평가참고사항'] = row[1][1]

        return syllabus_data
    except Exception as e:
        print(f"파일 파싱 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_as_json(data, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON 파일 저장 완료: {output_path}")
        return True
    except Exception as e:
        print(f"JSON 저장 중 오류: {e}")
        return False


# 강의계획서 다운로드 함수
def download_syllabus(year, semester_code, subject_code, class_number, subject_name=""):
    print(f"강의계획서 요청: {subject_name} ({subject_code}, 분반: {class_number})")

    # 과목명이 없는 경우 기본값 설정
    if not subject_name:
        subject_name = f"강의계획서_{subject_code}"

    # 안전한 파일명 생성 (특수문자 제거)
    safe_subject_name = re.sub(r'[\\/*?:"<>|]', "", subject_name)

    # 키 생성 (한 번만 생성하여 재사용)
    key = generate_key()

    # UbiReport 3단계 프로세스로 PDF 가져오기
    pdf_data = get_syllabus_pdf(year, semester_code, subject_code, class_number, key)

    # .bin 파일 파싱 (PDF 성공 여부와 관계없이)
    bin_file = f"syllabus_step1_{key}.bin"
    bin_path = os.path.join(save_dir, bin_file)

    if os.path.exists(bin_path):
        print(f".bin 파일 발견: {bin_path}")
        # .bin 파일 파싱
        parsed_data = parse_bin_file(bin_path)

        if parsed_data:
            # JSON으로 저장 (과목명_분반.json 형식)
            json_path = os.path.join(save_dir, f"{safe_subject_name}_{class_number}.json")
            if save_as_json(parsed_data, json_path):
                print(f"JSON 파일 저장 완료: {json_path}")
                return True

    if pdf_data:
        # PDF 저장 (과목명_분반.pdf 형식)
        pdf_path = os.path.join(save_dir, f"{safe_subject_name}_{class_number}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)
        print(f"PDF 파일 저장 완료: {pdf_path}")
        return True
    else:
        print("PDF 다운로드 실패")
        return False


# 메인 함수
def main():
    # 설정
    year = "2025"
    semester_code = "U211600010"  # 2025년 1학기 코드
    entrance_year = "2017"  # 입학년도 (필터링용)

    print("==== 강의계획서 다운로더 ====")
    print(f"기준 연도: {year}")
    print(f"학기 코드: {semester_code}")
    print(f"저장 경로: {save_dir}")
    print("===========================\n")

    # 1. 강의 목록 가져오기
    print(f"강의 목록을 가져오는 중...")
    courses = fetch_course_list(year, semester_code, entrance_year)

    if not courses:
        print("강의 목록을 가져오지 못했습니다.")
        return

    # 2. 강의 목록 저장 (참고용)
    courses_file = os.path.join(save_dir, "course_list.txt")
    with open(courses_file, "w", encoding="utf-8") as f:
        for course in courses:
            subject_name = course.get('subject_name', '이름 없음')
            subject_code = course['subject_code']
            class_number = course['class_number']
            f.write(f"{subject_code} - {subject_name} (분반: {class_number})\n")
    print(f"강의 목록 저장됨: {courses_file}")

    # 3. 각 강의별 강의계획서 다운로드
    print(f"\n총 {len(courses)}개 강의계획서 다운로드를 시작합니다.")

    success_count = 0
    for i, course in enumerate(courses):
        subject_code = course['subject_code']
        class_number = course['class_number']
        subject_name = course.get('subject_name', '이름 없음')

        print(f"\n[{i + 1}/{len(courses)}] 처리 중: {subject_name} ({subject_code}, 분반: {class_number})")

        success = download_syllabus(
            year,
            semester_code,
            subject_code,
            class_number,
            subject_name
        )

        if success:
            success_count += 1

        # 요청 간 지연 (서버 부하 방지)
        delay = 2 if i < 3 else 1.5  # 첫 몇 개는 조금 더 긴 지연
        print(f"{delay}초 대기 중...")
        time.sleep(delay)

    print(f"\n작업 완료. 총 {len(courses)}개 강의계획서 중 {success_count}개 다운로드 성공.")
    print(f"저장 위치: {save_dir}")


if __name__ == "__main__":
    main()