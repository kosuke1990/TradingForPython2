from bfWebsockts import WebSocketIO
import time

KEY = ''
SECRET = ''

class bFWebSocketIO(object):

    def __init__(self, symbol):
        self.symbol = symbol
        # self.order_book = OrderBook()
        self.msg = None

        def on_ticker(message):
            self.msg = message

        ws = WebSocketIO('https://io.lightstream.bitflyer.com', KEY, SECRET)
        ws.register_handler(channel=f'lightning_ticker_{self.symbol}', handler=on_ticker)

    def get_msg(self):
        return self.msg

if __name__ == '__main__':
    s = bFWebSocketIO('FX_BTC_JPY')
    while True:
        print(s.get_msg())
        time.sleep(0.1)