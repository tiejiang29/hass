import json
import time
from urllib import request, parse
import logging
from datetime import timedelta
import voluptuous as vol
import requests
 
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
import homeassistant.util.dt as dt_util
 
_LOGGER = logging.getLogger(__name__)

TIME_BETWEEN_UPDATES = timedelta(seconds=60)
# 配置文件中平台下的配置项

CONF_APP_KEY = 'appKey'
CONF_APP_SECRET = 'appSecret'
CONF_Device_Serial='deviceSerial'
CONF_OPTIONS = "options"
# 定义三个可选项
# 格式：配置项名称:[OBJECT_ID, friendly_name, icon, 单位]
OPTIONS = {
    "sceneStatus": ["ezviz_sceneStatus", "遮蔽状态", "mdi:eye-off", ""],
    "privacyStatus": ["ezviz_privacyStatus", "隐私状态", "mdi:looks", ""],
    "pirStatus": ["ezviz_pirStatus", "红外状态", "mdi:camcorder-box", ""],
    "alarmSoundMode": ["ezviz_alarmSoundMode", "告警模式", "mdi:surround-sound", ""],
}

ATTR_UPDATE_TIME = "更新时间"
ATTRIBUTION = "C6CN"

# 扩展基础的SCHEMA。在我们这个platform上，设备编号是必须要配置的项
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_Device_Serial): cv.string,
    vol.Required(CONF_APP_KEY): cv.string,
    vol.Required(CONF_APP_SECRET): cv.string,
    vol.Required(CONF_OPTIONS,
                 default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """根据配置文件，setup_platform函数会自动被系统调用."""
    _LOGGER.info("setup platform sensor.ezviz...")

    deviceSerial=config.get(CONF_Device_Serial)
    appKey= config.get(CONF_APP_KEY)
    appSecret= config.get(CONF_APP_SECRET)

    # 定义一个新的数据对象
    data = EZVIZData(hass,deviceSerial,appKey,appSecret)

    # 根据配置文件options中的内容，添加若干个设备
    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(EZVIZSensor(data, option))
    add_devices(dev, True)
    data.regist()

class EZVIZSensor(Entity):
    """定义一个传感器的类，继承自HomeAssistant的Entity类."""

    def __init__(self, data, option):
        """初始化."""
        self._data = data
        self._object_id = OPTIONS[option][0]
        self._friendly_name = OPTIONS[option][1]
        self._icon = OPTIONS[option][2]
        self._unit_of_measurement = OPTIONS[option][3]

        self._type = option
        self._state = None
        self._updatetime = None

    @property
    def name(self):
        """返回实体的名字."""
        return self._object_id

    @property
    def registry_name(self):
        """返回实体的friendly_name属性."""
        return self._friendly_name

    @property
    def state(self):
        """返回当前的状态."""
        return self._state

    @property
    def icon(self):
        """返回icon属性."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """返回unit_of_measuremeng属性."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """设置其它一些属性值."""
        if self._state is not None:
            return {
                ATTR_ATTRIBUTION: ATTRIBUTION,
                # 增加updatetime作为属性，表示获取的时间
                ATTR_UPDATE_TIME: self._updatetime
            }

    def update(self):
        # update只是从EZVIZData中获得数据，数据由EZVIZData维护。
        self._updatetime = self._data.updatetime

        if self._type == "privacyStatus":
            self._state = self._data.privacyStatus
        elif self._type == "sceneStatus":
            self._state = self._data.sceneStatus
        elif self._type == "alarmSoundMode":
            self._state = self._data.alarmSoundMode
        elif self._type == "pirStatus":
            self._state = self._data.pirStatus

class EZVIZData(object):
    """摄像头的数据，存储在这个类中."""
    def __init__(self, hass, deviceSerial,appKey,appSecret):
        """初始化函数."""

        self.hass = hass
        self.deviceSerial = deviceSerial
        self.apikey = {
                "appKey": appKey,
                "appSecret": appSecret
            }
        self.ENTITYID = "ezviz.home"
        self.access_Token = ''

        self._privacyStatus = None
        self._pirStatus = None
        self._sceneStatus = None
        self._alarmSoundMode = None
        self._updatetime = None

        self.update(dt_util.now())
        # 每隔TIME_BETWEEN_UPDATES，调用一次update()
        track_time_interval(hass, self.update, TIME_BETWEEN_UPDATES)

    @property
    def privacyStatus(self):
        """隐私状态"""
        return self._privacyStatus

    @property
    def sceneStatus(self):
        """遮蔽状态"""
        return self._sceneStatus

    @property
    def pirStatus(self):
        """红外状态"""
        return self._pirStatus

    @property
    def alarmSoundMode (self):
        """提醒模式"""
        return self._alarmSoundMode

    @property
    def updatetime(self):
        """更新时间."""
        return self._updatetime

    def update(self, now):
        """从远程更新信息."""
        _LOGGER.info("Update the EZVIZ state...")
        #POST获取数据
        params = {}
        status_url = "https://open.ys7.com/api/lapp/device/status/get"
        scene_url = "https://open.ys7.com/api/lapp/device/scene/switch/status"
        result = self._post(status_url, params)
        if result:
            # 根据http返回的结果，更新数据
            all_result = result['data']
            _LOGGER.debug(all_result)

            if all_result['privacyStatus'] == 1:
                self._privacyStatus = '启用隐私'
            elif all_result['privacyStatus'] == 0:
                self._privacyStatus = '关闭隐私'
            else:
                self._privacyStatus = '不支持'

            if all_result['pirStatus'] == 1:
                self._pirStatus = '启用'
            elif all_result['pirStatus'] == 0:
                self._pirStatus = '关闭'
            else:
                self._pirStatus = '不支持'

            if all_result['alarmSoundMode'] == 0:
                self._alarmSoundMode = '短叫'
            elif all_result['alarmSoundMode'] == 1:
                self._alarmSoundMode = '长叫'
            elif all_result['alarmSoundMode'] == 2:
                self._alarmSoundMode = '静音'
            else:
                self._alarmSoundMode = '禁用或不支持'

        scene = self._post(scene_url, params)
        if scene:
            if scene['data']['enable'] == 1:
                self._sceneStatus = '启用遮蔽'
            else:
                self._sceneStatus = '关闭遮蔽'

        self._updatetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # self._pirStatus= all_result['pirStatus']
        # self._privacyStatus= all_result['privacyStatus']
        # self._alarmSoundMode= all_result['alarmSoundMode']

    def request_token(self) -> str:
        #重新获取access_token
        access_Token = ""
        response = requests.post('https://open.ys7.com/api/lapp/token/get',data=self.apikey).json()
        #访问url
        if response["code"] == "200":
            _LOGGER.info('GET_TOKEN_SUCCESS')
            access_Token = response['data']['accessToken']
            attr = {'access_Token': access_Token}
            self.hass.states.set(self.ENTITYID, 'OK', attributes=attr)
        else:
            _LOGGER.error("Error API return, code=%s, msg=%s",response['code'],response['msg'])
        return  access_Token

    def Get_access_Token(self, isForce=False):
        # 记录info级别的日志
        _LOGGER.info("Update the EZVIZ state...")

        if not self.access_Token:
            entobj = self.hass.states.get(self.ENTITYID)
            if entobj:
                attr = entobj.attributes.copy()
                self.access_Token = attr['access_Token']

        if not self.access_Token:
            self.access_Token = self.request_token()
            return

        if isForce:
            self.access_Token = self.request_token()
        _LOGGER.info('TOKEN_SUCCESS')
        return

    def _post(self, url, data) -> dict:
        # 获取access_Token
        self.Get_access_Token()
        if not self.access_Token:
            _LOGGER.error("Request Token Error")
            return
        default_data = {
            "accessToken": self.access_Token,
            "deviceSerial": self.deviceSerial
        }
        data.update(default_data)
        ret = requests.post(url, data=data, timeout=5)
        if not ret.ok:
            _LOGGER.error("Request Error %s %s", url, str(data))
            return {}

        result = ret.json()
        if not result:
            _LOGGER.error("Request Empty Error %s %s", url, str(data))
            return {}

        code = result.get("code", "0")
        if code != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s, url=%s",
                          code,result['msg'], url)
            return {}

        return result


    def Enable_privacy(self, call):
        ctrl = {"enable": '1'}
        url = 'https://open.ys7.com/api/lapp/device/scene/switch/set'
        if self._post(url, ctrl):
            # 更新传感器状态
            self.hass.states.set('sensor.ezviz_scenestatus', '启用遮蔽')

    def Disable_privacy(self, call):
        ctrl = {"enable": '0'}
        url = 'https://open.ys7.com/api/lapp/device/scene/switch/set'
        if self._post(url, ctrl):
            self.hass.states.set('sensor.ezviz_scenestatus', '关闭遮蔽')

    def Enable_alarm(self, call):
        ctrl = {"isDefence": '1'}
        url = 'https://open.ys7.com/api/lapp/device/defence/set'
        if self._post(url, ctrl):
            # 更新传感器状态
            self.hass.states.set('sensor.ezviz_alarmSoundstatus', '布防')

    def Disable_alarm(self, call):
        ctrl = {"isDefence": '0'}
        url = 'https://open.ys7.com/api/lapp/device/defence/set'
        if self._post(url, ctrl):
            self.hass.states.set('sensor.ezviz_alarmSoundstatus', '撤防')

    def move(self, direc) -> str:
        ctrl = {
                "channelNo": '1',
                "direction": direc,
                "speed": '1'
               }
        start_url = 'https://open.ys7.com/api/lapp/device/ptz/start'
        if not self._post(start_url, ctrl):
            _LOGGER.error("move failed")
            return 'FAIL'

        # 等待0.2s后停止
        time.sleep(0.2)
        ctrl = {
                "channelNo": '1',
                "direction": direc
               }

        stop_url = 'https://open.ys7.com/api/lapp/device/ptz/stop'
        if not self._post(stop_url, ctrl):
            return 'FAIL'
        return 'OK'

    def up(self, call):
        self.move(0)

    def down(self, call):
        self.move(1)

    def left(self, call):
        self.move(2)

    def right(self, call):
        self.move(3)

    def upleft(self, call):
        self.move(4)

    def downleft(self,call):
        self.move(5)

    def upright(self, call):
        self.move(6)

    def downright(self, call):
        self.move(7)

    def stop(self, call):
        ctrl = {
                "channelNo": '1'
               }
        url ='https://open.ys7.com/api/lapp/device/ptz/stop'

        trytimes = 2
        for idx in range(trytimes):
            if self._post(url, ctrl):
                break
        return

    def regist(self):
        # 注册服务
        DOMAIN = "ezviz"
        self.hass.services.register(DOMAIN, 'enable_privacy', self.Enable_privacy)
        self.hass.services.register(DOMAIN, 'disable_privacy', self.Disable_privacy)
        self.hass.services.register(DOMAIN, 'enable_alarm', self.Enable_alarm)
        self.hass.services.register(DOMAIN, 'disable_alarm', self.Disable_alarm)
        self.hass.services.register(DOMAIN, 'up', self.up)
        self.hass.services.register(DOMAIN, 'down', self.down)
        self.hass.services.register(DOMAIN, 'left', self.left)
        self.hass.services.register(DOMAIN, 'right', self.right)
        self.hass.services.register(DOMAIN, 'upright', self.upright)
        self.hass.services.register(DOMAIN, 'downright', self.downright)
        self.hass.services.register(DOMAIN, 'upleft', self.upleft)
        self.hass.services.register(DOMAIN, 'downleft', self.downleft)
        self.hass.services.register(DOMAIN, 'stop', self.stop)

        return True
