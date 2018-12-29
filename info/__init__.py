from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from config import config_dict

# 只是申明了db对象而已,并没有做真实的数据库初始化操作
db = SQLAlchemy()

# 将redis_store对象申明为全局变量
# # type:StrictRedis --> 提前申明redis_store数据类型
redis_store = None  # type:StrictRedis


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

    # 5.借助session调整flask.session的存储位置到redis中存储
    Session(app)

    # return app, db, redis_store
    return app
