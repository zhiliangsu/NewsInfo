from flask import Blueprint

# 1.创建蓝图对象
passport_bp = Blueprint("passport", __name__, url_prefix="/passport")

# 3.让包知道views文件中的视图函数
from .views import *
