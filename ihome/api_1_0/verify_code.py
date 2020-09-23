# coding:utf-8

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants
from flask import current_app, jsonify, make_response
from ihome.utils.response_code import RET


@api.route("/get_image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    前端获取验证码
    :return:    验证码图片  异常：返回json
    """
    # 业务逻辑处理
    # 生产验证码图片
    # 名字，真是文本，图片数据
    name, text, image_data = captcha.generate_captcha()

    # 将验证码真实值与编号保存到redis中，设置有效期
    # redis数据类型：字符串 列表  哈希  set
    # "key"：xxx
    # 使用哈希维护有效期的时候只能整体设置
    # image_codes:{"":"","":""}

    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    #                       名字                          有效期                             记录值
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg="save image code id failed")
    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp
