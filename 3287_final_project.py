import sqlite3
from sqlite3 import Error
import random
import subprocess
import sys

#this will ensure that tabulate is loaded/pip installed for efficient table display
try:
    from tabulate import tabulate
except ImportError:
    subprocess.call([sys.executable, "-m", "pip", "install", 'tabulate'])
finally:
    from tabulate import tabulate
    
#set up a local db in current ram
def create_local_connection():
    """ create a database connection to a database that resides
        in the memory
    """
    #TODO Set up a more permanent db file residing in memory/google cloud's memory
    conn = None;
    success = 1;
    try:
        conn = sqlite3.connect(':memory:')
        print("sqlite version: ", sqlite3.version)
        print("storing database in RAM")
    except Error as e:
        print(e)
        success = 0;

    return conn, success;

#creates a db file in working directory
def create_localhost_connection():
    conn = None;
    success = 1
    localhost = r"hospital.db"
    try:
        conn = sqlite3.connect(localhost)
        #conn.autocommit = True
        print("sqlite version: ", sqlite3.version)
        print("Connecting to: ",localhost)
    except Error as e:
        print(e)
        success = 0
    return conn, success;

#Cannot easily be accomplished. SQlite works best on local databases. A flaw in the proposal for sure
def create_cloud_connection():
    cloudhost = "poop"
    conn = None;
    success = 1;
    try:
        conn = sqlite3.connect(cloudhost)
        print("sqlite version: ",sqlite3.version)
        print("Connecting to: ",cloudhost)
    except Error as e:
        print(e)
        success = 0
    return conn, success;

#creates table from passed in sql script
def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print("table successfully created")
    except Error as e:
        print(e)
        
#creates full schema        
def create_full_schema(conn):
    patients_schema = """CREATE TABLE Patients (
    patient_ID INT AUTO_INCREMENT,
    patient_name VARCHAR(45),
    DOB INT,
    disease_ID INT,
    UNIQUE (patient_name,DOB)
    PRIMARY KEY (patient_ID)
    );
    """
    samples_schema = """CREATE TABLE Samples (
    sample_ID INT,
    patient_ID INT,
    collection_date INT,
    freezer_ID INT,
    freezer_row INT,
    freezer_col INT,
    PRIMARY KEY (sample_ID),
    UNIQUE(freezer_ID,freezer_row,freezer_col)
    CONSTRAINT member_of
        FOREIGN KEY (patient_ID)
        REFERENCES Patients(patient_ID)
        ON DELETE CASCADE
    );"""
    diseases_schema = """CREATE TABLE Diseases (
    disease_ID INT,
    cancer_type VARCHAR(45),
    PRIMARY KEY (disease_ID)
    );"""
    mutations_schema = """CREATE TABLE Mutations (
    mutation_ID INT,
    mutation_name VARCHAR(45),
    PRIMARY KEY (mutation_ID)
    );"""
    freezers_schema = """CREATE TABLE Freezers (
    freezer_ID INT,
    freezer_name VARCHAR(45),
    PRIMARY KEY (freezer_ID)
    );"""
    patient_mutations_schema = """CREATE TABLE Patient_mutations (
    mutation_ID INT,
    disease_ID INT,
    patient_ID INT,
    UNIQUE(mutation_ID, disease_ID, patient_ID)
    );"""

    create_table(conn, patients_schema)
    create_table(conn, samples_schema)
    create_table(conn, diseases_schema)
    create_table(conn, mutations_schema)
    create_table(conn, freezers_schema)
    create_table(conn, patient_mutations_schema)

#gets user input from a predetermined menu and number of choices. only returns valid integer values
def get_user_input(menu_options,num_options):
    while(True):
        user_input = input(menu_options)
        try:
            user_intput = int(user_input)
            if (user_intput > 0 and user_intput <= num_options):
                return user_intput;
            else:
                print("Oops! that was not a valid option. Try again")
        except ValueError:
            print("Oops! That was not a valid number. Try again")
            
#adds disease into disease table, auto increments disease_ID            
def add_disease(conn, d_name):
    
    sql = "SELECT * FROM Diseases"
    c = conn.cursor()
    c.execute(sql)
    rows = c.fetchall()
    hits = 0
    for row in rows:
        hits = hits + 1
    hits = hits + 1
    sql = ''' INSERT INTO Diseases(disease_ID,cancer_type)
              VALUES(?,?)'''
    insert_command = (hits,d_name)
    c = conn.cursor()
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
    return hits

#checks if disease is in database, if so, returns disease ID, otherwise, inserts new disease into database and returns new disease_ID
def disease_lookup(conn,d_name):
    #d_name = input("What disease does the patient have?\n")
    sql = "SELECT disease_ID FROM Diseases WHERE cancer_type = ?"
    c = conn.cursor()
    c.execute(sql,(d_name,))
    d_id = c.fetchall()
    if (len(d_id) == 0):
        print("disease not in current database, adding disease")
        new_d_id = add_disease(conn, d_name)
        return new_d_id
    elif (len(d_id) == 1):
        print(d_id[0][0])
        return d_id[0][0]

#adds patient to database, gets name, date of birth, and disease, then generates a patient ID and inserts thsoe values into Patients table    
def add_patient(conn):
    p_name = input("what is the name of the patient\n")
    #hits = patient_lookup(conn,p_name)
    #if (hits > 0):
        #print("Patient already exists.")
        #return;
    while True:
        try:
            #TODO automatically generate patient_ID and get/populate disease_ID 
            #p_id = int(input("what is the patient_ID\n"))
            p_DOB = int(input("what is the DOB of the patient MMDDYYYY\n"))
            break
        except ValueError:
            print("Invalid format, try again")
    #test function
    p_id = generate_patient_ID(conn,p_name,p_DOB)
    
    d_name = input("What disease does the patient have?\n")
    d_id = disease_lookup(conn,d_name)
    
    sql = ''' INSERT INTO Patients(patient_ID,patient_name,DOB,disease_ID)
              VALUES(?,?,?,?)'''
    insert_command = (p_id,p_name,p_DOB,d_id)
    c = conn.cursor()
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
    return p_id

#gets new patient ID which will be the next available patient ID
def generate_patient_ID(conn,p_name,p_DOB):
    #check if patient already exists
    c = conn.cursor()
    sql = "SELECT patient_ID, patient_name FROM Patients WHERE patient_name = ? AND DOB = ?"
    c.execute(sql,(p_name,p_DOB))
    rows = c.fetchall()
    hits = 0
    for row in rows:
        hits = hits + 1
    if (hits == 0):
        sql = "SELECT MAX(patient_ID) FROM Patients"
        c.execute(sql)
        new_id = c.fetchall()
        return (new_id[0][0] + 1)
    
#gets and checks a user y/n input
def get_yn():
    while(True):
        user_in = input()
        if (user_in == "y" or user_in == "Y"):
            return True
        elif (user_in == "n" or user_in == "N"):
            return False
        else:
            print("invalid entry, please type 'y' or 'n'")
            
#finds next available sample_ID and returns that value
def generate_sample_ID(conn):
    sql = "SELECT MAX(sample_ID) FROM Samples"
    c = conn.cursor()
    c.execute(sql)
    #print(c.lastrowid)
    #return c.lastrowid
    new_id = c.fetchall()
    #print(new_id[0][0])
    return (new_id[0][0] + 1)

#determines if freezer is in database. If freezer exists, it returns freezer_ID, if freezer does not exist, it deletes the freezer
def freezer_lookup(conn):
    f_name = input("What is the name of the freezer?\n")
    sql = "SELECT freezer_ID FROM Freezers WHERE freezer_name = ?"
    c = conn.cursor()
    c.execute(sql,(f_name,))
    f_id = c.fetchall()
    if (len(f_id) == 0):
        print("Freezer not in database, adding freezer")
        new_f_id = add_freezer(conn, f_name)
        return new_f_id
    elif (len(f_id) == 1):
        return f_id[0][0]
    
#add freezer adds a freezer in the next available freezer ID (the primary key to freezers table)    
def add_freezer(conn, f_name):
    
    sql = "SELECT * FROM Freezers"
    c = conn.cursor()
    c.execute(sql)
    rows = c.fetchall()
    hits = 0
    for row in rows:
        hits = hits + 1
    hits = hits + 1
    sql = ''' INSERT INTO Freezers(freezer_ID,freezer_name)
              VALUES(?,?)'''
    insert_command = (hits,f_name)
    c = conn.cursor()
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
    return hits    

#gets or creates a new mutation ID. returns mutation ID if exists, otherwise returns the next available number
def mutation_lookup(conn):
    m_name = input("What is the name of the genetic mutation?\n")
    sql = "SELECT mutation_ID FROM Mutations WHERE mutation_name = ?"
    c = conn.cursor()
    c.execute(sql,(m_name,)) ################################
    m_id = c.fetchall()
    if (len(m_id) == 0):
        print("mutation not in database, adding mutation")
        new_m_id = add_mutation(conn,m_name)
        return new_m_id
    elif (len(m_id) == 1):
        return m_id[0][0]
    
#inserts a new mutation name and assigns it to the next available mutation ID
def add_mutation(conn,m_name):
    sql = "SELECT * FROM Mutations"
    c = conn.cursor()
    c.execute(sql)
    rows = c.fetchall()
    hits = 0
    for row in rows:
        hits = hits + 1
    hits = hits + 1
    sql = ''' INSERT INTO Mutations(mutation_ID,mutation_name)
              VALUES(?,?)'''
    insert_command = (hits,m_name)
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
    return hits

#add sample gets a sample_ID and gets storage location details adds it to samples table with selected patient's ID
def add_sample(conn,p_id):
    s_id = generate_sample_ID(conn)
    #add input checks
    #f_name = input("What is the name of the freezer where this is stored?\n")
    f_id = freezer_lookup(conn)
    while (True):
        try:
            col_date = int(input("what is the collection date MMDDYYYY\n"))
            break
        except ValueError:
            print("Oops, not valid date format")
    while (True):
        try:
            f_row = int(input("What row is the sample stored in?\n"))
            f_col = int(input("What column is the sample stored in?\n"))
            break
        except ValueError:
            print("Please enter integer values")
            
    sql = ''' INSERT INTO Samples(sample_ID,patient_ID,collection_date,freezer_ID,freezer_row,freezer_col)
              VALUES(?,?,?,?,?,?)'''
    insert_command = (s_id,p_id,col_date,f_id,f_row,f_col)
    c = conn.cursor()
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
    return

#patient lookup takes the conn, and a patient name, checks if patient(s) exist, if multiple, prompts user for date of birth
#if patient does not exist, allows user to add patient
def patient_lookup(conn,p_name):
    #p_name could also be an int
    try:
        p_name = int(p_name)
        sql = "SELECT patient_ID, patient_name FROM Patients WHERE patient_ID = ?"
    except ValueError:
        sql = "SELECT patient_ID, patient_name FROM Patients WHERE patient_name = ?"
    c = conn.cursor()
    c.execute(sql,(p_name,))
    rows = c.fetchall()
    hits = 0
    for row in rows:
        hits = hits + 1
        #print(row)
    print("hits: ",hits)
    if (hits == 0):
        print("patient not found in database, add patient?")
        yn_in = get_yn()
        if yn_in:
            p_id = add_patient(conn)
            print("add patient sample?")
            yn_in = get_yn()
            if yn_in:
                #print("this is where I would call add_sample()")
                add_sample(conn,p_id)
            #get_mutations()
        else:
            return
    elif (hits == 1):
        p_id = rows[0][0]
        #for row in rows:
            #print(row)
    elif (hits > 1):
        print("multiple patients have that name")
        while True:
            try: 
                p_DOB = int(input("what is the DOB of the patient MMDDYYYY\n"))
                break
            except ValueError:
                print("Invalid format, try again")
        sql = "SELECT patient_ID, patient_name FROM Patients WHERE patient_name = ? AND DOB = ?"
        c.execute(sql,(p_name,p_DOB))
        rows = c.fetchall()
        hits = 0
        p_id = rows[0][0]
        #for row in rows:
            #hits = hits + 1
            #print(row)
    full_patient_report(conn,p_id)    
    patient_menu(conn, p_id)
    
#this is a big one that will need to print patient name, ID, disease, number of samples, and list of genetic mutations
def full_patient_report(conn,p_id):
    sql = "SELECT patient_ID, patient_name, DOB, cancer_type FROM Patients, Diseases WHERE patient_ID = ? AND Patients.disease_ID = Diseases.disease_ID"
    c = conn.cursor()
    c.execute(sql,(p_id,))
    rows = c.fetchall()
    print(tabulate(rows, headers=['patient_ID','patient Name','Date of Birth','Disease'], tablefmt='psql'))
    #for row in rows:
        #print(row)
    list_patient_mutations(conn,p_id)
    full_samples_report(conn,p_id)
    print("Total Samples: ", get_samples_count(conn,p_id),"\n")
    
#find number of samples belonging to patient. Used in full report function    
def get_samples_count(conn,p_id):
    sql = "SELECT count(*) FROM Samples WHERE patient_ID = ?"
    c = conn.cursor()
    c.execute(sql,(p_id,))
    count = c.fetchall()
    return count[0][0]

#select all mutations with matching p_id then append them to a list and print it
def list_patient_mutations(conn,p_id):
    sql = "SELECT mutation_name FROM Mutations, Patient_mutations WHERE Patient_mutations.patient_ID = ? AND Mutations.mutation_ID = Patient_mutations.mutation_ID"
    c = conn.cursor()
    c.execute(sql,(p_id,))
    rows = c.fetchall()
    ret_list = []
    for row in rows:
        ret_list.append(row[0])
    if(len(ret_list) == 0):
        print("No genetic polymorphisms reccorded")
    else:
        print("Genetic Markers: ",ret_list)    
        
#prints a full sampples report for a particular patient. Requires p_id passed to it
def full_samples_report(conn,p_id):
    sql = "SELECT sample_ID, patient_ID, collection_date, freezer_row, freezer_col, freezer_name FROM Samples,Freezers WHERE patient_ID = ? AND  Samples.freezer_ID = Freezers.freezer_ID"
    c = conn.cursor()
    c.execute(sql,(p_id,))
    rows = c.fetchall()
    #print("sample_id |patient_ID |row |column |freezer_name")
    #for row in rows:
       # print(row[0], "         ",row[1],"      ",row[2],"  ",row[3],"    ",row[4])
    print("Samples belinging to this patient:")
    print(tabulate(rows, headers=['sample_ID','Patient_ID','collection date','row','column','Freezer name'], tablefmt='psql'))
def add_patient_mutation(conn, p_id):
    m_id = mutation_lookup(conn)
    #find disease_ID of patient
    sql = "SELECT disease_ID FROM Patients Where patient_ID = ?"
    c = conn.cursor()
    c.execute(sql,(p_id,))
    temp = c.fetchall()
    d_id = temp[0][0]
    sql = ''' INSERT INTO Patient_mutations(mutation_ID,disease_ID,patient_ID)
              VALUES(?,?,?)'''
    insert_command = (m_id,d_id,p_id)
    try:
        c.execute(sql,insert_command)
    except Error as e:
        print(e)
        
#menu for adding sample or mutation data to a selected patient        
def add_data_menu(conn,p_id):
    menu = "Press 1 to Add Sample\nPress 2 to Add Mutation\nPress 3 to go back\n"
    menu_options = 3
    while(True):
        user_input = get_user_input(menu,menu_options)
        if(user_input == 1):
            add_sample(conn,p_id)
        elif (user_input == 2):
            add_patient_mutation(conn,p_id)
        else:
            return
        
#deletes a sample from samples table        
def delete_sample(conn,p_id):
    full_patient_report(conn,p_id)
    while (True):
        try:
            user_input = int(input("enter sample_ID you wish to delete: "))
            break
        except ValueError:
            print("Oops, not valid sample_ID format")
    #flag indidcates that it is a valid sample in the database, and if it does not belong to the current patient, user has confirmed to proceed anyway
    flag = sample_lookup(conn,p_id,user_input)
    if (flag):
        sql = 'DELETE FROM Samples WHERE sample_ID = ?'
        c = conn.cursor()
        try:
            c.execute(sql, (user_input,))
            conn.commit()
        except Error as e:
            print(e)
            
#removes a genetic attribute from a patient. Checks if patient has mutation, if true, deletes entry            
def delete_genetic_att(conn,p_id):
    full_patient_report(conn,p_id)
    print("Gathering information on Mutation to delete:")
    m_id = mutation_lookup(conn)

    sql = "SELECT COUNT(*) FROM Patient_mutations WHERE patient_ID = ? AND mutation_ID = ?"
    c = conn.cursor()
    c.execute(sql,(p_id,m_id))
    temp = c.fetchall()
    if (len(temp) == 0):
        print("Patient does not have that mutation")
    else:
        sql = 'DELETE FROM Patient_mutations WHERE mutation_ID = ? AND patient_ID = ?'
        c = conn.cursor()
        try:
            c.execute(sql,(m_id,p_id))
            conn.commit()
        except Error as e:
            print(e)
#deletes all patient data, including sample and patient_mutations            
def delete_patient(conn,p_id):
    sql_pm = 'DELETE FROM Patient_mutations WHERE patient_ID = ?'
    sql_s = 'DELETE FROM Samples WHERE patient_ID = ?'
    sql_p = 'DELETE FROM Patients WHERE patient_ID = ?'
    c = conn.cursor()
    try:
        c.execute(sql_pm,(p_id,))
        c.execute(sql_s,(p_id,))
        c.execute(sql_p,(p_id,))
        conn.commit()
    except Error as e:
        print(e)
        
#gives user options for removing data from database    
def delete_data_menu(conn,p_id):
    menu = "Press 1 to delete sample\nPress 2 to delete genetic attribute\nPress 3 to delete current Patient\nPress 4 to go back\n"
    menu_options = 4
    while (True):
        user_input = get_user_input(menu,menu_options)
        if (user_input == 1):
            print("Delete sample")
            delete_sample(conn,p_id)
        elif (user_input == 2):
            print("Delete Genetic attribute")
            delete_genetic_att(conn,p_id)
        elif (user_input == 3):
            print("Delete Patient")
            delete_patient(conn,p_id)
        else:
            return
        
#modifies patient data, either name, date of birth, or disease        
def modify_patient_data(conn,p_id):
    full_patient_report(conn,p_id)
    menu = "Press 1 to Modify Patient Name\nPress 2 to Modify Patient DOB\nPress 3 to Modify Patient Disease\nPress 4 to go back\n"
    menu_options = 4
    while (True):
        user_input = get_user_input(menu,menu_options)
        if (user_input == 1):
            print("Modify Patient Name")
            user_input = input("Enter new patient name: ")
            sql = '''UPDATE Patients
                     SET patient_name = ?
                     WHERE patient_id = ?'''
            attributes = (user_input,p_id)
            c = conn.cursor()
            c.execute(sql,attributes)
            conn.commit()
        elif (user_input == 2):
            print("Modify Patient DOB")
            while (True):
                try:
                    user_input = int(input("what is the new Date of Birth MMDDYYYY\n"))
                    break
                except ValueError:
                    print("Oops, not valid date format")
            sql = '''UPDATE Patients
                     SET DOB = ?
                     WHERE patient_id = ?'''
            attributes = (user_input,p_id)
            c = conn.cursor()
            c.execute(sql,attributes)
            conn.commit()
        elif (user_input == 3):
            print("Modify Patient Disease")
            new_d_name = input("Enter new Disease name: ")
            d_id = disease_lookup(conn,new_d_name)
            sql = '''UPDATE Patients
                     SET disease_ID = ?
                     WHERE patient_id = ?'''
            attributes = (d_id,p_id)
            c = conn.cursor()
            c.execute(sql,attributes)
            conn.commit()
            sql = '''UPDATE Patient_mutations
                     SET disease_ID = ?
                     WHERE patient_ID = ?'''
            c = conn.cursor()
            c.execute(sql,attributes)
            conn.commit()
        else:
            return
        
#Finds if sample is in the database and belongs to selected patient. If in database and belongs to current patient, returns true
#Otherwise if sample exists but does not belong to patient, prompts the user to continue, yes = True, no = False
#If sample not in database, returns False
def sample_lookup(conn,p_id,user_input):
    sql = "SELECT count(*) FROM Samples WHERE sample_ID = ?"
    c = conn.cursor()
    c.execute(sql,(user_input,))
    count = c.fetchall()
    if (count[0][0] == 0):
        print("Sample not found in database")
        return False
    else:
        sql = "SELECT count(*) FROM Samples WHERE sample_ID = ? AND patient_ID = ?"
        c = conn.cursor()
        c.execute(sql,(user_input,p_id))
        count = c.fetchall()
        if (count[0][0] == 0):
            print("Sample does not belong to current patient, proceed anyway?")
            yn_in = get_yn()
            if yn_in:
                return True
            else:
                return False
        else:
            return True
        
#changes samples tuple to have a new location in storage        
def modify_sample_location(conn,p_id):
    full_patient_report(conn,p_id)
    while (True):
        try:
            user_input = int(input("enter sample_ID you wish to move: "))
            break
        except ValueError:
            print("Oops, not valid sample_ID format")
    flag = sample_lookup(conn,p_id,user_input)
    if (flag):
        f_id = freezer_lookup(conn)
        while (True):
            try:
                f_row = int(input("What row is the sample stored in?\n"))
                f_col = int(input("What column is the sample stored in?\n"))
                break
            except ValueError:
                print("Please enter integer values")
            
        sql = '''UPDATE Samples
                 SET freezer_ID = ?,
                     freezer_row = ?,
                     freezer_col = ?,
                 WHERE sample_ID = ?'''
        attributes = (f_id,f_row,f_col,user_input)
        c = conn.cursor()
        try:
            c.execute(sql,attributes)
            conn.commit() 
        except Error as e:
            print(e)
            
#changes attribute in patient mutations table but does not delete previous mutation from mutations table    
def modify_genetic_attribute(conn,p_id):
    #user_input = input("Enter Genetic attribute you wish to modify\n")
    m_name = input("What is the name of the genetic mutation you wish to modify?\n")
    
    #first see if it is in the database
    sql = "SELECT mutation_ID FROM Mutations WHERE mutation_name = ?"
    c = conn.cursor()
    c.execute(sql,(m_name,)) 
    temp = c.fetchall()
    if (len(temp) == 0):
        print("mutation not in database")
        return
    else:
        old_m_id = temp[0][0]
    sql = "SELECT COUNT(*) FROM Patient_mutations WHERE patient_ID = ? AND mutation_ID = ?"
    c = conn.cursor()
    c.execute(sql,(p_id,old_m_id))
    temp = c.fetchall()
    if (len(temp) == 0):
        print("Patient does not have that mutation")
    else:
        #get new mutation
        print("Gathering information on new mutation")
        new_m_id = mutation_lookup(conn)
        sql = '''UPDATE Patient_mutations
                 SET mutation_ID = ?
                 WHERE mutation_ID = ?
                     AND patient_ID = ?'''
        attributes = (new_m_id,old_m_id,p_id)
        c = conn.cursor()
        try:
            c.execute(sql,attributes)
            conn.commit()
        except Error as e:
            print(e)

#modify data menu directs user to which data can be modified and calls the appropreate function
def modify_data_menu(conn,p_id):
    menu = "Press 1 to Modify Sample location\nPress 2 to Modify Genetic Attributes\nPress 3 to Modify Patient Data\nPress 4 to go back\n"
    menu_options = 4
    while (True):
        user_input = get_user_input(menu,menu_options)
        if (user_input == 1):
            print("modify sample location")
            modify_sample_location(conn,p_id)
            #get sample ID from user, check if valid, get new location, check if valid
        elif (user_input == 2):
            print("modify genetic attributes")
            modify_genetic_attribute(conn,p_id)
        elif (user_input == 3):
            print("Modify Patient Data")
            modify_patient_data(conn,p_id)
        else:
            return
#handles options for user once a patient has been selected        
def patient_menu(conn, p_id):
    #so you found the patient, you now want to find samples, add sample, add mutations, or quit
    menu = "Press 1 to Display Patient Data\nPress 2 to Add Samples and Data\nPress 3 Modify Samples and Data\nPress 4 Delete Data\nPress 5 to go back\n"
    menu_options = 5
    while (True):
        user_input = get_user_input(menu,menu_options)
        if (user_input == 1):
            print("Display Patient Data")
            full_patient_report(conn,p_id)
        elif (user_input == 2):
            print("Add Data")
            add_data_menu(conn,p_id)
        elif (user_input == 3):
            print("Modify Data")
            modify_data_menu(conn,p_id)
            #add_sample(conn,p_id)
        elif (user_input == 4):
            print("Delete Data")
            delete_data_menu(conn,p_id)
            #add_patient_mutation(conn, p_id)
        else:
            return
        
#print whole db produces an ugly output, is not normally called and is primarilly used for debugging purposes. Query requires all tables have data
def print_whole_db(conn):
    c = conn.cursor()
    #select_command = "SELECT * FROM Patients"
    select_command = "SELECT patient_name, DOB, cancer_type, mutation_name, freezer_name, freezer_row, freezer_col FROM Patients, Samples, Diseases, Mutations, Freezers, Patient_mutations WHERE Patients.patient_ID = Samples.patient_ID AND Samples.freezer_ID = Freezers.freezer_ID AND Patients.disease_ID = Diseases.disease_ID AND Patients.patient_ID = Patient_mutations.patient_ID AND Patient_mutations.mutation_ID = Mutations.mutation_ID"
    c.execute(select_command)
    rows = c.fetchall()
    print("Big table:")
    for row in rows:
        print(row)
    
#main user interface, handles, database connection menu and main menu for queries
def UI():
    debug = False
    print("Welcome to the Patients Oncology and Organizational Partinioner (POOP)")
    menu = "Press 1 to create temporary DB in ram\nPress 2 to connect to static database\nPress 3 to create new database\n"
    menu_options = 3
    user_input = get_user_input(menu,menu_options)
    #print("read ", user_input, "as ", type(user_input), "with value: ", user_input)
    if (user_input == 1):
        (conn, success) = create_local_connection()
        local_memory = True
        if (success == 0):
            print("connection failed, terminating session.")
            raise SystemExit
        create_full_schema(conn)
        generate_fake_data(conn)
        
    elif (user_input ==2):
        print("Connect to local host db")
        #print("temporary measure: using local ram for db")
        local_memory = False
        #Temorary measure for development purposes
        (conn, success) = create_localhost_connection()
        if (success == 0):
            print("connection failed, terminating session.")
            raise SystemExit
    else:
        print("create new local database")
        local_memory = False
        (conn, success) = create_localhost_connection()
        if (success == 0):
            print("connection failed, terminating session.")
            raise SystemExit
        create_full_schema(conn)
        generate_fake_data(conn)
        
    #change menu, patient look up, find samples (by mutation or by disease)
    menu = "Press 1 to search patients\nPress 2 find samples by disease\nPress 3 find samples by genetic mutation\nPress 4 to save and quit\n"
    menu_options = 4
    while(True):
        user_input = get_user_input(menu,menu_options)
        if (user_input == 1):
            print("Patient look up")
            p_name = input("Enter name or patient ID\n")
            patient_lookup(conn,p_name)
        elif (user_input == 2):
            print("Find Samples by Disease")
            find_samples_by_disease(conn)
        elif (user_input == 3):
            print("Find Samples by Mutation")
            find_samples_by_genetic_mutation(conn)
        elif (user_input == 4):
            if (local_memory):
                print("Unable to save on local memory connection")
                break;
            else:
                print("save & quit")
                #this is me being lazy, but this will catch and commit any uncommited inserts
                conn.commit()
                break;
    if (debug):
        print_whole_db(conn)    
    conn.close()

#Selects all samples from patients with a particular disease.
def find_samples_by_disease(conn):
    #pass
    user_input = input("Please enter the name of the disease\n")
    sql = "SELECT COUNT(*) FROM Diseases WHERE cancer_type = ?"
    c = conn.cursor()
    c.execute(sql,(user_input,))
    temp = c.fetchall()
    if (temp[0][0] == 0):
        print("Disease not in database")
        return
    sql = "SELECT disease_ID FROM Diseases WHERE cancer_type = ?"
    c = conn.cursor()
    c.execute(sql,(user_input,))
    d_id = c.fetchall()[0][0]
    print("The following samples are from patients with the selected disease:")
    #sql = "SELECT patient_ID, patient_name, DOB FROM Patients WHERE disease_ID = ? "
    sql = "SELECT Patients.patient_ID, cancer_type, collection_date, sample_ID, freezer_row, freezer_col, freezer_name FROM Samples, Diseases, Freezers, Patients WHERE  Patients.disease_ID = ? AND Patients.disease_ID = Diseases.disease_ID AND Samples.patient_ID = Patients.patient_ID AND Freezers.freezer_ID = Samples.freezer_ID"
    c.execute(sql,(d_id,))
    result = c.fetchall()
    print(tabulate(result, headers=['p_ID','Disease','collection date','Sample ID','row','column', 'Freezer name'], tablefmt='psql'))
    
#some function from python documentation for intersection of lists
def intersection(lst1, lst2): 
    lst3 = [value for value in lst1 if value in lst2] 
    return lst3 

#find samples by genetic mutation creates a list of patients with each mutation. It then intersects each patient with
#a particular mutation with the initial list, eventually selecting only the patients with ALL mutations searched for
def find_samples_by_genetic_mutation(conn):
    m_id_list = []
    m_name_list = []
    while(True):
        m_name = input("What is the name of the genetic mutation?\n")
        sql = "SELECT mutation_ID FROM Mutations WHERE mutation_name = ?"
        c = conn.cursor()
        c.execute(sql,(m_name,)) ################################
        m_id = c.fetchall()
        if (len(m_id) == 0):
            print("mutation not in database, please select from the follwoing list: ")
            sql = "SELECT mutation_name FROM Mutations"
            c.execute(sql)
            result = c.fetchall()
            print(tabulate(result, headers=['Mutation name'], tablefmt='psql'))
        elif (len(m_id) == 1):
            #return m_id[0][0]
            m_name_list.append(m_name)
            m_id_list.append(m_id[0][0])
        #m_id_list should now contain a list of the ussers mutation ID's
        print("Select another mutation?")
        user_yn = get_yn()
        if (user_yn == False):
            break;
    #print(m_id_list)
    prime_list = []
    sql = "SELECT patient_ID FROM Patient_mutations WHERE mutation_ID = ?"
    primary_list = []
    try:
        c.execute(sql,(m_id_list[0],))
        pl = c.fetchall()
    except IndexError:
        print("No matches found")
        return
    for row in pl:
        primary_list.append(row[0])
    #print("primary search: ",pl)
    #print("reduced list: ",primary_list)
    
    for i in range(1,len(m_id_list)):
        secondary_list = []
        c.execute(sql,(m_id_list[i],))
        sl = c.fetchall()
        for row in sl:
            secondary_list.append(row[0])
        primary_list = intersection(primary_list,secondary_list)
    #print("patient ID's with mutation set: ",primary_list)
    print("Matches found: ", len(primary_list), "containing: ", m_name_list)
    
    for i in range(0,len(primary_list)):
        full_patient_report(conn,primary_list[i])
        
        
#generates a random date string. Date string is converted to integer upon insertion, dropping leading zero's. This is confusing and should be fixed later        
def get_random_date():
    #randrange(0, 101, 2)                 # Even integer from 0 to 100 inclusive
    month = str(random.randrange(1,12))
    if (len(month) == 1):
        month = "0" + month
    day = str(random.randrange(1,28))
    if (len(day) == 1):
        day = "0" + day
    year = str(random.randrange(1900,2018))
    date_string = month + day + year
    return date_string

#generates fake data for the relational database, 50 patients, with variable numbers of mutations. Each patient has 5 samples stored among 2 freezers
def generate_fake_data(conn):
    patient_list = generate_patient_data(conn)
    disease_list = ['Breast Cancer', 'Colorectal Cancer', 'Melanoma', 'Lung Cancer', 'Renal Cancer', 'Bladder Cancer', 'Non-Hodgkins lymphoma', 'Thyroid Cancer', 'Pancreatic Cancer', 'Leukemia']
    mutations_list = ['BRCA1', 'BRCA2', 'BRAF', 'RAS', 'pRb', 'p53', 'BCL2', 'SWI/SNF', 'WNT', 'MYC', 'ERK', 'TRK']
    freezer_list = ['Albus DoubleDoor', 'Mr Freeze','Steve the Pirate']
    #print(disease_list,mutations_list,freezer_list)
    
    
    sql = '''INSERT INTO Diseases(disease_ID,Cancer_type)
             VALUES(?,?)'''
    
    for i in range(0,len(disease_list)):
        c = conn.cursor()
        insert_command = (i,disease_list[i])
        try:
            c.execute(sql,insert_command)
        except Error as e:
            print(e)
    c.execute("SELECT * FROM Diseases")
    rows = c.fetchall()
    for row in rows:
        print(row)
    
    sql = '''INSERT INTO Mutations(mutation_ID,mutation_name)
             VALUES(?,?)'''
    for i in range(0,len(mutations_list)):
        c = conn.cursor()
        insert_command = (i,mutations_list[i])
        try:
            c.execute(sql,insert_command)
        except Error as e:
            print(e)
            
    sql = '''INSERT INTO Freezers(freezer_ID,freezer_name)
             VALUES(?,?)'''
    for i in range(0,len(freezer_list)):
        c = conn.cursor()
        insert_command = (i,freezer_list[i])
        try:
            c.execute(sql,insert_command)
        except Error as e:
            print(e)
            
    sql = ''' INSERT INTO Patients(patient_ID,patient_name,DOB,disease_ID)
              VALUES(?,?,?,?)'''
    sql_m = '''INSERT INTO Patient_mutations(mutation_ID,disease_ID,patient_ID)
               VALUES(?,?,?)'''
    sql_s = '''INSERT INTO Samples(sample_ID,patient_ID,collection_date,freezer_ID,freezer_row,freezer_col)
               VALUES(?,?,?,?,?,?)'''
    s_id = 0
    #f_id = 0
    
    for i in range(0,len(patient_list)):
        c = conn.cursor()
        p_DOB = get_random_date()
        d_id = random.randrange(0,len(disease_list))
        insert_command = (i,patient_list[i],p_DOB,d_id)
        pm_list = generate_random_mutations(mutations_list)
        try:
            c.execute(sql,insert_command)
            for l in range(0,len(pm_list)):
                pm_insert = (pm_list[l],d_id,i)
                c.execute(sql_m,pm_insert)
            for k in range(0,5):
                s_col_date = get_random_date()
                f_id = random.randrange(0,len(freezer_list))
                f_row = s_id//10
                f_col = s_id %10
                s_insert = (s_id,i,s_col_date,f_id,f_row,f_col)
                c.execute(sql_s,s_insert)
                s_id = s_id + 1
        except Error as e:
            print(e)
    sql = "SELECT * FROM Patients"
    c.execute(sql)
    rows = c.fetchall()
    conn.commit()
    #for row in rows:
        #print(row)
        
#randomly selects variable numbers of mutations from mutations table to insert into patient mutations
def generate_random_mutations(mutations_list):
    ret_list = []
    number_of_mutations = random.randrange(0,len(mutations_list))
    for i in range(0,number_of_mutations):
        mutation_number = random.randrange(0,len(mutations_list))
        ret_list.append(mutation_number)
    ret_list = list(set(ret_list))
    return ret_list

#reads patient names from file and returns as a list to be inserted into patient table
def generate_patient_data(conn):
    filename = "random_names.txt"
    with open(filename) as f:
        mylist = f.read().splitlines() 
    #print(mylist)
    ds = get_random_date()
    #print(ds)
    return mylist

def main():
    UI()
    
if __name__ == '__main__':
    main()