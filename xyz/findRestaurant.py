from geocode import getGeoLocation
import json
import httplib2

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

foursquare_client_id = "4KZBB34R2W4APRMIJIJX1DWUO04NP2PNCQJX2EFK5PZLV1CD"
foursquare_client_secret = "CPT2SIUZAV5WTUNTVGG0WI3ZAJKO4I0HJ5TV2TE3U3I3KW5R"


def findARestaurant(mealType,location):
	#1. Use getGeocodeLocation to get the latitude and longitude coordinates of the location string.
	latitude, longitude = getGeoLocation(location)
	#2.  Use foursquare API to find a nearby restaurant with the latitude, longitude, and mealType strings.
	#HINT: format for url will be something like https://api.foursquare.com/v2/venues/search?client_id=CLIENT_ID&client_secret=CLIENT_SECRET&v=20130815&ll=40.7,-74&query=sushi
	url = ('https://api.foursquare.com/v2/venues/search?client_id=%s&client_secret=%s&v=20130815s&ll=%s,%s&query=%s' % (foursquare_client_id, foursquare_client_secret, latitude, longitude, mealType))
	h = httplib2.Http()
	result = json.loads(h.request(url,'GET')[1])

	#3. Grab the first restaurant
	if result['response']['venues']:
		restaurant = result['response']['venues'][0]
		venue_id = restaurant['id']
		restaurant_name = restaurant['name']
		restaurant_add = restaurant['location']['formattedAddress']
		address =""
		for i in restaurant_add:
			address += i + " "
		restaurant_add = address
		print restaurant_add	

		#4. Get a  300x300 picture of the restaurant using the venue_id (you can change this by altering the 300x300 value in the URL or replacing it with 'orginal' to get the original picture
		url = ('https://api.foursquare.com/v2/venues/%s/photos?client_id=%s&v=20130815s&client_secret=%s' % (venue_id, foursquare_client_id, foursquare_client_secret))
		res ult = json.loads(h.request(url,'GET')[1])
		if result['response']['photos']['items']:
			first_photo = result['response']['photos']['items'][0]
			prefix = first_photo['prefix']
			suffix = first_photo['suffix']
			imageURL = prefix + "300x300" + suffix
		#5. Grab the first image
		#6. If no image is available, insert default a image url
		#7. Return a dictionary containing the restaurant name, address, and image url
		else:
			restaurantInfo = {'name':restaurant_name, 'address':restaurant_add, 'image':imageURL}
			print "restaurant name %s" % restaurantInfo['name']
			print "restaurant address %s" % restaurantInfo['address']
			print "image %s" % restaurantInfo['image']
			return restaurantInfo

	else:	
		print "No restaurants were Found @%s" % location
		return "No Rstaurants Found"	




if __name__ == '__main__':
	findARestaurant("Pizza", "Tokyo, Japan")
	findARestaurant("Tacos", "Jakarta, Indonesia")
	findARestaurant("Tapas", "Maputo, Mozambique")
	findARestaurant("Falafel", "Cairo, Egypt")
	findARestaurant("Spaghetti", "New Delhi, India")
	findARestaurant("Cappuccino", "Geneva, Switzerland")
	findARestaurant("Sushi", "Los Angeles, California")
	findARestaurant("Steak", "La Paz, Bolivia")
	findARestaurant("Gyros", "Sydney Australia")
