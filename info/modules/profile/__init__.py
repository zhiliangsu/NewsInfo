from flask import Blueprint

# 1.创建蓝图对象
profile_bp = Blueprint("profile", __name__, url_prefix="/user")

# 3.让包知道views文件中的视图函数
from .views import *
