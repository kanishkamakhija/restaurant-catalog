# import httplib2
# import json

# import sys
# import codecs
# sys.stdout = codecs.getwriter('utf8')(sys.stdout)
# sys.stderr = codecs.getwriter('utf8')(sys.stderr)




# def getGeoLocation(inputPlace):
# 	googple_api_key = " AIzaSyDugUdfv_UBT3r2wI_pQLN3rnYFZNBU5hU"
# 	stringLocation = inputPlace.replace(" ","+")
# 	url = ('https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s' % (stringLocation, googple_api_key))
# 	h = httplib2.Http()
# 	# response, content = h.request(url, 'GET')
# 	# result = json.loads(content)
# 	result = json.loads(h.request(url,'GET')[1])
# 	latitude  = result['results'][0]['geometry']['location']['lat']
# 	longitude = result['results'][0]['geometry']['location']['lng']
# 	return (latitude,longitude)  

import httplib2
import json

def getGeoLocation(inputPlace):
    # Use Google Maps to convert a location into Latitute/Longitute coordinates
    # FORMAT: https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=API_KEY
    google_api_key = "AIzaSyDugUdfv_UBT3r2wI_pQLN3rnYFZNBU5hU"
    locationString = inputPlace.replace(" ", "+")
    url = ('https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s'% (locationString, google_api_key))
    h = httplib2.Http()
    result = json.loads(h.request(url,'GET')[1])
    latitude = result['results'][0]['geometry']['location']['lat']
    longitude = result['results'][0]['geometry']['location']['lng']
    return (latitude,longitude)