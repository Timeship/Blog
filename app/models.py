#!/usr/bin/env python
# coding=utf-8
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import login_manager
from .import db

class Role(UserMixin,db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(64),unique=True,index=True)
    users = db.relationship('User',backref='role')

    def __repr__(self):
        return '<Role %r>'%self.name

class User(UserMixin,db.Model):
    #...
    __tablename__ = 'users'

    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean,default=False)

    def __repr__(self):
        return '<Role %r>'%self.username

    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def vertify_password(self,password):
        return check_password_hash(self.password_hash,password)

    confirmed = db.Column(db.Boolean,default=False)

    def generate_confirmation_token(self,expiration=3600): #generate_confirmation_token方法生成一个令牌，有效期为1小时
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id}) #dump方法为指定数据生成一个加密签名

    def confirm(self,token): #confirm方法检验令牌，如果检验通过，则把新添加的confirmed属性设置为True
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token) #为了解码令牌，序列化对象提供了loads()方法,唯一参数是令牌字符串，load检验签名和过期时间，如果通过，
                                  #返回原始数据，如果不正确或者过期了，抛出异常
        except:
            return False
        if data.get('confirm') !=self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

