#!/usr/bin/env python
# coding=utf-8
import hashlib
from datetime import datetime
from flask.ext.login import UserMixin,AnonymousUserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app,request
from . import login_manager
from .import db

'''权限设置'''
class Permission:
    FOLLOW = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80

'''角色设置'''
class Role(UserMixin,db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True,index=True) #index，创建索引，提升查询效率
    default = db.Column(db.Boolean,default=False,index=True)#default为这列定义默认值
    permissions = db.Column(db.Integer)
    users = db.relationship('User',backref='role',lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES,True),
            'Moderator':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES |Permission.MODERATE_COMMENTS,False),
            'Administrator':(0xff,False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>'%self.name

'''关注设置'''
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)

'''评论设置'''
class Comment(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

    '''将评论的markdown格式转成html显示'''
    @staticmethod
    def on_changed_body(target,value,initiator):
        allowed_tags = ['a','abbr','acronym','b','code','em','i','strong']
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))

'''用户设置'''
class User(UserMixin,db.Model):
    #...
    __tablename__ = 'users'

    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean,default=False)
    #...
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text()) #db.Text不需要像db.String那样指定最大长度
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    #.. .
    posts = db.relationship('Post',backref='author',lazy='dynamic')
     
    '''关注者,此处为一个一对多关系''' 
    followed = db.relationship('Follow',foreign_keys=[Follow.follower_id],backref=db.backref('follower',lazy='joined'),\
                               lazy='dynamic',cascade='all,delete-orphan')

    '''粉丝,此处也为一个一对多关系'''
    followers = db.relationship('Follow',foreign_keys=[Follow.followed_id],backref=db.backref('followed',lazy='joined'),
                               lazy='dynamic',cascade='all,delete-orphan')
    
    '''评论'''
    comments = db.relationship('Comment',backref='author',lazy='dynamic')

    @property
    def followed_posts(self):
        return Post.query.join(Follow,Follow.followed_id==Post.author_id).filter(Follow.follower_id==self.id)

    def __repr__(self):
        return '<Role %r>'%self.username

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    '''生成头像'''
    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url,hash=hash,size=size,default=default,rating=rating)

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

    '''生成重设密码的检验令牌'''
    def generate_reset_token(self,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self,token,new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    '''生成重设邮箱地址的检验令牌'''
    def generate_email_change_token(self,new_email,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'change_email':self.id,'new_email':new_email})

    def change_email(self,token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email')!=self.id:
            return False
        new_email = data.get('new_email')
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True
    
    '''检验是否有权限'''
    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions
 
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)
    
    '''检查上次登陆时间'''
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    '''关注关系的辅助方法'''
    def follow(self,user):
        if not self.is_following(user):
            f = Follow(follower=self,followed=user)
            db.session.add(f)
    def unfollow(self,user):
        f = self.followed.filter_by(followed_id = user.id).first()
        if f:
            db.session.delete(f)
    def is_following(self,user):
        return self.followed.filter_by(followed_id = user.id).first() is not None
    def is_followed_by(self,user):
        return self.follwers.filter_by(follower_id = user.id).first() is not None


'''检查匿名用户'''
class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

'''博客的文章'''
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment',backref='post',lazy='dynamic')

    '''on_changed_body函数注册在body字段上，是sqlalchemy的set事件监听函数，
    只要body字段改变就调用将文本渲染成html格式，结果保存在body.html中'''
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','blockquote','code','em','i','li','ol','pre','strong','ul','h1','h2','h3','p']
        target.body_html = bleach.linkify(bleach.clean(
                                         markdown(value,output_format='html'),tags=allowed_tags,strip=True
                                        ))
db.event.listen(Post.body,'set',Post.on_changed_body)












