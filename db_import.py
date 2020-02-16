import csv, sqlite3, os

print("** Exam question importer **")
database = input("[q] Location of database: ")
csv_to_import = input("[q] Location of csv: ")

if not os.path.isfile(database):
    print(f"[x] {database} is not valid")
    exit()

if not os.path.isfile(csv_to_import):
    print(f"[x] {csv_to_import} is not valid")
    exit()

print(f"[i] Open connection to [{database}]...", end=' ')
con = sqlite3.connect(database)
cur = con.cursor()
print("done")

print("[i] Deleting records...", end=' ')
cur.execute("DELETE FROM exam_questions")
con.commit()
print("done")


print(f"[i] Reading in csv data from [{csv_to_import}]")
with open(csv_to_import, 'r', encoding='utf-8') as fin:
    records = csv.DictReader(fin)
    to_db = [(
        i['id'],
        i['question_id'],
        i['question'],
        i['question_type'],
        i['question_images'],
        i['option_a'],
        i['option_b'],
        i['option_c'],
        i['option_d'],
        i['answer'],
        i['question_category']
    ) for i in records]

#remove the header record

insert_sql = '''
INSERT INTO exam_questions(
    id,
    question_id, 
    question,
    question_type, 
    question_images,
    option_a,
    option_b,
    option_c,
    option_d,
    answer,
    question_category) VALUES (?,?,?,?,?,?,?,?,?,?,?);
'''

print(f"[i] Insert {len(to_db)} records into table...", end=' ')
cur.executemany(insert_sql, to_db)
print("done")
con.close()
print("[i] Exit")