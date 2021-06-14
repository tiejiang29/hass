# 使用说明
1. 将下载的插件中的`ezviz`文件夹复制到`custom_components`目录下
2. `key`和`secret`请在[萤石开发网站](https://bbs.hassbian.com/thread-7062-1-1.html)获取
3. 在`configuration.yaml`文件中添加以下内容启用插件

```yaml
sensor:
  - platform: ezviz
    appKey: ****
    appSecret: ****
    deviceSerial: ***
    scan_interval: 30
    options: 
      - sceneStatus
      - privacyStatus
      - pirStatus
      - alarmSoundMode
      - defenceStatus
      - onlineStatus
```

4. 在`configuration.yaml`添加两个开关，用于修改移动侦测和遮蔽状态
```yaml
switch:
  - platform: template
    switches:
      sence:
        friendly_name: 镜头遮蔽
        value_template: "{{ is_state('sensor.ezviz_sceneStatus', '启用遮蔽') }}"
        turn_on:
          service: ezviz.enable_sence
        turn_off:
          service: ezviz.disable_sence
        icon_template: >-
          {% if is_state('sensor.ezviz_sceneStatus', '启用遮蔽') %}
            mdi:eye-off
          {% else %}
            mdi:eye
          {% endif %}
  - platform: template
    switches:
      defence:
        friendly_name: 布防状态(活动检测)
        value_template: "{{ is_state('sensor.ezviz_defenceStatus', '布防') }}"
        turn_on:
          service: ezviz.enable_defence
        turn_off:
          service: ezviz.disable_defence
        icon_template: >-
          {% if is_state('sensor.ezviz_defenceStatus', '布防') %}
            mdi:shield-home
          {% else %}
            mdi:shield-off
          {% endif %}
```
5. 安装 [radial-menu](https://github.com/custom-cards/radial-menu) 插件
6. 将如下代码，通过原始编辑器，在合适的位置添加进去
```yaml
    cards:
      - type: entities
        entities:
          - entity: switch.sence
          - entity: switch.defence
          - entity: sensor.ezviz_alarmsoundmode
            name: 告警声音模式
          - entity: sensor.ezviz_onlinestatus
            name: 在线状态
          - entity: sensor.ezviz_privacystatus
            name: 隐私状态
        show_header_toggle: false
        title: 摄像机状态
      - default_dismiss: false
        default_open: true
        icon: 'mdi:webcam'
        items:
          - entity: null
            icon: 'mdi:arrow-up-thick'
            name: 上
            tap_action:
              action: call-service
              service: ezviz.up
          - entity: null
            icon: 'mdi:arrow-right-thick'
            name: 右
            tap_action:
              action: call-service
              service: ezviz.right
          - entity: null
            icon: 'mdi:arrow-down-thick'
            name: 下
            tap_action:
              action: call-service
              service: ezviz.down
          - entity: null
            icon: 'mdi:arrow-left-thick'
            name: 左
            tap_action:
              action: call-service
              service: ezviz.left
        name: 家
        type: 'custom:radial-menu'

 ```
7. enjoyit

