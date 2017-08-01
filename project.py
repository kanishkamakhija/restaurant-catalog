from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
#request ---- in order to get data form our form
#jsonify ---- eazily configure api input for application
#instance of the class with the name of the application as running argument
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, relationship
from database_setup import Base, Restaurant, MenuItem, User
from flask import session as login_session


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()



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
    # if 'username' not in login_session:
    #     return render_template('publicrestaurants.html', restaurants = restaurants)
    # else:
    return render_template('restaurant.html', restaurants = restaurants)




"""Add a new restaurant"""

@app.route('/restaurants/new/', methods = ['GET', 'POST'])
def newRestaurant():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'])
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html')




"""Edit a restaurant"""

@app.route('/restaurants/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
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
    # if 'username' not in login_session:
    #     return redirect('/login')
    # if restaurantToDelete.user_id != login_session['user_id']:
    #     return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"

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
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)

	return render_template('menu.html', restaurant = restaurant, items = items, restaurant_id = restaurant_id)



"""Add new item to the menu of a particular restaurant"""

@app.route('/restaurants/<int:restaurant_id>/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		name = request.form['name']
		desc = request.form['description']
		price = request.form['price']
		course = request.form['course']
		newitem = MenuItem(name = name,description =  desc, price = price, course = course, restaurant_id = restaurant_id)
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
