from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from flask_paginate import Pagination, get_page_args
from PIL import Image
from io import BytesIO
import base64
import os
import json
import mysql.connector

from database import database_open, database_query, database_close
import config


dbconn = database_open(config.MYSQL_DATABASE_HOST,
                       config.MYSQL_DATABASE_DB,
                       config.MYSQL_DATABASE_USER,
                       config.MYSQL_DATABASE_PASSWORD)

cursor = dbconn.cursor()

# Read the whole photos table
sql = "SELECT id, filename, crop, crop_other, contributor_name, lat, lng, width, height, camera_model, lens_desc, timestamp, archived FROM photos"
val = ()
cursor.execute(sql,val)
data = cursor.fetchall()


# Read the taxonomies
sql = "SELECT * from taxonomy"
val = ()
cursor.execute(sql,val)
taxonomy = cursor.fetchall()


# Read the categories
sql = "SELECT * from categories"
val = ()
cursor.execute(sql,val)
categories = cursor.fetchall()




app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def main():
	if("who" in session):
		return redirect("/photos?page=1&per_page=10")
	else:
		return redirect("/login")



@app.route('/login', methods=["POST", "GET"])
def login():
	if(request.method == "POST"):
		session["who"] = request.form.get("who")
		return redirect("/")
	return render_template("login.html")
	

@app.route('/photos')
def photos():

	if(not "who" in session):
		return redirect("/login")

	#page = request.args.get('page', 1, type=int)

	page, per_page, offset = get_page_args()
	print("page = %d" %page)
	print("per_page = %d" %per_page)
	print("offset = %d" %offset)

	pagination = Pagination(page=page, per_page=per_page, offset=offset, total=len(data), record_name='Photos')

	subset=data[offset:offset+per_page]

	return(render_template("photos.html", 
				data=subset, 
				taxonomy=taxonomy, 
				categories=categories,
				pagination=pagination, 
				form="submitIt", 
				who=session["who"]))

@app.route('/help')
def help():
	if("who" in session):
		who = session["who"]
	else:
		who = ""
	return(render_template("help.html", who=who))



@app.route('/upload', methods = ['GET', 'POST'])
def upload():
	print("In upload()");

	if request.method == 'POST':
		content = request.json

		image_data = content['croppedImage']
		image_who  = content['who']
	
		# strip the mime type info off the image string to get just the base64
		image_data = image_data.split("base64,")[1];

		im = Image.open(BytesIO(base64.b64decode(image_data)))
		im.save("uploads/foo.png")

		return 'file uploaded successfully'

if __name__ == '__main__':
	app.run(port=9999, debug=True)
