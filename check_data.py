from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_processor import Base, Course, Syllabus
import json
import os
from data_processor import Base  # 테이블 정의 포함


# 데이터베이스 설정
'''
DATABASE_URL = "sqlite:///course_recommender.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
'''
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'course_recommender.db')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)  # 테이블 생성

def print_course_info(course):
    """강의 정보 출력"""
    print("\n" + "="*50)
    print(f"교과목명: {course.subject_name}")
    print(f"담당교수: {course.professor}")
    print(f"이수구분: {course.course_type}")
    print(f"학과/학년: {course.major} {course.year}")
    print(f"분반: {course.class_number}")
    print(f"학기: {course.semester}")
    
    # 기본 정보
    basic_info = json.loads(course.syllabus.basic_info)
    print("\n[기본 정보]")
    print(f"이메일: {basic_info.get('email', '')}")
    print(f"연락처: {basic_info.get('phone', '')}")
    print(f"수업목표: {basic_info.get('course_objective', '')}")
    
    # 교수 정보
    professor_info = json.loads(course.syllabus.professor_info)
    print("\n[교수 정보]")
    print(f"연구실: {professor_info.get('office', '')}")
    print(f"상담가능시간: {professor_info.get('consultation_time', '')}")
    
    # 강의 정보
    course_info = json.loads(course.syllabus.course_info)
    print("\n[강의 정보]")
    print(f"강의실: {course_info.get('classroom', '')}")
    print(f"요일/시간: {course_info.get('schedule', '')}")
    
    # 평가 방법
    evaluation = json.loads(course.syllabus.evaluation)
    print("\n[평가 방법]")
    print(f"A 비율: {evaluation.get('a_ratio', '')}")
    print(f"평가방법: {evaluation.get('evaluation_method', '')}")
    print(f"중간고사: {evaluation.get('midterm', '')}")
    print(f"기말고사: {evaluation.get('final', '')}")
    print(f"출석: {evaluation.get('attendance', '')}")
    print(f"과제: {evaluation.get('assignment', '')}")
    print(f"기타: {evaluation.get('other', '')}")
    
    # 교재 정보
    textbook_info = json.loads(course.syllabus.textbook_info)
    print("\n[교재 정보]")
    print(f"주교재: {textbook_info.get('main_textbook', '')}")
    print(f"참고자료: {textbook_info.get('reference', '')}")
    
    # 핵심역량

    core_competencies = json.loads(course.syllabus.core_competencies)
    print("\n[핵심역량]")
    print(f"소통역량: {core_competencies.get('communication', '')}")
    print(f"창의역량: {core_competencies.get('creativity', '')}")
    print(f"인성역량: {core_competencies.get('personality', '')}")
    print(f"실무역량: {core_competencies.get('practical', '')}")
    print(f"도전역량: {core_competencies.get('challenge', '')}")
    print("="*50)


def main():
    session = Session()
    print("DB 위치:", os.path.join(BASE_DIR, 'course_recommender.db'))
    try:
        # 전체 강의 수 확인
        total_courses = session.query(Course).count()
        print(f"\n총 {total_courses}개의 강의가 저장되어 있습니다.")
        
        # 처음 5개 강의 정보 출력
        print("\n처음 5개 강의의 상세 정보:")
        courses = session.query(Course).limit(5).all()
        for course in courses:
            print_course_info(course)
            
    finally:
        session.close()

if __name__ == "__main__":
    main() 