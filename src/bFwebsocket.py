import threading
import socketio
import datetime
from functools import partial

# https://github.com/alunfes/bitbankBot/blob/24ff3767c0ec1116c838241a58695c78d5e98a05/BitbankWS.py
# https://github.com/gosling-goldwyn/bit_websocket/blob/e723c9a34b4fab2bbbe8b3d3a137524ea434c8ce/receiver.py

class BFsocketData:
    @classmethod
    def initialize(cls):
        cls.last_price = 0
        cls.lock_last_price = threading.Lock()

    @classmethod
    def set_last_price(cls, last_price):
        with cls.lock_last_price:
            print(last_price)
            cls.last_price = last_price
    
    @classmethod
    def get_last_price(cls):
        with cls.lock_last_price:
            return cls.last_price

class BFsocket:

    def __init__(self, channel):
        self.channel = channel

    def on_data(self, channel, data):
        BFsocketData.set_last_price(data)

    def on_connect(self):
        print('connection established {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))
        self.sio.on(self.channel, partial(self.on_data, self.channel))
        self.sio.emit('subscribe', self.channel)

    def on_disconnect(self):
        print('disconnected from server {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))

    def start(self):
        BFsocketData.initialize()
        self.sio = socketio.Client()
        self.sio.on('connect', self.on_connect)
        self.sio.connect('https://io.lightstream.bitflyer.com', transports=['websocket'])
        self.sio.wait()

if __name__ == '__main__':
    bf = BFsocket("lightning_ticker_BTC_JPY")
    bf.start()
    