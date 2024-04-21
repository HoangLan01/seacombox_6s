__author__ = 'osb holding jsc'

import random, sys
import gc
import time
import board
import displayio
import terminalio
import busio
import digitalio
import zlib, json
from adafruit_display_text import label
import adafruit_imageload
import alarm
import adafruit_gps
import microcontroller
import adafruit_dht
import gc

mcu_config_keys = ['seacom_id', 'name', 'vessel_name', 'reg_number', 'acusn', 'imo', 'mmsi', 'callsign', 'antennasn']

mcu_config = {
    'seacom_id': 'KG94081TS',
    "name" : "seacom",
    "vessel_name" : "KG94081TS",
    "reg_number" : "N/A",
    "acusn" : "N/A",
    "imo" : "1600005",
    "mmsi" : "160000005",
    "callsign" : "N/A",
    "modemsn" : "N/A",
    "antennasn" : "N/A",
    'waiting': 10, # 60
    'dhcp':True,
    'network_check': 5, # 120
    'gateway': (10,18,151,33),
    'subnet' : (255,255,225,248),
    'localip' : (192,168,2,88),
    'dns_server':(8,8,8,8),
    'u0targetip' : (113,161,141,78),
    'u0targetport' : 6001,
    'SCREEN_ENABLE': True,
    'IMAGE_FILE':"images/logo.bmp",
    'SPRITE_SIZE':(96, 50),
    'SCREEN_SIZE':(320, 240, 90),
    'SCREEN_BUS':'SPI',
    'display':{
        'SPI':{
            'SCL': board.GP18,
            'MOSI':board.GP19,
            'CS':board.GP17,
            'RESET':board.GP21,
            'DC':board.GP20,
            'size': (320, 240)
        },
        'I2C':{
            'SCL': board.GP1,
            'SDA1':board.GP0,
            'size': (128,64)
        },
    },
    # 'buttons':[UP, DOWN, OK, Exit, SOS, Cancel Alarm] // False when not connect to keyboard
    'buttons_enable':[True, True, True, True, True, True],
    'buttons_GP':[board.GP6, board.GP7, board.GP8, board.GP9, board.GP14, board.GP26],
    'buttons':[None, None, None, None, None, None],
    'SOS_url':'http://seacomcam.com:48000/'
}


gps_has_fix = False
sos_on = False
eth_on = False
sensor_on = False
internet_on = False
priority = False
priority_time = 0
SOS_link = mcu_config['SOS_url']+'sos/'+mcu_config['mmsi']


# screen
speaker = digitalio.DigitalInOut(board.GP15)
speaker.direction = digitalio.Direction.OUTPUT
def buzz(sleep=0.5, step = 1):
    for i in range(0, step):
        speaker.value = True
        time.sleep(sleep)
        speaker.value = False
        time.sleep(sleep*2)

buzz(step=1)

btns_power = digitalio.DigitalInOut(board.GP27)
btns_power.direction = digitalio.Direction.OUTPUT
btns_power.value = True
buttons = mcu_config['buttons']
for i in range(len(mcu_config['buttons_enable'])):
    if mcu_config['buttons_enable'][i]:
        buttons[i] = digitalio.DigitalInOut(mcu_config['buttons_GP'][i])
        buttons[i].direction = digitalio.Direction.INPUT

led_GPS = digitalio.DigitalInOut(board.GP2)
led_GPS.direction = digitalio.Direction.OUTPUT
led_Internet = digitalio.DigitalInOut(board.GP3)
led_Internet.direction = digitalio.Direction.OUTPUT
led_noSend = digitalio.DigitalInOut(board.GP16)
led_noSend.direction = digitalio.Direction.OUTPUT
led_noSend.value = False

led_Internet.value = True
led_noSend.value = True

buzz(step=2)


infors = []
displayio.release_displays()
SCREEN_ENABLE = mcu_config['SCREEN_ENABLE']
if SCREEN_ENABLE:
    if mcu_config['SCREEN_BUS'] =='SPI':
        # from adafruit_st7735r import ST7735R as DISPLAYDRV
        from adafruit_st7789 import ST7789 as DISPLAYDRV
        LED_Backlight = digitalio.DigitalInOut(board.GP28)
        LED_Backlight.direction = digitalio.Direction.OUTPUT
        LED_Backlight.value =True
        spi = busio.SPI(clock=mcu_config['display']['SPI']['SCL'], MOSI=mcu_config['display']['SPI']['MOSI'])

        tft_cs = mcu_config['display']['SPI']['CS']
        reset = mcu_config['display']['SPI']['RESET']
        tft_dc = mcu_config['display']['SPI']['DC']

        display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=reset)
        buzz()
        # display = DISPLAYDRV(display_bus, width=mcu_config['SCREEN_SIZE'][0], height=mcu_config['SCREEN_SIZE'][1], rotation=mcu_config['SCREEN_SIZE'][2], bgr=True)
        display = DISPLAYDRV(display_bus, width=mcu_config['SCREEN_SIZE'][0], height=mcu_config['SCREEN_SIZE'][1], rotation=mcu_config['SCREEN_SIZE'][2])
        # display = DISPLAYDRV(display_bus, width=240, height=240, rowstart=80)
    elif mcu_config['SCREEN_BUS'] =='I2C':
        from adafruit_displayio_sh1106 import SH1106 as DISPLAYDRV
        i2c = busio.I2C(board.GP1, board.GP0)
        while not i2c.try_lock():
            pass
        try:
            print("I2C addresses found:",[hex(device_address) for device_address in i2c.scan()],)
            device_addresses = [hex(device_address) for device_address in i2c.scan()]
            time.sleep(2)
        finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
            i2c.unlock()
        time.sleep(1)
        display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
        buzz()
        display = DISPLAYDRV(display_bus, width=128, height=64)
        print("I2C addresses found:",device_addresses,)

    infors.append(displayio.CIRCUITPYTHON_TERMINAL)

def show_display(display_group = None, image = None, content = None, caption = None):
    if SCREEN_ENABLE == False:
        return None
    if image is None and content is not None:
        while len(display_group)>0:
            display_group.pop()
    icon_bit = None
    icon_pal = None
    icon_grid = None
    if image is not None:
        SCREEN_BUS = mcu_config['SCREEN_BUS']
        bg_bit = displayio.Bitmap(mcu_config['display'][SCREEN_BUS]['size'][0], mcu_config['display'][SCREEN_BUS]['size'][1], 1)
        bg_pal = displayio.Palette(1)
        bg_pal[0] = 0xFFFFFF  # White color
        bg_grid = displayio.TileGrid(bg_bit, pixel_shader=bg_pal)
        display_group.append(bg_grid)

        icon_bit, icon_pal = adafruit_imageload.load(image,
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)

        icon_grid = displayio.TileGrid(icon_bit, pixel_shader=icon_pal,
                                        width=1, height=1,
                                        tile_height=mcu_config['SPRITE_SIZE'][1], tile_width=mcu_config['SPRITE_SIZE'][0],
                                        default_tile=0,
                                        x=(int((mcu_config['display'][SCREEN_BUS]['size'][0]-mcu_config['SPRITE_SIZE'][0])/2)), y=int((mcu_config['display'][SCREEN_BUS]['size'][1]-mcu_config['SPRITE_SIZE'][1])/2))
        display_group.append(icon_grid)

        text = ''
        font = terminalio.FONT
        color = 0x0000FF
        # Create the text label
        text_area = label.Label(font, text=text, color=color, scale=2)
        text_area.x = 50
        text_area.y = 220
        display_group.append(text_area)
    if caption is not None:
        display_group[-1].text = caption
        display.refresh()

    title = ''
    lines = []
    if content is not None:
        if 'title' in content:
            title = content['title']
        if 'lines' in content:
            lines = content['lines']
        text = title
        font = terminalio.FONT
        color = 0x0000FF
        text_area = label.Label(font, text=text, color=color, scale=2)
        text_area.x = 20
        text_area.y = 20
        display_group.append(text_area)
        line_number = 0
        for line in lines:
            line_number +=1
            text = line
            font = terminalio.FONT
            color = 0x0000FF
            # Create the text label
            text_area = label.Label(font, text=text, color=color, scale=1)
            text_area.x = 20
            text_area.y = 20 + 20 * line_number
            display_group.append(text_area)

    del icon_bit, icon_pal, icon_grid, title, lines
    gc.collect()
    return display_group


if SCREEN_ENABLE:
    infor = show_display(displayio.Group(), mcu_config['IMAGE_FILE'], None, "Hello seacom")
    infors.append(infor)
    # Seacom Information
    title = 'Seacom Information'
    lines = []
    lines.append('- boxid: {}'.format(mcu_config['seacom_id']))
    lines.append('- Name: {}'.format(mcu_config['name']))
    lines.append('- vessel_name: {}'.format(mcu_config['vessel_name']))
    lines.append('- Hotline: 0678906789')
    params = {
        'title': title,
        'lines': lines
    }
    infor = show_display(displayio.Group(), None, params, None)
    infors.append(infor)
    # Seacom Information
    title = 'Current weather'
    lines = []
    lines.append('- "last_updated": "2023-12-08 10:15"')
    lines.append('- "temp_c": 23.0')
    lines.append('- "condition": "Sunny"')
    lines.append('- "wind_kph": 11.2')
    lines.append('- "wind_dir": "ESE"')
    lines.append('- "humidity": 61')
    lines.append('- "feelslike_c": 24.7')
    params = {
        'title': title,
        'lines': lines
    }
    infor = show_display(displayio.Group(), None, params, None)
    infors.append(infor)


    i= 0
    i+=1
    display.root_group = infors[i%len(infors)]
else:
    buzz()
    buzz()
time.sleep(2)
buzz(step=3)

def show_text(text = 'Welcom to seacom'):
    if SCREEN_ENABLE:
    	infors[1] = show_display(display_group=infors[1], caption=text)
show_text('GPS fixing')
# if SCREEN_ENABLE:
#     infors[1] = show_display(display_group=infors[1], caption='GPS fixing')

# GPS
TX = board.GP4
RX = board.GP5
uart = busio.UART(TX, RX, baudrate=9600, timeout=30)
gps = adafruit_gps.GPS(uart, debug=True)
gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
gps.send_command(b'PMTK220,1000')
gps.update()
last_update = time.monotonic()
while True:
    time.sleep(1)
    gps.update()
    current = time.monotonic()
    if current - last_update >= 2.0:
        last_update = current
        if not gps.has_fix:
            print('Waiting for fix...')
            continue
        print('=' * 40)  # Print a separator line.
        print('Latitude: {0:.6f} degrees'.format(gps.latitude))
        print('Longitude: {0:.6f} degrees'.format(gps.longitude))
        gps_has_fix = True
        led_GPS.value = True
        buzz(step=4)
        break
    if current - last_update >= 1800:
        show_text('Can not fix GPS')
        print('Can not fix GPS')
        buzz(step=10)
        break
# Ethernet hat
show_text('Ethernet setting')
# if SCREEN_ENABLE:
#     infors[1] = show_display(display_group=infors[1], caption='Ethernet setting')
client = None
import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

print("Wiznet5k WebClient Test")

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_URL = "http://api.coindesk.com/v1/bpi/currentprice/USD.json"


spi_bus = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
cs = digitalio.DigitalInOut(board.GP13)


# Initialize ethernet interface with DHCP
# eth = WIZNET5K(spi_bus, cs, is_dhcp=True)
eth = WIZNET5K(spi_bus, cs, is_dhcp=False)

IP_ADDRESS = mcu_config['localip']
SUBNET_MASK = mcu_config['subnet']
GATEWAY_ADDRESS = mcu_config['gateway']
DNS_SERVER = mcu_config['dns_server']
print(IP_ADDRESS,SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

is_dhcp = mcu_config['dhcp']
if is_dhcp == False:
    eth = WIZNET5K(spi_bus, cs, is_dhcp=is_dhcp)
    eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)
    print("Chip Version:", eth.chip)
    print("MAC Address:", [hex(i) for i in eth.mac_address])
    print("My IP address is:", eth.pretty_ip(eth.ip_address))
if is_dhcp == True:
    try:
        print('get DHCP')
        eth = WIZNET5K(spi_bus, cs, is_dhcp=is_dhcp)
        print("Chip Version:", eth.chip)
        print("MAC Address:", [hex(i) for i in eth.mac_address])
        print("MAC Address:", [i for i in eth.mac_address])
        print("My IP address is:", eth.pretty_ip(eth.ip_address))
        buzz()
    except:
        buzz()
        buzz()
        buzz()
        buzz()
        buzz()
        import alarm, time
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
        print('I am going to Deep Sleep in 5s')
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

# Set network configuration


# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)
socket.set_interface(eth)
client = socket.socket(type=socket.SOCK_DGRAM)  # Allocate socket for the server

target_ip = '{}.{}.{}.{}'.format(mcu_config['u0targetip'][0],mcu_config['u0targetip'][1],mcu_config['u0targetip'][2],mcu_config['u0targetip'][3])
target_port = mcu_config['u0targetport']   # Port to listen on
try:
    if eth.link_status == False:
        show_text('The Ethernet connection is down.')
        print('ConnectionError: The Ethernet connection is down.')
    else:
        # eth._debug = True
        try:
            print("IP lookup adafruit.com: %s" %eth.pretty_ip(eth.get_host_by_name("adafruit.com")))
            #eth._debug = True
            print("Fetching text from", TEXT_URL)
            r = requests.get(TEXT_URL)
            print('-'*40)
            print(r.text)
            print('-'*40)
            r.close()

            print()
            print("Fetching json from", JSON_URL)
            r = requests.get(JSON_URL)
            print('-'*40)
            print(r.json())
            print('-'*40)
            r.close()
            led_Internet.value = True
            internet_on = True
            buzz()
            print("Done!")
            show_text('Ethernet is done')
        except Exception as e:
            if hasattr(e, 'message'):
                t_msg = str(e.message)
            else:
                t_msg = str(e)
            print('error', t_msg)
            internet_on = True
            led_Internet.value = False
            show_text('Ethernet is error')
        #param int type: Socket type, use SOCK_STREAM for TCP and SOCK_DGRAM for UDP,
        try:
            # target_ip = '113.160.22.246'
            # target_port = 6001  # Port to listen on
            client.sendto('hello EveryOne from {}'.format(mcu_config['seacom_id']).encode(),(target_ip, target_port))  # Bind to IP and Port
            show_text('Show hello everyone')
        except Exception as e:
            if hasattr(e, 'message'):
                t_msg = str(e.message)
            else:
                t_msg = str(e)
            print('error', t_msg)
            show_text('error {}'.format(t_msg))
    eth_on = True
except:
    buzz(step=5)
    show_text('Error when setting Ethernet')
    eth_on = False

if eth_on == False:
    buzz()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
    print('I am going to Deep Sleep in 5s')
    show_text('Restart cause by Ethernet Error')
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

# Sensor
show_text('Sensors setting ...')
# if SCREEN_ENABLE:
#     infors[1] = show_display(display_group=infors[1], caption='Sensor setting')
try:
    sensor_dht22 = adafruit_dht.DHT22(board.GP22)
    print(sensor_dht22.temperature)
    print(sensor_dht22.humidity)
    print(microcontroller.cpu.temperature)
    sensor_on = True
    buzz(step=1)
except:
    show_text('Sensors setting error')
    buzz(step=5)
    pass

last_update = []

last_update.append(time.monotonic())
last_update.append(time.monotonic())
last_update.append(time.monotonic())
update_last_update = []
update_last_update.append(True)
update_last_update.append(True)
update_last_update.append(True)

sos_keep = True

def led_flash(led_onoff):
    for i in range(3):
        led_onoff.value = False
        time.sleep(0.5)
        led_onoff.value = True
    pass
# if SCREEN_ENABLE:
#     display.root_group = infors[1]

buzz(2)
error_count = 0
show_text('{}'.format(mcu_config['seacom_id']))
# if SCREEN_ENABLE:
#     infors[1] = show_display(display_group=infors[1], caption='Ready')

while True:
    time.sleep(0.1)
    try:
        gc.collect()
        if sos_on:
            print('----------------------------- SOS ON')
            buzz(sleep=0.1)

        if buttons[0] is not None:
            if buttons[0].value:
                i+=1
                i = i%len(infors)
                print('Press UP')
                show_text('Press UP. {}'.format(mcu_config['seacom_id']))
                if SCREEN_ENABLE:
                    display.root_group = infors[i]

        if buttons[1] is not None:
            if buttons[1].value:
                i+=-1
                i = i%len(infors)
                print('Press Down')
                show_text('Press Down. {}'.format(mcu_config['seacom_id']))
                if SCREEN_ENABLE:
                    display.root_group = infors[i]

        if buttons[2] is not None:
            if buttons[2].value:
                print('Press OK')
                # infors[1] = show_display(display_group=infors[1], caption='HOLLA')
                show_text('Press OK. {}'.format(mcu_config['seacom_id']))
                if SCREEN_ENABLE:
                    display.root_group = infors[1]

        if buttons[3] is not None:
            if buttons[3].value:
                print('Press Exit')
                i = 0
                # infors[1] = show_display(display_group=infors[1], caption='HELLO ANH LAM')
                show_text('Press Exit. {}'.format(mcu_config['seacom_id']))
                if SCREEN_ENABLE:
                    display.root_group = infors[i]
                buzz()
        if buttons[4] is not None:
            if buttons[4].value:
                print('Press SOS')
                i = 0
                print('Press SOS')
                if SCREEN_ENABLE:
                    display.root_group = infors[1]
                show_text('Press SOS. {}'.format(mcu_config['seacom_id']))
                buzz()
                # reboot pico
                sos_on = True
                priority = True
                priority_time = 0
                print('check sos for 5s', end='')
                for i in range(50):
                    time.sleep(0.1)
                    print('.', end='')
                    sos_on = True
                    if buttons[4].value == False:
                        show_text('NO SOS. {}'.format(mcu_config['seacom_id']))
                        print('NO SOS')
                        sos_on = False
                        break
                if sos_on:
                    buzz()
                    buzz()
                    buzz()
                    buzz()
                    buzz()
            # else:
            #     sos_on = False
            #     speaker.value = False
        if buttons[5] is not None:
            if buttons[5].value:
                buzz()
                print('Press Cancel')
                if SCREEN_ENABLE:
                    display.root_group = infors[1]
                show_text('Press Cancel. {}'.format(mcu_config['seacom_id']))
                reboot = False
                speaker.value = False
                sos_on = False
                priority = True
                priority_time = 0
                for i in range(300):
                    time.sleep(0.1)
                    print('.', end='')
                    reboot = True
                    if buttons[5].value == False:
                        reboot = False
                        break
                if reboot:
                    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
                    print('I am going to Deep Sleep in 5s')
                    show_text('Restart in 5s')
                    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
        current = time.monotonic()
        gps.update()
        current = time.monotonic()
        i_update = 0
        if current - last_update[i_update] >= 1.0:
            if sos_on:
                print('SOS')
                buzz(sleep=0.1)
                # speaker.value = True
            else:
                # buzz(sleep=1)
                speaker.value = False
                # print('NOSOS')
            update_last_update[i_update] = True
        if update_last_update[i_update]:
            update_last_update[i_update] = False
            last_update[i_update] = time.monotonic()
        i_update += 1
        # current = time.monotonic()
        waiting = mcu_config['waiting']
        if current - last_update[i_update] >= waiting:
            print('Sending report')
            update_last_update[i_update] = True
            params = {}
            for key, value in mcu_config.items():
                if key in mcu_config_keys:
                    params[key] = value

            if not gps.has_fix:
                print('Waiting for fix...')
                led_flash(led_GPS)
                led_flash(led_GPS)
                led_flash(led_GPS)
                gps_has_fix = False
                led_GPS.value = False
            else:
                led_GPS.value = True
            if gps.has_fix:
                gps_has_fix = True
                print('=' * 40)  # Print a separator line.
                print('Latitude: {0:.6f} degrees'.format(gps.latitude))
                print('Longitude: {0:.6f} degrees'.format(gps.longitude))
            if gps_has_fix:
                params['lat']   = gps.latitude
                params['lon']   = gps.longitude
                # params['timestamp_utc']   = gps.timestamp_utc
                print('imestamp_utc')
                print(gps.timestamp_utc)
                params['timestamp'] = time.mktime(gps.timestamp_utc)
                params['satellites']   = gps.satellites
                params['altitude_m']   = gps.altitude_m
                params['speed_knots']   = gps.speed_knots
                # params['sats']   = gps.sats
                # params['pdop']   = gps.pdop
                # params['hdop']   = gps.hdop
                # params['vdop']   = gps.vdop
            if sos_on:
                params['sos']   = 1
            else:
                params['sos']   = 0
            if sensor_on:
                params['microcontroller.cpu.temperature'] = microcontroller.cpu.temperature
                params['temperature'] = sensor_dht22.temperature
                params['humidity'] = sensor_dht22.humidity

            if eth_on:
                # check internet
                if priority and priority_time<5:
                    params['priority'] = 1
                    priority_time+=1
                else:
                    priority = False
                    priority_time = 0
                if internet_on:
                    led_Internet.value = True
                else:
                    led_flash(led_Internet)
                    led_flash(led_Internet)
                    led_flash(led_Internet)
                    led_Internet.value = False
                client.sendto(json.dumps(params).encode(),(target_ip, target_port))  # Bind to IP and Port
                print(target_ip, target_port)
                print(json.dumps(params).encode())

        if update_last_update[i_update]:
            update_last_update[i_update] = False
            last_update[i_update] = time.monotonic()

        # check network
        # current = time.monotonic()
        i_update += 1
        waiting = mcu_config['network_check']
        if current - last_update[i_update] >= waiting:
            try:
                print(SOS_link)
                if sos_on:
                    buzz(sleep=0.1)
                response = requests.get(SOS_link)
                s_json = response.json()
                print('SOS {}'.format(s_json))
                if priority == False:
                    if mcu_config['mmsi'] in s_json:
                        sos_by_backend = bool(s_json[mcu_config['mmsi']])
                        print('SOS 1 {}{}'.format(sos_by_backend, mcu_config['mmsi']))
                        if sos_by_backend:
                            print('SOS 2')
                            show_text('*** SOS *** {}'.format(mcu_config['seacom_id']))
                            sos_on = True
                        else:
                            print('SOS 3')
                            show_text('{}'.format(mcu_config['seacom_id']))
                            sos_on = False
                internet_on = True
                if sos_on:
                    buzz(sleep=0.1)
            except Exception as e:
                buzz(step=5)
                if hasattr(e, 'message'):
                    t_msg = str(e.message)
                else:
                    t_msg = str(e)
                print('error', t_msg)
                internet_on = False
            pass
            print('Check network')
            last_update[i_update] = time.monotonic()
    except Exception as e:
        error_count+=1
        buzz()
        if hasattr(e, 'message'):
            t_msg = str(e.message)
        else:
            t_msg = str(e)
        print('error', t_msg)
        if error_count>50:
            time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
            print('I am going to Deep Sleep in 5s')
            alarm.exit_and_deep_sleep_until_alarms(time_alarm)
