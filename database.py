import re
import mysql.connector

import config


def database_open(db_host, db_database, db_username, db_password):
	try:
		#print(db_host, db_database, db_username, db_password)
		connection = mysql.connector.connect(host=db_host, database=db_database, username=db_username, password=db_password)
		print("CONNECTED TO DB!")
		return(connection)
	except mysql.connector.Error as error:
		print("FAILED TO CONNECT TO DB: " + error)
		exit(-1)



def database_query(conn, sql, val):

	#print(sql)
	#print(val)


	try:
		cursor = conn.cursor()
		cursor.execute(sql, val)
		return(cursor)
		
	except mysql.connector.Error as error:
		print("FAILED TO QUERY DB: " + error)
		return(None)


def database_close(conn):
	conn.close()




