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
    "privacyStatus": ["ezviz_privacyStatus", "遮蔽状态", "", ""],
    "AlarmStatus": ["ezviz_AlarmStatus", "移动侦测", "", ""],
    "alarmSoundMode": ["ezviz_alarmSoundMode", "报警音模式", "mdi:surround-sound", ""],
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

    # 定义一个新的数据对象，用于获取萤石API数据。
    data = EZVIZData(hass,deviceSerial,appKey,appSecret)
 
    # 根据配置文件options中的内容，添加若干个设备
    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(EZVIZSensor(data, option))
    add_devices(dev, True)
 
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
        elif self._type == "alarmSoundMode":
            self._state = self._data.alarmSoundMode 
        elif self._type == "AlarmStatus":
            self._state = self._data.AlarmStatus

class EZVIZData(object):
    """摄像头的数据，存储在这个类中."""
    def __init__(self, hass, deviceSerial,appKey,appSecret):
        """初始化函数."""
        self._params = {"accessToken": "",
                        "deviceSerial": deviceSerial
                        }
        self._apikey = {"appKey": appKey,
                        "appSecret": appSecret
                        }
        self._privacyStatus = None
        self._AlarmStatus = None
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
    def AlarmStatus(self):
        """报警状态"""
        return self._AlarmStatus
 
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
        statusCode = requests.post('https://open.ys7.com/api/lapp/device/list',data=self._params).json()["code"]
        if statusCode == "200":
            _LOGGER.info('TOKEN_SUCCESS')
        else:
            response = requests.post('https://open.ys7.com/api/lapp/token/get',data=self._apikey).json()
            #访问url
            if response["code"] == "200":
                _LOGGER.info('GET_TOKEN_SUCCESS')
                self._params["accessToken"] = response['data']['accessToken']
            else:
                _LOGGER.error("Error API return, code=%s, msg=%s",response['code'],response['msg'])
            return
        #POST获取数据
            
        result = requests.post('https://open.ys7.com/api/lapp/device/info',data=self._params).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return

        # 根据http返回的结果，更新数据
        all_result = result['data']
        # _LOGGER.error(all_result)

        if all_result['defence'] == 1:
            self._AlarmStatus = '布防'
        else:
            self._AlarmStatus = '撤防'
            
        if all_result['alarmSoundMode'] == 0:
            self._alarmSoundMode = '短叫'
        elif all_result['alarmSoundMode'] == 1:
            self._alarmSoundMode = '长叫'
        elif all_result['alarmSoundMode'] == 2:
            self._alarmSoundMode = '静音'
        else:
            self._alarmSoundMode = '禁用或不支持'
            
        result = requests.post('https://open.ys7.com/api/lapp/device/scene/switch/status',data=self._params).json()
        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "200":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result['code'],result['msg'])
            return

        # 根据http返回的结果，更新数据
        all_result = result['data']
        if all_result['enable'] == 1:
            self._privacyStatus = '启用遮蔽'
        else:
            self._privacyStatus = '关闭遮蔽'

        
        self._updatetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
