import sqlite3
conn = sqlite3.connect(r'D:\AI-Interview - Working\interview_logs.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM interview_logs;")
conn.commit()
conn.close()
print("All data cleared from logs table.")
