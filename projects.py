#! /usr/bin/env python2

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, relationship
from database_setup import Base, Restaurant, MenuItem, User
import os
import sys
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from flask import session as login_session
import random
import string
# new imports for authentication and authorization
# login_session works as a dict and save data of user login session
# generates pseudo random string that identify each session
# imports for this step
# from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# connect to db and create db session
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


"""
    create a state token to prevent required forgery.
    & store it in a session for later verification.
"""


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "the current session state is %s" %login_session['state']
    return render_template('login.html', STATE=state)


"""
Third party authentication i.e.
allow user to login throough gmail
"""


@app.route('/gconnect', methods=['POST'])
def gconnect():
    #  validate state token
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

    # check all the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # if there is an error in access token info then abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access_token is used for intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access_token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # get user Information through google account.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # get user picture
    # url = of pic
    # h = httplib2.Http()
    # result = h.request(url, 'GET')[1]
    # data = json.loads(result)
    # login_session['pictur'] = data["data"]["url"]
    # see if a user exist, if does'nt make a new one.
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
    output += ''' " style = "width: 300px;
                             height: 300px;
                             border-radius: 150px;
                             -webkit-border-radius: 150px;
                             -moz-border-radius: 150px;">
              '''
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT- revoke users token and reset their login session.


"""
Function to disconnect the connected user
from their linked gmail account.
"""


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
# execute http get req to revoke current token.
    access_token = credentials
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
        restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
        flash("Successfully disconnected")
        return render_template('restaurant.html', restaurants=restaurants)
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


"""
Function that will return JSON APis
to view Restaurant Information
"""


@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


"""
Function that will return JSON APis
to view Restaurant Menu Information
"""


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


"""
Function that will display
all restaurant currently present in the database.
"""


@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    return render_template(
        'restaurant.html',
        restaurants=restaurants,
        login_session=login_session)


"""
Function to add new restaurant
in the database.
"""


@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newRestaurant = Restaurant(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html')


"""
Function to delete the restaurant
from the database.
"""


@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurantToDelete = session.query(
        Restaurant).filter_by(id=restaurant_id).one_or_none()
    if 'username' not in login_session:
        return redirect('/login')
    if (
        restaurantToDelete and restaurantToDelete.user_id) != (
            login_session['user_id']):
        flash('You are not authorized to delete this restaurant')
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        itemsToDelete = session.query(MenuItem).filter_by(
            restaurant_id=restaurantToDelete.id)
        itemsToDelete.delete()
        session.delete(restaurantToDelete)
        flash('%s Successfully Deleted' % restaurantToDelete.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template(
            'deleterestaurant.html', restaurant=restaurantToDelete)


"""
Function to edit the existing restaurant
in the database.
"""


@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    editedRestaurant = session.query(
        Restaurant).filter_by(
            id=restaurant_id).one_or_none()
    if 'username' not in login_session:
        return redirect('/login')
    if (
        editedRestaurant and editedRestaurant.user_id) != (
            login_session['user_id']):
        flash('You are not authorized to edit this restaurant')
        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            flash('Restaurant successfully edited %s' % editedRestaurant.name)
            return redirect(
                url_for('showRestaurants', restaurant_id=restaurant_id))
    else:
        return render_template(
            'editrestaurant.html', restaurant=editedRestaurant)


"""
Function to show the menu
of the restaurant.
"""


@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(
        Restaurant).filter_by(
            id=restaurant_id).one_or_none()
    if not restaurant:
        flash("Restaurant does not exist")
        return redirect(url_for('showRestaurants'))
    creator = getUserInfo(restaurant.user_id)
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    if (
        'username' not in login_session or restaurant.user_id) != (
            login_session['user_id']):
        return render_template(
            'publicmenu.html',
            items=items,
            restaurant=restaurant,
            creator=creator)
    else:
        return render_template(
            'menu.html',
            items=items,
            restaurant=restaurant,
            creator=creator)


"""
Function to edit the existing menu item
in the restaurant menu.
"""


@app.route(
    '/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit',
    methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    restaurantToDelete = session.query(
        Restaurant).filter_by(
            id=restaurant_id).one_or_none()
    if not restaurantToDelete:
        flash('This restaurant does not exist')
        return redirect(url_for('showRestaurants'))
    if not editedItem:
        flash('This item does not exist')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if restaurantToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to edit item from this restaurant menu')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
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
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template(
            'editmenuitem.html',
            restaurant_id=restaurant_id,
            menu_id=menu_id, i=editedItem)


"""
Function to add a new menu item
in the restaurant menu.
"""


@app.route(
    '/restaurant/<int:restaurant_id>/menu/new/',
    methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(
        Restaurant).filter_by(
            id=restaurant_id).one_or_none()
    if not restaurant:
        flash('This restaurant does not exist')
        return redirect(url_for('showRestaurants'))
    if login_session['user_id'] != restaurant.user_id:
        flash('You are not authorized to create menu item for this restaurant')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if request.method == 'POST':
        newItem = MenuItem(
            name=request.form['title'],
            description=request.form['description'],
            price=request.form['price'],
            course=request.form['course'],
            restaurant_id=restaurant_id,
            user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)


"""
Function to delete the existing menu item
from the restaurant menu.
"""


@app.route(
    '/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete',
    methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurantToDelete = session.query(
                                       Restaurant).filter_by(
                                       id=restaurant_id).one_or_none()
    if not restaurantToDelete:
        flash('This restaurant does not exist')
        return redirect(url_for('showRestaurants'))
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    if not itemToDelete:
        flash('This item does not exist')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if restaurantToDelete.user_id != login_session['user_id']:
        flash(
            'You are not authorized to delete item from this restaurant menu')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)


""" A user helper function.
Creates a new user or allow a user to login.
"""


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

"""
This function returns the information of the existing user
from the user database.
"""


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
