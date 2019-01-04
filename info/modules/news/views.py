from . import news_bp
from flask import render_template


# 127.0.0.1:5000/news/news_id  news_id:新闻对应的id地址
@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """新闻详情页展示"""
    return render_template("news/detail.html")
