# 使用说明
1、将下载的插件中两个文件夹复制到custom_components目录下<br/>
2、key和secret请在萤石开发网站获取，具体可详见https://bbs.hassbian.com/thread-7062-1-1.html<br/>
3、在configuration.yaml文件中添加以下内容启用插件<br/>

~~~
ezvizctrl:
  deviceSerial: ****设备序列号
  appKey: ****api接口里面的appkey
  appSecret: ****api接口里面的appsecret
sensor:
  - platform: ezviz
    appKey: ****
    appSecret: ****
    deviceSerial: ***
    scan_interval: 30
    options: 
      - privacyStatus
      - AlarmStatus
      - alarmSoundMode
~~~
4、在configuration.yaml添加两个开关，用于修改移动侦测和遮蔽状态
~~~
switch:
  - platform: template
    switches:
      privacy:
        friendly_name: 镜头遮蔽
        value_template: "{{ is_state('sensor.ezviz_privacystatus', '启用遮蔽') }}"
        turn_on:
          service: ezvizctrl.enable_privacy
        turn_off:
          service: ezvizctrl.disable_privacy
        icon_template: >-
          {% if is_state('sensor.ezviz_privacystatus', '启用遮蔽') %}
            mdi:eye-off
          {% else %}
            mdi:eye
          {% endif %}
  - platform: template
    switches:
      alarm:
        friendly_name: 移动侦测
        value_template: "{{ is_state('sensor.ezviz_alarmstatus', '布防') }}"
        turn_on:
          service: ezvizctrl.enable_alarm
        turn_off:
          service: ezvizctrl.disable_alarm
        icon_template: >-
          {% if is_state('sensor.ezviz_alarmstatus', '布防') %}
            mdi:shield-home
          {% else %}
            mdi:shield-off
          {% endif %}
~~~
5、在lovelace上面添加控制界面
首先安装 radial-menu 插件，https://github.com/custom-cards/radial-menu
将如下代码，通过原始编辑器，在合适的位置添加进去
~~~
- cards:
   - entities:
       - switch.privacy
       - switch.alarm
       - sensor.ezviz_alarmsoundmode
     show_header_toggle: false
     title: 摄像机状态
     type: entities
   - default_dismiss: false
     default_open: true
     icon: 'mdi:webcam'
     items:
       - entity: null
         icon: 'mdi:arrow-up-thick'
         name: 上
         tap_action:
           action: call-service
           service: ezvizctrl.up
       - entity: null
         icon: 'mdi:arrow-right-thick'
         name: 右
         tap_action:
           action: call-service
           service: ezvizctrl.right
       - entity: null
         icon: 'mdi:arrow-down-thick'
         name: 下
         tap_action:
           action: call-service
           service: ezvizctrl.down
       - entity: null
         icon: 'mdi:arrow-left-thick'
         name: 左
         tap_action:
           action: call-service
           service: ezvizctrl.left
     name: 家
     type: 'custom:radial-menu'
 type: vertical-stack

6、enjoyit
~~~
