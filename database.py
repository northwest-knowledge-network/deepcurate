import re
import mysql.connector

import config

def database_open():
	try:
		connection = mysql.connector.connect(host=config.MYSQL_DATABASE_HOST, 
						     database=config.MYSQL_DATABASE_DB, 
						     username=config.MYSQL_DATABASE_USER, 
						     password=config.MYSQL_DATABASE_PASSWORD)
		return(connection)

	except mysql.connector.Error as error:
		print("FAILED TO CONNECT TO DB: " + error)
		exit(-1)



def database_query(conn, sql, val):

	try:
		cursor = conn.cursor()
		cursor.execute(sql, val)
		return(cursor)
		
	except mysql.connector.Error as error:
		print("FAILED TO QUERY DB: " + error)
		return(None)


def database_close(conn):
	conn.close()




