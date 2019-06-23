"""
用途：以服务方式控制萤石摄像头
版本：V0.1
依赖：ezviz/sensor.py控件
"""

import json
from urllib import request, parse
import logging
import requests
from time import sleep

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
 
 
_LOGGER = logging.getLogger(__name__)
 
DOMAIN = "ezvizctrl"
ENTITYID = DOMAIN + ".home"

# 预定义配置文件中的key值
CONF_DEVICESERIAL = "deviceSerial"
CONF_APPKEY = "appKey"
CONF_APPSECRET = "appSecret"


# 在python中，__name__代表模块名字
_LOGGER = logging.getLogger(__name__)

# 配置文件的样式
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_DEVICESERIAL): cv.string,
                vol.Required(CONF_APPKEY): cv.string,
                vol.Required(CONF_APPSECRET): cv.string,	
            }),
    },
    extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """配置文件加载后，setup被系统调用."""
    conf = config[DOMAIN]
    deviceSerial = conf.get(CONF_DEVICESERIAL)
    appKey = conf.get(CONF_APPKEY)
    appSecret = conf.get(CONF_APPSECRET)

    access_Token = ''
    attr = {"access_Token": access_Token,}

    hass.states.set(ENTITYID, 'OK', attributes=attr)
    
    def Get_access_Token():
        # 记录info级别的日志
        _LOGGER.info("Update the EZVIZ state...")
        attr = hass.states.get(ENTITYID).attributes.copy()
        access_Token = attr['access_Token']
        params = {"accessToken": access_Token,
                  "deviceSerial": deviceSerial
                 }
        apikey = {"appKey": appKey,
                  "appSecret": appSecret
                 }
        # 检查access_token是否有效
        statusCode = requests.post('https://open.ys7.com/api/lapp/device/list',data=params).json()["code"]
        if statusCode == "200":
            _LOGGER.info('TOKEN_SUCCESS')
        else:
            #重新获取access_token
            response = requests.post('https://open.ys7.com/api/lapp/token/get',data=apikey).json()
            #访问url
            if response["code"] == "200":
                _LOGGER.info('GET_TOKEN_SUCCESS')
                access_Token = response['data']['accessToken']
                attr['access_Token'] = access_Token
                hass.states.set(ENTITYID, 'OK', attributes=attr)
            else:
                _LOGGER.error("Error API return, code=%s, msg=%s",response['code'],response['msg'])
                return
        return access_Token

    def Enable_privacy(call):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "enable": '1'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/scene/switch/set',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return
        # 更新传感器状态
        hass.states.set('sensor.ezviz_privacystatus', '启用遮蔽')

    def Disable_privacy(call):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "enable": '0'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/scene/switch/set',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return
        hass.states.set('sensor.ezviz_privacystatus', '关闭遮蔽')

    def Enable_alarm(call):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "isDefence": '1'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/defence/set',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return
        # 更新传感器状态
        hass.states.set('sensor.ezviz_alarmstatus', '布防')

    def Disable_alarm(call):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "isDefence": '0'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/defence/set',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return
        # 更新传感器状态
        hass.states.set('sensor.ezviz_alarmstatus', '撤防')

    def move(direc):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "channelNo": '1',
                "direction": direc,
                "speed": '1'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/ptz/start',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return
        # 等待0.2s后停止
        sleep(0.2)
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "channelNo": '1',
                "direction": direc
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/ptz/stop',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            ##防止因为意外再次执行停止
            result = requests.post('https://open.ys7.com/api/lapp/device/ptz/stop',data=ctrl).json()
            if result["code"] != "200":
                _LOGGER.error("Error API return, code=%s, msg=%s",
                              result['code'],result['msg'])
                return
        return 'OK'

    def up(call):
        result = move(0)
        if result is None:
            _LOGGER.error("move failed")
            return

    def down(call):
        result = move(1)
        if result is None:
            _LOGGER.error("move failed")
            return

    def left(call):
        result = move(2)
        if result is None:
            _LOGGER.error("move failed")
            return

    def right(call):
        result = move(3)
        if result is None:
            _LOGGER.error("move failed")
            return

    def upleft(call):
        result = move(4)
        if result is None:
            _LOGGER.error("move failed")
            return

    def downleft(call):
        result = move(5)
        if result is None:
            _LOGGER.error("move failed")
            return

    def upright(call):
        result = move(6)
        if result is None:
            _LOGGER.error("move failed")
            return

    def downright(call):
        result = move(7)
        if result is None:
            _LOGGER.error("move failed")
            return
        
    def stop(call):
        # 获取access_Token
        access_Token = Get_access_Token()
        if access_Token is None:
            _LOGGER.error("Request Token Error")
            return
        ctrl = {"accessToken": access_Token,
                "deviceSerial": deviceSerial,
                "channelNo": '1'
               }
        result = requests.post('https://open.ys7.com/api/lapp/device/ptz/stop',data=ctrl).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            ##防止因为意外再次执行停止
            result = requests.post('https://open.ys7.com/api/lapp/device/ptz/stop',data=ctrl).json()
            if result["code"] != "200":
                _LOGGER.error("Error API return, code=%s, msg=%s",
                             result['code'],result['msg'])
                return

    # 注册服务
    hass.services.register(DOMAIN, 'Enable_privacy', Enable_privacy)
    hass.services.register(DOMAIN, 'Disable_privacy', Disable_privacy)    
    hass.services.register(DOMAIN, 'Enable_alarm', Enable_alarm)
    hass.services.register(DOMAIN, 'Disable_alarm', Disable_alarm)
    hass.services.register(DOMAIN, 'up', up)
    hass.services.register(DOMAIN, 'down', down)
    hass.services.register(DOMAIN, 'left', left)
    hass.services.register(DOMAIN, 'right', right)
    hass.services.register(DOMAIN, 'upright', upright)
    hass.services.register(DOMAIN, 'downright', downright)
    hass.services.register(DOMAIN, 'upleft', upleft)
    hass.services.register(DOMAIN, 'downleft', downleft)    
    hass.services.register(DOMAIN, 'stop', stop)

    return True
