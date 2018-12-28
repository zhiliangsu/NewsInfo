from redis import StrictRedis


# 0.创建配置类(父类)
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


class DevelopmentConfig(Config):
    """开发模式的配置类"""
    DEBUG = True


class ProductionConfig(Config):
    """生产(线上)模式的配置类"""
    DEBUG = False


# 给外界使用提供一个接口
# 使用: config_dict["development"] ---> DevelopmentConfig
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}
