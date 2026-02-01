import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pyvjoy import VJoyDevice
import io
import qrcode
import socket




app = Flask(__name__)
socketio = SocketIO(app,debug=True)

gamepadStatus = False

buttonState =  ['0']*8


def setup():
    '''
    This will always connect to VJoyDevice: 1. 
    Open to vJoyConf - Configure vJoy Devices to change the number of axes and buttons.
    '''
    global virtual_joystick
    virtual_joystick = VJoyDevice(1)
    virtual_joystick.data.wAxisX = 16383
    virtual_joystick.data.wAxisY = 16383
    
    buttonState = ['0'] * 8
    buttonState = ''.join(buttonState)
    virtual_joystick.data.lButtons = int(buttonState,2)  
    virtual_joystick.update()

def map_value(value, in_min, in_max, out_min, out_max):
    '''
    Maps a value from one range to another
    Parameters:
        value (float): The value to map
        in_min (float): The minimum value of the input range
        in_max (float): The maximum value of the input range
        out_min (float): The minimum value of the output range
        out_max (float): The maximum value of the output range
    '''
    mapped_value = int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    if (mapped_value < out_min):
        mapped_value = out_min
    if mapped_value > out_max:
        mapped_value = out_max
    return mapped_value


@app.route('/')
def index():
    '''
    This is the main page of the application.
    '''
    setup()
    return render_template('index.html')
    

@socketio.on('update_joystick_axis')
def handle_update_joystick_axis(data):
    """
    When a slider is moved, the virtual joystick's axis value is updated.
    """
    axis = data.get('axis')
    value = int(data.get('value', 0))

    if axis == 'x':
        virtual_joystick.data.wAxisX = value
    elif axis == 'y':
        virtual_joystick.data.wAxisY = value
    elif axis == 'z':
        virtual_joystick.data.wAxisZ = value
    elif axis == 'slider1':
        virtual_joystick.data.wDial = value
    elif axis == 'slider2':
        virtual_joystick.data.wSlider = value
    
    virtual_joystick.update()


@socketio.on('button_press')
def handle_button_press(data):
    '''
    When a button is pressed, the virtual joystick's button state is updated.  
    '''
    # print(data["button"])
    buttonState = ['0'] * 8
    buttonState[-int(data["button"])] = '1'
    flipped_binary_string = ''.join(buttonState)
    virtual_joystick.data.lButtons = int(flipped_binary_string,2)  
    virtual_joystick.update()

    
@socketio.on('button_release')
def handle_button_press(data):
    '''
    When a button is released, the virtual joystick's button state is updated.
    '''
    buttonState = ['0'] * 8
    flipped_binary_string = ''.join(buttonState)
    virtual_joystick.data.lButtons = int(flipped_binary_string,2)  
    virtual_joystick.update()

@socketio.on('gamepadButton')
def handle_gamepad_button_press(data):
    '''
    Get the button status from the gamepad and update the virtual joystick.
    '''
    # print(data["gamepadButtonData"])
    # print("virtual_joystick.data.lButtons",virtual_joystick.data.lButtons)
    gamepadButtons = data["gamepadButtonData"]
    gamepadButtons.reverse()
    # print(gamepadButtons)
    binary_string = ''.join(map(str, gamepadButtons))
    virtual_joystick.data.lButtons = int(binary_string,2)  
    virtual_joystick.update()

@socketio.on('gamepadConnection')
def getGamepadConnectionStatus(data):
    '''
    Get the gamepad connection status.
    Reset all values
    '''
    global gamepadStatus
    gamepadStatus = data["connected"]
    # print("Gamepad connection: ",gamepadStatus)

    virtual_joystick.data.wAxisX = 16383
    virtual_joystick.data.wAxisY = 16383
    
    buttonState = ['0'] * 8
    buttonState = ''.join(buttonState)
    virtual_joystick.data.lButtons = int(buttonState,2)  
    virtual_joystick.update()

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    # socketio.run(app, debug=True)
    qr = qrcode.QRCode()
    ip = get_lan_ip()
    qr.add_data("http:"+ip+":5000")
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())
    socketio.run(app, host='0.0.0.0', port=5000)

