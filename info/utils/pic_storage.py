import qiniu

# 直接使用老师创建的空间
access_key = "W0oGRaBkAhrcppAbz6Nc8-q5EcXfL5vLRashY4SI"
secret_key = "tsYCBckepW4CqW0uHb9RdfDMXRDOTEpYecJAMItL"

# 上传的图片的空间名称
bucket_name = "information22"


# data --> 上传图片的二进制数据
def pic_storage(data):
    """上传用户图片数据到七牛云平台"""

    if not data:
        raise AttributeError("图片数据为空")

    # 权限验证
    q = qiniu.Auth(access_key, secret_key)
    # 上传的图片名称
    # 如果不设置key,七牛云会自动给图片分配一个图片名称,而且是唯一的
    # key = 'hello'

    token = q.upload_token(bucket_name)

    # 上传图片数据到七牛云
    ret, info = qiniu.put_data(token, None, data)

    print(ret)
    print("-----------------------")
    print(info)

    # 封装的工具类,给别人调用,一旦产生异常一定要抛出不能私自解决,如果私自解决了,别人就不知道错误发生在什么地方
    if ret is not None:
        print('All is OK')
    else:
        # 抛出异常
        raise AttributeError("上传图片到七牛云失败")

    if info.status_code == 200:
        print("上传图片成功")
    else:
        raise AttributeError("上传图片到七牛云失败")

    return ret['key']


if __name__ == '__main__':
    file_name = input("输入上传的文件:")
    with open(file_name, "rb") as f:
        print(pic_storage(f.read()))
