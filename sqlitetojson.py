import sqlite3
import json

# 데이터베이스 파일 경로
db_path = 'db.sqlite3'
json_output_path = 'db_export.json'

def export_sqlite_to_json(db_path, json_output_path):
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 데이터베이스의 모든 테이블 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        db_data = {}

        for table_name in tables:
            table = table_name[0]
            cursor.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            # 각 테이블 데이터를 JSON으로 변환
            table_data = [dict(zip(columns, row)) for row in rows]
            db_data[table] = table_data

        # JSON 파일로 저장
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(db_data, json_file, indent=4, ensure_ascii=False)

        print(f"✅ 데이터베이스가 성공적으로 {json_output_path}로 내보내졌습니다!")
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

# 스크립트 실행
export_sqlite_to_json(db_path, json_output_path)
