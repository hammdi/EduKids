"""
Quick fix script for registration issue
Run this with: python fix_registration.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from django.db import connection

print("=" * 60)
print("🔧 Fixing Registration Issue")
print("=" * 60)

# Check if birth_date column allows NULL
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(students_student)")
    columns = cursor.fetchall()
    
    print("\n📊 Current students_student table structure:")
    for col in columns:
        col_id, name, col_type, not_null, default_val, pk = col
        null_status = "NOT NULL" if not_null else "NULL OK"
        print(f"  - {name}: {col_type} ({null_status})")
    
    # Check if birth_date is NOT NULL
    birth_date_col = [col for col in columns if col[1] == 'birth_date']
    if birth_date_col and birth_date_col[0][3] == 1:  # not_null = 1
        print("\n❌ Problem found: birth_date is NOT NULL")
        print("\n🔧 Fixing: Making birth_date nullable...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # But first, let's try a simpler approach - just allow NULL temporarily
        try:
            # Get all data
            cursor.execute("SELECT * FROM students_student")
            existing_data = cursor.fetchall()
            
            # Drop and recreate with NULL allowed
            cursor.execute("DROP TABLE IF EXISTS students_student_backup")
            cursor.execute("""
                CREATE TABLE students_student_backup AS 
                SELECT * FROM students_student
            """)
            
            cursor.execute("DROP TABLE students_student")
            
            cursor.execute("""
                CREATE TABLE students_student (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    grade_level VARCHAR(3) NOT NULL,
                    birth_date DATE NULL,
                    learning_style VARCHAR(15) NOT NULL,
                    preferred_language VARCHAR(10) NOT NULL,
                    progress_score REAL NOT NULL,
                    total_points INTEGER NOT NULL,
                    current_level INTEGER NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES students_user(id)
                )
            """)
            
            # Restore data
            cursor.execute("""
                INSERT INTO students_student 
                SELECT * FROM students_student_backup
            """)
            
            cursor.execute("DROP TABLE students_student_backup")
            
            print("✅ Fixed! birth_date is now nullable")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n⚠️ Please run migrations instead:")
            print("   python manage.py makemigrations")
            print("   python manage.py migrate")
    else:
        print("\n✅ birth_date already allows NULL - database is OK!")
        print("\n💡 The error might be from an old Django process.")
        print("   Try restarting the Django server.")

print("\n" + "=" * 60)
print("✅ Done!")
print("=" * 60)
