import json
import psycopg2
from datetime import datetime
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Alex',
    'user': 'xuehanshuo',
    'password': ''  # replace with your password
}


def migrate_programs_data():
    """Migrate programs.jsonl data to PostgreSQL"""

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Read JSONL file
        with open('data/curated/programs.jsonl', 'r', encoding='utf-8') as f:
            programs_data = []
            for line in f:
                if line.strip():  # Skip empty lines
                    programs_data.append(json.loads(line))

        print(f"Found {len(programs_data)} programs to migrate")

        # Insert each program
        for program in programs_data:
            # Convert date string to date object
            source_updated = None
            if program.get('source_updated'):
                source_updated = datetime.strptime(
                    program['source_updated'], '%Y-%m-%d').date()

            # Insert program data
            insert_query = """
            INSERT INTO programs (
                id, university, program, fields, type, campus, intakes,
                tuition_nzd_per_year, english_ielts, english_no_band_below,
                english_toefl_total, english_toefl_writing, duration_years,
                level, academic_reqs, other_reqs, url, source_updated, content
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            cursor.execute(insert_query, (
                program.get('id'),
                program.get('university'),
                program.get('program'),
                program.get('fields'),
                program.get('type'),
                program.get('campus'),
                program.get('intakes'),
                program.get('tuition_nzd_per_year'),
                program.get('english_ielts'),
                program.get('english_no_band_below'),
                program.get('english_toefl_total'),
                program.get('english_toefl_writing'),
                program.get('duration_years'),
                program.get('level'),
                program.get('academic_reqs'),
                program.get('other_reqs'),
                program.get('url'),
                source_updated,
                program.get('content')
            ))

            print(f"Inserted: {program.get('id')} - {program.get('program')}")

        # Commit changes
        conn.commit()
        print(f"\nSuccessfully migrated {len(programs_data)} programs!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate_programs_data()
