from models import Base, User
from flask import Flask, jsonify, request, url_for, abort
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from flask import Flask

engine = create_engine('sqlite:///users.db')


@app.route('/users', methods = ['POST'])
def add_user():
	username = request.json.get('username')
	password = request.json.get('password')
	if username is None or password is None:
		abort(400)
	if session.query(User).filter_by(username = username).first() is not None:
		abort(400)
	user = User(username = username)
	user.create_pwd(pwd)
	session.add(user)
	session.commit()
	return = jsonify({'username': user.username }),201

Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()
app =Flask(__name__)	

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port=5000)from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine