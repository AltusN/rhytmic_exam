import csv, sqlite3, os, sys

USAGE = """
The first paramters should be whether to [i]mport or [e]xport the exam questions
The second optional parameter should be where the db is (default is to look for it
in current dir named 'rhytmic.db'). 
"""

def import_questions(database:str, csv_to_import:str) -> None:

    temp_table = "temp_questions"
    exam_questions_table = "exam_questions"

    print(f"[i] Open connection to [{database}]...", end=" ")
    con = sqlite3.connect(database)
    cur = con.cursor()
    print("done")

    print("[i] Delete the tempory table if it exists...", end=" ")
    cur.execute(f"DROP TABLE IF EXISTS {temp_table}")
    print("done.")

    print("[i] Making backup of current exam questions...", end=" ")
    cur.execute(f"CREATE TABLE {temp_table} AS SELECT * FROM {exam_questions_table}")
    print("done.")
    
    print("[i] Deleting records...", end=" ")
    cur.execute("DELETE FROM exam_questions")
    con.commit()
    print("done.")

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
            i['question_category'],
            i['exam_level']
        ) for i in records]

    #remove the header record

    INSERT_SQL = '''
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
        question_category,
        exam_level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);
    '''

    print(f"[i] Insert {len(to_db)} records into table...", end=" ") 
    try:
        cur.executemany(INSERT_SQL, to_db)
        con.commit()
        print("done")
    except Exception as e:
        print(["[x] Somehting went wrong with the questions insert. rolling back", e])
        cur.execute(f"DELETE FROM {exam_questions_table}")
        cur.execute(f"INSERT INTO {exam_questions_table} SELECT * from {temp_table}")
        cur.execute(f"DROP TABLE {temp_table}")
        con.commit()
    finally:
        con.close()

    print("[i] Exit")

def export_questions(database:str, csv_out:str) -> None:

    exam_questions_table = "exam_questions"

    print(f"[i] Open connection to [{database}]...", end=" ")
    con = sqlite3.connect(database)
    cur = con.cursor()
    print("done.")
    
    print(f"[i] Reading records from {exam_questions_table} table...", end=" ")
    rs = cur.execute(f"SELECT * FROM {exam_questions_table}")
    print("done.")

    print("[i] Exporting questions to csv...", end=" ")

    with open(csv_out, 'w', newline='', encoding='utf-8') as f_out:
        csv_writer = csv.writer(f_out,)
        # write out the header
        csv_writer.writerow([i[0] for i in rs.description])
        # and then the data
        csv_writer.writerows(rs)

    print("done.")

    # Don't need the connectionn anymore
    con.close()

if __name__=="__main__":
    print(len(sys.argv))
    mode = None
    db = None
    csv_file = None

    if len(sys.argv) == 4:
        # only check the mode.. the rest is up to the user to have correct
        print(f"[i] All parameters specified: {sys.argv[1:]}")
        mode = sys.argv[1]
        db = sys.argv[2]
        csv_file = sys.argv[3]

        match mode:
            case "i":
                import_questions(db, csv_file)
            case "e":
                export_questions(db, csv_file)
            case _:
                print("[x] Could not determine the mode.")
    else:
        print("** Exam question import / export **")
        
        mode = input("[q] (i)mport or (e)xport? ")
        
        if mode.lower() not in ('i', 'e'):
            print(f'[x] Expected either i or e, not {mode}')
            exit()
        else:
            mode = mode.lower()

        db = input("[q] Location of database: ")

        if db is None or db == "":
            print("[i] No database location specified, using default .\\rhytmic.db")
            db = "rhytmic.db"
        elif not os.path.isfile(db):
            print("[x] Database location is not valid")
            exit()

        csv_file = input("[q] Location of csv: ")

        if mode == 'i' and not os.path.isfile(csv_file):
            print(f"[x] Invalid file location specided {csv_file}")
            exit()
        

        if mode == "e":
            export_questions(db, csv_file)
        else:
            import_questions(db, csv_file)
