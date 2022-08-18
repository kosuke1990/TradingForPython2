import time
import socketio
import datetime

# ref
# https://github.com/gosling-goldwyn/bit_websocket/blob/e723c9a34b4fab2bbbe8b3d3a137524ea434c8ce/receiver.py
# https://github.com/philipperemy/bitflyer/blob/88acae8dc48b0177e1af41e78a4980a6a8510f5d/bitflyer/ticker.py
# https://www.raspberrypirulo.net/entry/socketio-client

class WebSocketIO(object):

    def __init__(self, end_point, key, secret):
        self.end_point = end_point
        self.key = key
        self.secret = secret

        self.sio = socketio.Client()
        self.sio.on('connect', self.on_connect)
        self.sio.connect(self.end_point, transports=['websocket'])
        while not self._connected:
            time.sleep(1)

    def on_connect(self):
        print('connection established {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))
        self._connected = True

    def on_disconnect(self):
        print('disconnected from server {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))

    def auth(self):
        pass

    def on_auth(self, data):
        print('Auth process done')

    def register_handler(self, channel, handler):
        self.sio.on(channel, handler)
        self.sio.emit('subscribe', channel)

if __name__ == '__main__':
    ws = WebSocketIO('https://io.lightstream.bitflyer.com', '', '')
    ws.on_connect()
