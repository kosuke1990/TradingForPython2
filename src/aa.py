import time
import socketio
import datetime

class MyCustomNamespace(socketio.ClientNamespace):
    def __init__(self, path, sio, host) -> None:
        super().__init__()
        self.path = path
        self.sio = sio
        self.host = host
        self.data = None

    def on_connect(self):
        print('connection established {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))
        self.sio.emit('subscribe', "lightning_executions_BTC_JPY", namespace=self.path)

    def on_disconnect(self):
        print('disconnected from server {}'.format(datetime.datetime.now()+datetime.timedelta(hours=9)))

    def on_lightning_executions_BTC_JPY(self, msg):
        return msg
        # print(msg)
        
    # def on_ticker(self,data):
    #     #self.sio.emit('subscribe', "lightning_executions_BTC_JPY", namespace=self.path)
    #     self.sio.emit('subscribe', data)

class SocketIOClient:

    def __init__(self, host, path):
        self.host = host
        self.path = path
        self.sio = socketio.Client()
        self.msg = None

    def connect(self, func):
        self.sio.register_namespace(MyCustomNamespace(self.path, self.sio, self.host))
        # transports設定しないとwebsocket通信にならない
        self.sio.connect(self.host, transports=['websocket'])
        self.sio.wait()

if __name__ == '__main__':
    sio = SocketIOClient('https://io.lightstream.bitflyer.com', '/')
    sio.connect(on_lightning_executions_BTC_JPY)
