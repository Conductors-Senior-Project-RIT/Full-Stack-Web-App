import psycopg
import os
import yaml

# helper function, connects to the database
def create_connection():
    cfg = {}
    full_config_path = os.path.join(os.path.dirname(__file__), '../../config/postgres_config.yml')
    with open(full_config_path, 'r') as file:
        cfg = yaml.load(file, Loader=yaml.FullLoader)
        # print(cfg['database'])
        # print(cfg['user'])
        # print(cfg['password'])
        # print(cfg['host'])
        # print(cfg['port'])
    return psycopg.connect(
        dbname=cfg['database'],
        user=cfg['user'],
        password=cfg['password'],
        host=cfg['host'],
        port=cfg['port']
    )

# opens an sql file, and runs the code inside on the db
def run_sql_file(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    connection = create_connection()
    cursor = connection.cursor()
    with open(file_path, 'r') as sql_file:
        cursor.execute(sql_file.read())
    connection.commit()
    connection.close()

# runs a command to get data
def run_get_cmd(sql, args={}): # returns list of tuples 
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(sql, args)
    tuples = cursor.fetchall()
    connection.close()
    return tuples

# runs a sql command to commit changes to the db
def run_exec_cmd(sql, args={}): #always returns none https://stackoverflow.com/questions/37965198/python-psycopg2-cursor-execute-returning-none
    connection = create_connection()
    cursor = connection.cursor()
    res = cursor.execute(sql, args)
    connection.commit()
    connection.close()
    return res
