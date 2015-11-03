#!/usr/bin/env python
# coding=utf-8
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .models import Permission

'''
functiontools.partial 偏函数，函数式编程思想
用一些默认参数包装一个可调用对象，返回结果是可调用对象，并且可以像原始对象一样对待
冻结部分函数位置函数或关键字参数，简化函数，更少更灵活的函数参数调用
http://www.wklken.me/posts/2013/08/18/python-extra-functools.html
'''
def permission_required(permission):
    def decorator(f):
        @wraps(f) #使用了Python标准库中的functools包
                  #调用函数装饰器partial(update_wrapper, wrapped=wrapped, assigned=assigned, updated=updated)的简写
        def decorator_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorator_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
