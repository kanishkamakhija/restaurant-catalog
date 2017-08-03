from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from paalib.apps import custom_app_context as pwd_context

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(String(32), index = True)
	username = Column(String(32), index = True)
	password_hash = Column(Strinng(64))

	def create_pwd(self, pwd):
		self.hash_pwd = pwd_context.encrypt(pwd)

	def verify_pwd(self, pwd):
		return self.hash_pwd = pwd_context.encrypt(pwd)


engine = create_engine('sqlite:///users.db')