from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from flask_paginate import Pagination, get_page_args
from PIL import Image
from io import BytesIO
import base64, uuid
import os
import json
import mysql.connector

from database import database_open, database_query, database_close
import config


dbconn = database_open()
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

		# strip the mime type info off the image string to get just the base64
		image_data = image_data.split("base64,")[1];
		img = Image.open(BytesIO(base64.b64decode(image_data))).convert('RGB')

		img_photo_id = content['photo_id']
		img_curator_id  = content['who']
		img_notes = content['notes']
		img_taxonomy_id = content['taxonomy']
		(img_width, img_height) = img.size

		print(img_photo_id)
		print(img_curator_id)
		print(img_taxonomy_id)
		print(img_notes)
		print(img_width, img_height)
	

		newfilenamebase = str(uuid.uuid4())
		newfilename = newfilenamebase + ".jpg"

		#+-------------+--------------+------+-----+---------+----------------+
		#| Field       | Type         | Null | Key | Default | Extra          |
		#+-------------+--------------+------+-----+---------+----------------+
		#| id          | int(11)      | NO   | PRI | NULL    | auto_increment |
		#| photos_id   | int(11)      | YES  |     | NULL    |                |
		#| curators_id | int(11)      | YES  |     | NULL    |                |
		#| taxonomy_id | int(11)      | YES  |     | NULL    |                |
		#| width       | int(11)      | YES  |     | NULL    |                |
		#| height      | int(11)      | YES  |     | NULL    |                |
		#| path        | varchar(256) | YES  |     | NULL    |                |
		#| notes       | text         | YES  |     | NULL    |                |
		#+-------------+--------------+------+-----+---------+----------------+
		
		dbconn = database_open()
		sql = "INSERT INTO processed (photos_id, curators_id, taxonomy_id, width, height, path, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)"
		val = (img_photo_id, img_curator_id, img_taxonomy_id, img_width, img_height, newfilename, img_notes)
		result = database_query(dbconn, sql, val)
		dbconn.commit()
		database_close(dbconn)

		img.save(os.path.join(config.CROPPED_ROOT, "imagebank", newfilename), quality=100)

		img.thumbnail(config.THUMBNAIL_SIZE)
		thumbpath  = os.path.join(config.CROPPED_ROOT, "thumbnails", newfilename)
		img.save(thumbpath, format="JPEG", quality=50, optimize=True, progressive=True)

		return 'file uploaded successfully'

if __name__ == '__main__':
	app.run(port=9999, debug=True)
