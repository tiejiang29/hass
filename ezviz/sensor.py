import time
import logging
from datetime import timedelta
import voluptuous as vol
from requests.exceptions import RequestException
from requests_futures.sessions import FuturesSession

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
    "alarmSoundMode": ["ezviz_alarmSoundMode", "告警声音模式", "mdi:surround-sound", ""],
    "defenceStatus":["ezviz_defenceStatus", "布防状态", "mdi:shield-home", ""],
    "onlineStatus": ["ezviz_onlineStatus", "在线状态", "mdi:link", ""],
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
        elif self._type == "defenceStatus":
            self._state = self._data.defenceStatus
        elif self._type == "onlineStatus":
            self._state = self._data.onlineStatus

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
        self._defenceStatus = None
        self._onlineStatus = None
        self._updatetime = None
        self.session = FuturesSession()

        self.update(dt_util.now())
        # 每隔TIME_BETWEEN_UPDATES，调用一次update()
        track_time_interval(hass, self.update, TIME_BETWEEN_UPDATES)

    @property
    def privacyStatus(self):
        """隐私状态"""
        return self._privacyStatus

    @property
    def defenceStatus(self):
        """布防状态"""
        return self._defenceStatus

    @property
    def onlineStatus(self):
        """机器在线状态"""
        return self._onlineStatus

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
        _LOGGER.debug("Update the EZVIZ state...")
        #POST获取数据
        params = {}
        status_url = "https://open.ys7.com/api/lapp/device/status/get"
        result = self._post(status_url, params)
        if result:
            # 根据http返回的结果，更新数据
            all_result = result['data']

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

        self.get_sceneStatus()
        self.get_deviceInfo()

        self._updatetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def get_sceneStatus(self):
        params = {}
        scene_url = "https://open.ys7.com/api/lapp/device/scene/switch/status"
        scene = self._post(scene_url, params)
        if scene:
            if scene['data']['enable'] == 1:
                self._sceneStatus = '启用遮蔽'
            else:
                self._sceneStatus = '关闭遮蔽'

    def get_deviceInfo(self):
        #布防开关(活动状态检测开关)
        url = "https://open.ys7.com/api/lapp/device/info"
        params = {}
        ret = self._post(url, params)
        retdata = ret.get("data", {})
        defence = retdata.get("defence", 0)
        if defence == 0:
            self._defenceStatus = "撤防"
        else:
            self._defenceStatus = "布防"

        #设备是否在线
        online = retdata.get("status", 0)
        if online == 0:
            self._onlineStatus = "离线"
        else:
            self._onlineStatus = "在线"


    def request_token(self) -> str:
        #重新获取access_token
        access_Token = ""
        response_async = self.session.post('https://open.ys7.com/api/lapp/token/get',data=self.apikey)
        try:
            response = response_async.result().json()
        except RequestException as ex:
            _LOGGER.error(ex)
            return ""

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
        _LOGGER.debug('TOKEN_SUCCESS')
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
        trytimes = 2
        ret = None
        for tryidx in range(trytimes):
            ret_async = self.session.post(url, data=data, timeout=5)
            ret = ret_async.result()
            if not ret.ok:
                _LOGGER.warning("Request Error %s %s", url, str(data))
                continue
            break

        if not ret or not ret.ok:
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


    def enable_sence(self, call):
        ctrl = {"enable": '1'}
        url = 'https://open.ys7.com/api/lapp/device/scene/switch/set'
        if self._post(url, ctrl):
            # 更新传感器状态
            self._sceneStatus = "启用遮蔽"
            self.hass.states.set('sensor.ezviz_sceneStatus', self._sceneStatus)
            _LOGGER.info("enable sence")

    def disable_sence(self, call):
        ctrl = {"enable": '0'}
        url = 'https://open.ys7.com/api/lapp/device/scene/switch/set'
        if self._post(url, ctrl):
            self._sceneStatus = "关闭遮蔽"
            self.hass.states.set('sensor.ezviz_sceneStatus', self._sceneStatus)
            _LOGGER.info("disable sence")

    def enable_defence(self, call):
        #活动检测开关
        ctrl = {"isDefence": '1'}
        url = 'https://open.ys7.com/api/lapp/device/defence/set'
        if self._post(url, ctrl):
            # 更新传感器状态
            self._defenceStatus = "布防"
            self.hass.states.set('sensor.ezviz_defenceStatus', '布防')
            _LOGGER.info("enable defence")

    def disable_defence(self, call):
        ctrl = {"isDefence": '0'}
        url = 'https://open.ys7.com/api/lapp/device/defence/set'
        if self._post(url, ctrl):
            self._defenceStatus = "撤防"
            self.hass.states.set('sensor.ezviz_defenceStatus', '撤防')
            _LOGGER.info("disable defence")

    def move(self, direc) -> str:
        if not self.start(direc):
            _LOGGER.error("move failed")
            return 'FAIL'

        # 等待0.2s后停止
        time.sleep(0.2)

        if not self.stop(direc):
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

    def start(self, direc) -> bool:
        ctrl = {
                "channelNo": '1',
                "direction": direc,
                "speed": '1'
               }
        start_url = 'https://open.ys7.com/api/lapp/device/ptz/start'
        return self._post(start_url, ctrl)

    def stop(self, call) -> bool:
        ctrl = {
            "channelNo": '1',
            "direction": call,
        }
        url = 'https://open.ys7.com/api/lapp/device/ptz/stop'
        return self._post(url, ctrl)

    def regist(self):
        # 注册服务
        DOMAIN = "ezviz"
        self.hass.services.register(DOMAIN, 'enable_sence', self.enable_sence)
        self.hass.services.register(DOMAIN, 'disable_sence', self.disable_sence)
        self.hass.services.register(DOMAIN, 'enable_defence', self.enable_defence)
        self.hass.services.register(DOMAIN, 'disable_defence', self.disable_defence)
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
