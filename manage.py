from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


# 从单一职责的原则考虑,manage文件单独作为项目启动文件即可,其他配置可以抽取出去


# 0.创建配置类
class Config(object):
    """自定义配置类,将配置信息以属性的方式罗列即可"""
    DEBUG = True

    # mysql数据库配置信息
    # 连接mysql数据库的配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@localhost:3306/NewsInfo"
    # 开启数据库跟踪模式
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis数据库配置信息
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379

    # 使用session记得添加加密字符串对session_id进行加密处理
    SECRET_KEY = "DSFJSLGJSLDJFEWIJGJSDKJ*&^DFDFDS"

    # 将flask中的session存储到redis数据库的配置信息
    # 存储到哪种类型的数据库
    SESSION_TYPE = "redis"
    # 具体将session中的数据存储到哪个redis数据库对象
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1)
    # session存储的数据后产生的session_id需要加密
    SESSION_USE_SIGNER = True
    # 设置非永久存储
    SESSION_PERMANENT = False
    # 设置过期时长,默认过期时长:31天
    PERMANENT_SESSION_LIFETIME = 86400


# 1.创建app对象,并从配置类加载配置信息
app = Flask(__name__)
app.config.from_object(Config)

# 2.创建mysql数据库对象
db = SQLAlchemy(app)

# 3.创建redis数据库对象
"""
redis_store.set("age", 18)  ---> 存储到redis -- 0号数据库
session["name"] = "curry"   ---> 存储到redis -- 1号数据库
"""
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

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

# 6.创建管理对象,将app对象交给管理对象管理起来
manager = Manager(app)

# 7.数据库迁移初始化
Migrate(app, db)

# 8.添加迁移命令
manager.add_command("db", MigrateCommand)


@app.route('/')
def index():
    return "Hello World!"


if __name__ == '__main__':
    # 9.使用manager对象启动flask项目,代替app.run()
    manager.run()
