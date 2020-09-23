# coding:utf-8

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
import random

from ronglian_sms_sdk import SmsSDK


@api.route("/image_codes/<image_code_id>")
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


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}]'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")
    # 校验参数
    if not all([image_code, image_code_id]):
        # 表示参数不完整
        return jsonify(error=RET.PARAMERR, errmsg="参数不完整")

    # 业务逻辑处理
    # 从redis中取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg="redis数据库异常")

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示图片验证码没有或者过期
        return jsonify(error=RET.NODATA, errmsg="图片验证码失效")
    # 与用户填写的值进行对比
    if real_image_code.lower() != image_code.lower():
        # 表示用户填写错误
        return jsonify(error=RET.DATAERR, errmsg="图片验证码错误")

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号已存在
            return jsonify(error=RET.DATAEXIST, errmsg="手机号已存在")

    # 如果手机号不存在，则生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg="保存短信验证码异常")

    # 发送短信
    accId = '8a216da874af5fff0174b997014c04eb'
    accToken = '91ca470532d049d9ae2bc3726d9036c4'
    appId = '8a216da874af5fff0174b997025604f2'

    def send_message():
        sdk = SmsSDK(accId, accToken, appId)
        tid = '1'
        mobile = '18168580698'
        datas = ('1', '2')
        resp = sdk.sendMessage(tid, mobile, datas)
        print(resp)
        return resp

    try:
        result = send_message()
        if result == 0:
            # 发送成功
            return jsonify(error=RET.OK, errmsg="发送成功")
        else:
            return jsonify(error=RET.THIRDERR, errmsg="发送失败")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.THIRDERR, errmsg="发送异常")

    # 返回值
