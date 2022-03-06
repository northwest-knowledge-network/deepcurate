import os
import re
import json
import exifread as ef
import mysql.connector
import uuid

from PIL import Image

import config
from database import database_open, database_query, database_close 


# for now, IMPORT_BATCH points to the src directory to import images from
IMPORT_BATCH = os.path.join(config.PHOTOS_ROOT, 'batch_001_01.14.2022')

# THUMBNAILS is the directory containing normalized, resized thumbnails
THUMBNAILS = os.path.join(config.PHOTOS_ROOT, 'thumbnails')

# IMAGEBANK is the directory containing all full-size imported images
IMAGEBANK = os.path.join(config.PHOTOS_ROOT, 'imagebank')

# PREVIEWDIR is the directory containing larger previews of images for popups
PREVIEWDIR = os.path.join(config.PHOTOS_ROOT, 'previews')


print("PATHS:")
print("   PHOTOS_ROOT: %s" %config.PHOTOS_ROOT)
print("   IMPORT_BATCH: %s" %IMPORT_BATCH)
print("   THUMBNAILS: %s" %THUMBNAILS)
print("   IMAGEBANK: %s" %IMAGEBANK)
print("   PREVIEWDIR: %s" %PREVIEWDIR)




def _convert_to_degrees(value):
	"""
	Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format
	:param value:
	:type value: exifread.utils.Ratio
	:rtype: float
	"""

	if(value.values[0].den == 0 or 
	   value.values[1].den == 0 or
	   value.values[2].den == 0):
		return(-9999)	

	d = float(value.values[0].num) / float(value.values[0].den)
	m = float(value.values[1].num) / float(value.values[1].den)
	s = float(value.values[2].num) / float(value.values[2].den)

	return d + (m / 60.0) + (s / 3600.0)



def getGPS(filepath):
	'''
	returns gps data if present other wise returns empty dictionary
	'''
	with open(filepath, 'rb') as f:

		tags = ef.process_file(f)
		latitude = tags.get('GPS GPSLatitude')
		latitude_ref = tags.get('GPS GPSLatitudeRef')
		longitude = tags.get('GPS GPSLongitude')
		longitude_ref = tags.get('GPS GPSLongitudeRef')
		if latitude:
			lat_value = _convert_to_degrees(latitude)
			if(lat_value == -9999):
				return {}
			if latitude_ref.values != 'N':
				lat_value = -lat_value
		else:
			return {}
		if longitude:
			lon_value = _convert_to_degrees(longitude)
			if(lon_value == -9999):
				return {}
			if longitude_ref.values != 'E':
				lon_value = -lon_value
		else:
			return {}
		return {'lat':lat_value, 'lng':lon_value}
	return {}




def getTimestamp(filepath):
	with open(filepath, 'rb') as f:
		tags = ef.process_file(f)

		dateTaken = tags.get('EXIF DateTimeOriginal')
		if(dateTaken == None):
			return None
		else:
			#return {'timestamp': str(dateTaken)}
			return(str(dateTaken))




def get_metadata(fullpath):
	print(fullpath)

	img = Image.open(fullpath)
	(w,h) = img.size

	lens_model = None
	camera_model = None
	lat = None
	lng = None
	timestamp = None

	exif_data = img._getexif()
	if(exif_data):
		if 42036 in exif_data:   # Lens Model
			lens_model = exif_data[42036]

		if 272 in exif_data:   # Camera Model
			camera_model = exif_data[272]

		gps = getGPS(fullpath)
		if(gps):
			lat = gps['lat']
			lng = gps['lng']

		timestamp = getTimestamp(fullpath)

	metadata_dict = {'fullpath':fullpath,
		       'width':w,
		       'height':h,
		       'lens':lens_model,
		       'camera':camera_model,
		       'lat':lat,
		       'lng':lng,
		       'timestamp':timestamp}

	return(metadata_dict)



def process_filename(filename):
	
	foo = re.split(r'[-]+', filename)
	y = [x for x in foo if not x.endswith('jpg') and not x.endswith('gif') and not x.endswith('png') and not x.endswith('JPG') and not x.endswith('GIF') and not x.endswith('PNG') and not x.endswith('jpeg') and not x.endswith('JPEG')]	

	crop = None
	cropother = None
	name = None

	if(len(y)>=2):
		if(y[0]=="other"):
			cropother = y[1]
			y.pop(1)

	if(len(y)>=1):
		crop = y[0]
		y.pop(0)

	if(len(y)>0):
		name = ' '.join([str(elem) for elem in y])

	return {'filename':filename, 'crop':crop, 'crop_other':cropother, 'name':name}


def deposit_image(fullpath, newfilename, imagebank, thumbnail, previews):

	img = Image.open(fullpath)

	imgbankpath = os.path.join(imagebank, newfilename)
	img.save(imgbankpath, format="JPEG", quality=100, optimize=True, progressive=True)	

	thumb_img = img.copy()
	thumb_img.thumbnail(config.THUMBNAIL_SIZE)
	thumbpath   = os.path.join(thumbnail, newfilename)
	thumb_img.save(thumbpath, format="JPEG", quality=50, optimize=True, progressive=True)

	prev_img = img.copy()
	prev_img.thumbnail(config.PREVIEW_SIZE)
	prevpath   = os.path.join(previews, newfilename)
	prev_img.save(prevpath, format="JPEG", quality=75, optimize=True, progressive=True)



	

########
#  MAIN
######## 


dbconn = database_open(config.MYSQL_DATABASE_HOST,
		       config.MYSQL_DATABASE_DB,
		       config.MYSQL_DATABASE_USER,
		       config.MYSQL_DATABASE_PASSWORD)


pics = os.listdir(IMPORT_BATCH)
for p in pics:

	newfilename = str(uuid.uuid4()) + ".jpg"

	fullpath = os.path.join(IMPORT_BATCH, p)
	filestuff = process_filename(p)
	metadata = get_metadata(fullpath)

	metadata.update(filestuff)  # append filestuff dict to metadata dict

	sql = "INSERT INTO photos (filename, crop, crop_other, contributor_name, lat, lng, width, height, camera_model, lens_desc, timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
	val = (newfilename, metadata['crop'], metadata['crop_other'], metadata['name'], metadata['lat'], metadata['lng'], metadata['width'], metadata['height'], metadata['camera'], metadata['lens'], metadata['timestamp'])

	deposit_image(fullpath, newfilename, IMAGEBANK, THUMBNAILS, PREVIEWDIR)

	result = database_query(dbconn, sql, val)
	dbconn.commit()

database_close(dbconn)

exit(0)

