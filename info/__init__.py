from flask import Flask, render_template, g
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config import config_dict
import logging
from logging.handlers import RotatingFileHandler
from info.utils.common import do_index_class, get_user_data

# 只是申明了db对象而已,并没有做真实的数据库初始化操作

db = SQLAlchemy()

# 将redis_store对象申明为全局变量
# # type:StrictRedis --> 提前申明redis_store数据类型
redis_store = None  # type:StrictRedis


def write_log(config_class):
    """配置记录日志方法"""

    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小: 100M、保存的日志文件个数上限
    # bug: 当maxBytes的值设得太小的时候, windows中会出现logging模块多进程问题:
    # PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。:
    # 'D:\\Study\\szhm_Python22_Coding\\ProjectsWebFlask\\NewsInfo\\logs\\log' ->
    # 'D:\\Study\\szhm_Python22_Coding\\ProjectsWebFlask\\NewsInfo\\logs\\log.1'
    # 解决方案: https://blog.csdn.net/chongtong/article/details/80831782
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024**100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    #                 DEBUG   index.py         100 name
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 将app封装起来,给外界调用提供一个接口
# development ---> 返回的是开发模式的app对象
# production  ---> 返回的是生产(线上)模式的app对象
def create_app(config_name):
    """
    将与app相关联的配置封装到'工厂方法'中
    :param config_name: 定义需要创建哪种类型的app对象
    :return: app对象
    """
    # 1.创建app对象,并从配置类加载配置信息
    app = Flask(__name__)
    # 根据development键获取对应的配置类名
    config_class = config_dict[config_name]
    # DevelopmentConfig ---> 开发模式的app对象
    # ProductionConfig --->  线上模式的app对象
    app.config.from_object(config_class)

    # DevelopmentConfig.LOG_LEVEL = DEBUG
    # ProductionConfig.LOG_LEVEL = ERROR
    # 1.1.记录日志
    write_log(config_class)

    # 2.创建mysql数据库对象
    # if app is not None:
    #     self.init_app(app)
    # 延迟加载,懒加载思想,当app有值的时候才进行真正的初始化操作
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 3.创建redis数据库对象(懒加载的思想)
    """
    redis_store.set("age", 18)  ---> 存储到redis -- 0号数据库
    session["name"] = "curry"   ---> 存储到redis -- 1号数据库
    """
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 4.开启后端的CSRF保护机制
    """
    Checks the ``csrf_token`` field sent with forms, or the ``X-CSRFToken``
    header sent with JavaScript requests. Render the token in templates using``{{ csrf_token() }}``.
    
    底层:
        1.提取cookie中的csrf_token的值
        2.提取表单中的csrf_token的值,或者ajax请求头中的X-CSRFToken键对应的值
        3.对比这两个值是否相等
    """
    CSRFProtect(app)

    # 在每一次请求之后,都设置一个csrf_token值
    @app.after_request
    def set_csrf_token(response):
        # 1.生成csrf_token随机值
        csrf_token = generate_csrf()
        # 2.借助响应对象将csrf_token保存到cookie中
        response.set_cookie("csrf_token", csrf_token)
        # 3.将响应对象返回
        return response

    # 捕获404异常,返回统一404页面
    @app.errorhandler(404)
    @get_user_data
    def handle_404_not_found(e):

        # 1.查询用户基本信息
        user = g.user

        data = {
            "user_info": user.to_dict() if user else None
        }

        # 返回404模板数据,同时传入用户信息
        return render_template("news/404.html", data=data)

    # 添加自定义过滤器
    app.add_template_filter(do_index_class, "do_index_class")

    # 5.借助session调整flask.session的存储位置到redis中存储
    Session(app)

    # 6.注册首页蓝图
    # 将蓝图的导入延迟到工厂方法中,真正需要注册蓝图的时候再导入,能够解决循环导入的问题
    from info.modules.index import index_bp
    app.register_blueprint(index_bp)

    # 登录注册模块的蓝图
    from info.modules.passport import passport_bp
    app.register_blueprint(passport_bp)

    # 新闻详情页模块的蓝图
    from info.modules.news import news_bp
    app.register_blueprint(news_bp)

    # 个人中心模块的蓝图
    from info.modules.profile import profile_bp
    app.register_blueprint(profile_bp)

    # 管理后台模块的蓝图
    from info.modules.admin import admin_bp
    app.register_blueprint(admin_bp)

    # return app, db, redis_store
    return app
