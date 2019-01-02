from info.modules.index import index_bp
import logging
from flask import current_app, render_template
from info import redis_store
from info.models import User


@index_bp.route('/')
def index():
    # 设置redis键值对
    redis_store.set("name", "bryant")
    print(redis_store.get("name"))

    # 日志的使用
    logging.debug("我的debug信息")
    logging.info("我的info信息")
    logging.warning("我的warning信息")
    logging.error("我的error信息")
    logging.critical("我的critical信息")

    # flask中记录日志方法(项目使用这种方式记录)
    current_app.logger.debug("flash记录debug信息")
    # 返回渲染模板文件
    return render_template("news/index.html")


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
