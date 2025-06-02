from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
import os
from datetime import datetime
from sqlalchemy import inspect

# 기존 DB 삭제
'''
if os.path.exists("course_recommender.db"):
    os.remove("course_recommender.db")
    print("기존 course_recommender.db 삭제 완료")
'''
# 데이터베이스 설정
'''
DATABASE_URL = "sqlite:///course_recommender.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
'''

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'course_recommender.db')}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# 모델 정의
class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    subject_code = Column(String(20))  # 과목코드
    subject_name = Column(String(200))  # 교과목명 (항목_18)
    class_number = Column(String(20))  # 분반
    professor = Column(String(100))  # 담당교수 (항목_9)
    college = Column(String(100))  # 단과대학
    major = Column(String(100))  # 학과
    course_type = Column(String(50))  # 이수구분 (항목_5)
    year = Column(String(20))  # 학년
    semester = Column(String(20))  # 학기

    syllabus_id = Column(Integer, ForeignKey("syllabus.id"))
    syllabus = relationship("Syllabus", back_populates="course")
    weekly_plans = relationship("WeeklyPlan", back_populates="course")

class Syllabus(Base):
    __tablename__ = "syllabus"

    id = Column(Integer, primary_key=True)
    basic_info = Column(Text)  # 기본 정보 (JSON 형식)
    professor_info = Column(Text)  # 교수 정보 (JSON 형식)
    course_info = Column(Text)  # 강의 정보 (JSON 형식)
    evaluation = Column(Text)  # 평가 방법 (JSON 형식)
    textbook_info = Column(Text)  # 교재 정보 (JSON 형식)
    core_competencies = Column(Text)  # 핵심역량 (JSON 형식)

    course = relationship("Course", back_populates="syllabus")

class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"))
    week_number = Column(Integer)
    topic = Column(String(200))
    content = Column(Text)

    # 관계 설정
    course = relationship("Course", back_populates="weekly_plans")

def init_db():
    """데이터베이스 초기화"""
    Base.metadata.drop_all(engine)  # 기존 테이블 제거 (안전)
    Base.metadata.create_all(engine)  # 테이블 생성

def process_json_files(json_dir):
    """폴더 내의 모든 JSON 파일을 처리하여 데이터베이스에 저장"""
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
            total_files = len(json_files)

            print(f"총 {total_files}개의 JSON 파일을 처리합니다...")

            for i, json_file in enumerate(json_files, 1):
                file_path = os.path.join(json_dir, json_file)
                print(f"\n[{i}/{total_files}] {json_file} 처리 중...")

                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                basic_info = data.get("기본정보", {})
                evaluation_info = data.get("평가방법", {})

                print(f"기본 정보: {basic_info.get('교과목명', '')} (교과목명)")
                print(f"담당교수: {basic_info.get('담당교수명', '')}")
                print(f"이수구분: {basic_info.get('교과목 구분', '')}")

                course = Course(
                    subject_code=basic_info.get("교과목 코드", ""),
                    subject_name=basic_info.get("교과목명", ""),
                    class_number=basic_info.get("분반", ""),
                    professor=basic_info.get("담당교수명", ""),
                    #college="",  # 단과대학이 따로 없으면 빈값 처리
                    major=basic_info.get("학과/학년", "").split()[0] if "학과/학년" in basic_info else "",
                    course_type=basic_info.get("교과목 구분", ""),
                    year=basic_info.get("학과/학년", "").split()[-1] if "학과/학년" in basic_info else "",
                    #semester=""  # 필요시 추가
                )

                syllabus = Syllabus(
                    basic_info=json.dumps({
                        "email": basic_info.get("E-mail", ""),
                        "phone": basic_info.get("연락처", ""),
                        "subject_name": basic_info.get("교과목명", ""),
                        "professor": basic_info.get("담당교수명", ""),
                        "major_year": basic_info.get("학과/학년", ""),
                        "course_objective": basic_info.get("수업목표", "")
                    }, ensure_ascii=False),
                    professor_info=json.dumps({
                        "consultation_time": basic_info.get("상담가능시간", "")
                    }, ensure_ascii=False),
                    course_info=json.dumps({
                        "classroom": basic_info.get("강의실", ""),
                        "schedule": basic_info.get("요일/시간", "")
                    }, ensure_ascii=False),
                    evaluation=json.dumps({
                        "a_ratio": evaluation_info.get("100", ""),
                        "evaluation_method": evaluation_info.get("절대평가 기준", ""),
                        "midterm": basic_info.get("25%", ""),
                        "final": basic_info.get("20%", ""),
                        "attendance": basic_info.get("5%", ""),
                        "assignment": basic_info.get("0%", "")
                    }, ensure_ascii=False),
                    textbook_info=json.dumps({
                        "main_textbook": basic_info.get("주교재", ""),
                        "reference": basic_info.get("참고자료", "")
                    }, ensure_ascii=False),
                    core_competencies=json.dumps({}, ensure_ascii=False)
                )

                course.syllabus = syllabus
                session.add(course)
                print(f"강의 정보 저장 완료: {course.subject_name}")

            session.commit()
            print("\n모든 데이터 처리 완료")

        except Exception as e:
            session.rollback()
            print(f"데이터 처리 중 오류 발생: {str(e)}")
            raise
        finally:
            session.close()

    except Exception as e:
        print(f"파일 처리 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    # DB 초기화
    init_db()

    # JSON 파일이 있는 폴더 경로
    json_dir = "data/syllabi"

    # 폴더 존재 여부 확인
    if not os.path.exists(json_dir):
        print(f"오류: {json_dir} 폴더를 찾을 수 없습니다.")
        print("크롤링한 데이터가 저장된 폴더의 경로를 확인해주세요.")
        exit(1)

    # 데이터 처리
    process_json_files(json_dir)

    inspector = inspect(engine)
    print("생성된 테이블 목록:", inspector.get_table_names())