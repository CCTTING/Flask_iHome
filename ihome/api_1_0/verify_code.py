# coding:utf-8

from . import api

@api.route("/get_image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    前端获取验证码
    :return:    验证码图片
    """
    # 业务逻辑处理
    # 生产验证码图片
    #