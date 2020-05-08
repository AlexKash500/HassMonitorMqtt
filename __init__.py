
import logging
import re
import sys
from subprocess import check_output, CalledProcessError

import voluptuous as vol

import homeassistant.loader as loader
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv
from homeassistant.components import recorder
from homeassistant.components.sensor import (DOMAIN, PLATFORM_SCHEMA)
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.components.mqtt import (
    ATTR_DISCOVERY_HASH,
    CONF_QOS,
    CONF_UNIQUE_ID,
    MqttAttributes,
    MqttAvailability,
    MqttDiscoveryUpdate,
    MqttEntityDeviceInfo,
    subscription,
)

DEPENDENCIES = ["mqtt"]

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "monitor_mqtt"

CONF_CLIENT_NAME = "client_name"
DEFAULT_CLIENT_NAME = "computer"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_NAME, default=DEFAULT_CLIENT_NAME): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

inbox_information = [{'id':'ram', 'name': 'ram_used_percentage', 'sensor_label': 'Ram used percentage', 'unity': '%', 'icon': 'mdi:memory'},
                     {'id':'cpu', 'name': 'cpu_used_percentage',
                      'sensor_label': 'CPU used percentage', 'unity': '%', 'icon': 'mdi:calculator-variant'},
                     {'id':'disk', 'name': 'disk_used_percentage',
                      'sensor_label': 'Disk used percentage', 'unity': '%', 'icon': 'mdi:harddisk'},
                     {'id':'os', 'name': 'operating_system',
                      'sensor_label': 'Operating system', 'unity': '', 'icon': 'mdi:$OPERATING_SYSTEM'},
                     {'id':'time', 'name': 'message_time', 'sensor_label': 'Last update time', 'unity': '', 'icon': 'mdi:clock-outline'}]


outbox_information = [{'id':'shutdown', 'name': 'shutdown_command', 'sensor_label': 'Shutdown', 'icon': 'mdi:power'},
                      {'id':'reboot', 'name': 'reboot_command',
                       'sensor_label': 'Reboot', 'icon': 'mdi:restart'},
                      {'id':'lock', 'name': 'lock_command',
                       'sensor_label': 'Lock', 'icon': 'mdi:lock'}
                      ]


async def async_setup(hass, config):

    client_name = config[DOMAIN].get(
        CONF_CLIENT_NAME)
    topic = 'monitor/' + client_name + '/'

    # These hass.data will be passed to the sensors
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['client_name'] = client_name
    hass.data[DOMAIN]['topic'] = topic
    hass.data[DOMAIN]['inbox_information'] = inbox_information
    hass.data[DOMAIN]['outbox_information'] = outbox_information
    hass.data[DOMAIN]['last_message_time'] = None

    def update(call=None):
        """Mqtt updates automatically when messages arrive"""
        pass

    hass.services.async_register(DOMAIN, "monitor", update)

    # Load the sensors - that receive and manage clients messages
    hass.async_create_task(
        async_load_platform(
            hass, SENSOR_DOMAIN, DOMAIN, None,  config
        )
    )

    # Load the scripts - that send tommands to the client
    hass.async_create_task(
        async_load_platform(
            hass, SWITCH_DOMAIN, DOMAIN, None,  config
        )
    )

    hass.async_create_task(
        async_load_platform(
            hass, BINARY_SENSOR_DOMAIN, DOMAIN, None,  config
        )
    )

    return True
