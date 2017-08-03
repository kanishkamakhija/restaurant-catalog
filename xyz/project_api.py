from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
#request ---- in order to get data form our form
#jsonify ---- eazily configure api input for application
#instance of the class with the name of the application as running argument
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, relationship
from database_setup import Base, Restaurant, MenuItem, User
from flask import session as login_session 
"""login_session works as a dict and store users session with the server"""
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
#import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for  x in xrange(32))
	login_session['state'] = state
	# return "the current session state is %s" % login_session['state']
 	return render_template('login.html', STATE = state)

@app.route('/gconnect', methods = ['POST'])
def gconnect():
    #validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response


    #check all the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    #if there is an error in access token info then abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    #verify that the access_token is used for intended user.
    gplus_id = credentials.id_token['sub']
    if result['user-id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #verify that the access_token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    #store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    #get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']


    # #get user picture
    # url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    # h = httplib2.Http()
    # result = h.request(url, 'GET')[1]
    # data = json.loads(result)

    # login_session['picture'] = data["data"]["url"]


    #see if a user exist, if does'nt make a new one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# @app.route('/gconnect', methods=['POST'])
# def gconnect():
# 	if request.args.get('state') != login_session['state']:
# 		response = make_response(json.dumps('Invalid state parameter'), 401)
# 		response.headers['Content-Type'] = 'application/json'
# 		return response

# 	code = request.data
# 	try:
# 		#upgrade the authorization code into a credentials object
# 		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
# 		oauth_flow.redirect_uri = 'postmessage'
# 		credentials = oauth_flow.step2_exchange(code)
# 	except FlowExchangeError:
# 		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
# 		response.headers['Content-Type'] = 'application/json'
# 		return response 	


# 	#check that access token is valid
# 	access_token = credentials.access_token
# 	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
# 	h = httplib2.Http()
# 	result = json.loads(h.request(url, 'GET')[1])


# 	#if there is an error in access token info then abort.
# 	if result.get('error') is not None:
# 	    response = make_response(json.dumps(result.get('error')), 500)
# 	    response.headers['Content-Type'] = 'application/json'
# 	    return response

# 	#verify that the access_token is used for intended user.
# 	gplus_id = credentials.id_token['sub']
# 	if result['user-id'] != gplus_id:
# 	    response = make_response(json.dumps("Token's user ID doesn't match given app's."), 401)
# 	    response.headers['Content-Type'] = 'application/json'
# 	    return response

# 	#check to see if the user is already loged in
# 	stored_credentials = login_session.get('credentials')
# 	stored_gplus_id = login_session.get('gplus_id')
# 	if stored_credentials is not None and gplus_id == stored_gplus_id:
# 		response = make_response(json.dumps('Current user is already connected.'), 200)
# 		response.headers['Content-Type'] = 'application/json'
# 		return response

 
	# #store the access token in the session for later use.
	# login_session['credentials'] = credentials
	# login_session['gplus_id'] = gplus_id

	# #get user info.
 #    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
 #    params = {'access_token': credentials.access_token, 'alt': 'json'}
 #    answer = requests.get(userinfo_url, params=params)
 #    data = answer.json()

#     login_session['username'] = data['name']
#     login_session['picture'] = data['picture']
#     login_session['email'] = data['email']


#     #get user picture
#     url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
#     h = httplib2.Http()
#     result = h.request(url, 'GET')[1]
#     data = json.loads(result)

#     login_session['pictur'] = data["data"]["url"]


#     #see if a user exist, if does'nt make a new one.
#     user_id = getUserID(login_session['email'])
#     if not user_id:
#         user_id = createUser(login_session)
#     login_session['user_id'] = user_id

#     output = ''
#     output += '<h1>Welcome, '
#     output += login_session['username']
#     output += '!</h1>'
#     output += '<img src="'
#     output += login_session['picture']
#     output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
#     flash("you are now logged in as %s" % login_session['username'])
#     print "done!"
#     return output



#DISCONNECT- revoke users token and reset their login session.
@app.route('/gdisconnect')
def gdisconnect():
    #only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


#user helper function.
def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).Filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserId(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None


#Makhing an API endpoint (GET request) (other type of req can also be created)

@app.route('/restaurants/JSON')
def resturantsJSON():
	restaurants = session.query(Restaurant).all()
	return jsonify(restaurants = [i.serialize for i in restaurants])

	
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(MenuItems = [i.serialize for i in items])


#Adding API endpoint here
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
	menuItem = session.query(MenuItem).filter_by(id = menu_id).one()
	return jsonify(MenuItem = menuItem.serialize)



"""Show all the restaurants"""

@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    if 'username' not in login_session:
        return render_template('publicrestaurants.html', restaurants = restaurants)
    else:
        return render_template('restaurant.html', restaurants = restaurants)




"""Add a new restaurant"""

@app.route('/restaurants/new/', methods = ['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'])
        user_id = login_session['user_id']
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html')




"""Edit a restaurant"""

@app.route('/restaurants/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
            return redirect(url_for('showRestaurants'))
    else:
        return render_template('editrestaurant.html', restaurant = editedRestaurant)




"""Delete a restaurant"""

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if restaurantToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        session.delete(restaurantToDelete)
        flash('%s Successfully Deleted' % restaurantToDelete.name)
        session.commit()
        return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
    else:
        return render_template('deleterestaurant.html', restaurant=restaurantToDelete)



#decorators ----@a that wrap the function in app.route func
#and used to bind a func to a url

"""Show a menu of a restaurant"""

@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/menu')
def restaurantMenu(restaurant_id = 1):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	creator = getUserInfo(restaurant.user_id)
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicmenu.html, items = items, restaurant = restaurant, creator = creator')
	else:
		return render_template('menu.html', restaurant = restaurant, items = items, creator = crearor)




"""Add new item to the menu of a particular restaurant"""

@app.route('/restaurants/<int:restaurant_id>/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		name = request.form['name']
		desc = request.form['description']
		price = request.form['price']
		course = request.form['course']
		newitem = MenuItem(name = name,description =  desc, price = price, course = course, restaurant_id = restaurant_id, user_id = restaurant.user_id)
		session.add(newitem)
		session.commit()
		flash("New Menu Item Created")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)




"""Edit the item from a menu of a restaurant"""

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	editedItem = session.query(MenuItem).filter_by(id = menu_id).one()
	
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']
		if request.form['price']:
			editedItem.price = request.form['price']
		if request.form['course']:
			editedItem.course = request.form['course']			
		
		session.add(editedItem)
		session.commit()
		flash("Menu Item Has Been Edited!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, i = editedItem)




"""Delete the item from a menu of a restaurant"""

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	itemToDelete = session.query(MenuItem).filter_by(id = menu_id).one()
	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		flash("Menu Item Has  Been Deleted!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('deletemenuitem.html', i = itemToDelete)




if __name__ == '__main__':
	#secure key to create session for flash messages
	app.secret_key = 'super_secret_key'
	#the webserver reloads itself by enabling debug each time it finds any modification
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000) #run on the localhost
