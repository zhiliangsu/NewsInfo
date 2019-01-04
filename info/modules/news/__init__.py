from flask import Blueprint

# 1.创建蓝图对象
news_bp = Blueprint("news", __name__, url_prefix="/news")

# 3.让包知道views文件中的视图函数
from info.modules.news.views import *