import threading
import socketio
from time import sleep
from datetime import datetime
from itertools import chain
from collections import deque, defaultdict
from functools import partial

import math
import copy
import time
from pymongo import MongoClient

conf_ = {"host": "localhost",
         "port": 27017,
         "username": "root",
         "password": "example",
         "database": "ticker",
         "collection": "ETH_BTC"}

def lightning_channels(product_id, topics):
    return ['lightning_' + t + '_' + product_id.replace('/','_') for t in topics]

def lightning_channel(product_id, topic):
    return 'lightning_' + topic + '_' + product_id.replace('/','_')

class Streaming:

    def __init__(self):
        self.sio = None
        self.running = False
        self.subscribed_channels = []
        self.endpoints = []
        self.connected = False
        self.callbacks = defaultdict(list)

    def sio_on_data(self, channel, data):
        self.on_data(channel,data)

    def sio_on_disconnect(self):
        print('disconnected')
        self.connected = False

    def sio_on_connect(self):
        print('connected')
        self.connected = True
        if len(self.subscribed_channels):
            for channel in self.subscribed_channels:
                self.sio_subscribe(channel)

    def sio_subscribe(self,channel):
        self.sio.on(channel,partial(self.sio_on_data,channel))
        self.sio.emit('subscribe',channel)

    def sio_disconnect(self):
        self.sio.disconnect()

    def sio_run_loop(self):
        while self.running:
            try:
                self.sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=1, reconnection_delay_max=30)
                self.sio.on('connect', self.sio_on_connect)
                self.sio.on('disconnect', self.sio_on_disconnect)
                self.sio.connect('https://io.lightstream.bitflyer.com', transports = ['websocket'])
                self.sio.wait()
            except Exception as e:
                print(e)
            if self.running:
                sleep(5)

    def on_data(self,channel,data):
        if isinstance(data,list):
            data[-1]['receved_at'] = datetime.utcnow()
            data[-1]['bucket_size'] = len(data)
        for cb in self.callbacks[channel]:
            cb(channel,data)

    def get_endpoint(self, product_id='ETH_BTC', topics=['ticker', 'executions']):
        ep = self.get_endpoint_for_channels(lightning_channels(product_id,topics))
        ep.product_id = product_id
        return ep

    def get_endpoint_for_channels(self, channels):
        ep = Streaming.Endpoint()
        self.endpoints.append(ep)
        for channel in channels:
            self.subscribe_channel(channel,ep.put)
        return ep

    def subscribe_channel(self, channel, callback):
        self.callbacks[channel].append(callback)
        if channel not in self.subscribed_channels:
            if self.connected:
                self.subscribe(channel)
            self.subscribed_channels.append(channel)

    def start(self):
        print('start Streaming')
        self.running = True
        self.subscribe = self.sio_subscribe
        self.disconnect = self.sio_disconnect
        self.thread = threading.Thread(target=self.sio_run_loop)
        self.thread.start()

    def stop(self):
        if self.running:
            print('Stop Streaming')
            self.running = False
            self.disconnect()
            self.thread.join()
            for ep in self.endpoints:
                ep.shutdown()

    class Endpoint:

        def __init__(self):
            self.cond = threading.Condition()
            self.data = defaultdict(lambda:deque(maxlen=1000))
            self.latest = defaultdict(lambda:None)
            self.closed = False
            self.suspend_count = 0
            self.product_id = ''

        def put(self, channel, message):
            with self.cond:
                self.data[channel].append(message)
                self.latest[channel] = message
                self.cond.notify_all()

        def suspend(self, flag):
            with self.cond:
                if flag:
                    self.suspend_count += 1
                else:
                    self.suspend_count = max(self.suspend_count-1, 0)
                self.cond.notify_all()

        def wait_for(self, topics=[], product_id=None):
            channels = lightning_channels(product_id or self.product_id, topics)
            for channel in channels:
                while True:
                    data = self.data[channel]
                    if len(data) or self.closed:
                        break
                    else:
                        print('Waiting for stream data...')
                        sleep(1)

        def wait_any(self, topics=[], timeout=None, product_id=None):
            channels = lightning_channels(product_id or self.product_id, topics)
            result = True
            with self.cond:
                while True:
                    available = 0
                    if self.suspend_count == 0:
                        for channel in channels:
                            available = available + len(self.data[channel])
                    if available or self.closed:
                        break
                    else:
                        if self.cond.wait(timeout) == False:
                            result = False
                            break
                        if len(channels)==0:
                            break
            return result

        def shutdown(self):
            with self.cond:
                self.closed = True
                self.cond.notify_all()

        def get_channel_data(self, channel, blocking, timeout):
            with self.cond:
                if blocking:
                    while True:
                        if len(self.data[channel]) or self.closed:
                            break
                        else:
                            if self.cond.wait(timeout) == False:
                                break
                data = list(self.data[channel])
                self.data[channel].clear()
            return data

        def get_ticker(self, blocking=False, timeout=None, product_id=None):
            channel = lightning_channel(product_id or self.product_id, 'ticker')
            self.get_channel_data(channel, blocking, timeout)
            return self.latest[channel]

        def get_tickers(self,blocking=False, timeout=None, product_id=None):
            channel = lightning_channel(product_id or self.product_id, 'ticker')
            return self.get_channel_data(channel, blocking, timeout)

        def get_executions(self, blocking=False, timeout=None, product_id=None, chained=True):
            channel = lightning_channel(product_id or self.product_id, 'executions')
            data = self.get_channel_data(channel, blocking, timeout)
            if not chained:
                return data
            return list(chain.from_iterable(data))

        def get_board_snapshot(self, blocking=False, timeout=None, product_id=None):
            channel = lightning_channel(product_id or self.product_id, 'board_snapshot')
            self.get_channel_data(channel, blocking, timeout)
            return self.latest[channel]

        def get_boards(self, blocking=False, timeout=None, product_id=None):
            channel = lightning_channel(product_id or self.product_id, 'board')
            return self.get_channel_data(channel, blocking, timeout)


if __name__ == "__main__":

    streaming = Streaming()
    streaming.start()
    ep = streaming.get_endpoint(product_id='ETH_BTC', topics=['executions','ticker'])

    while True:
        try:
            ep.wait_any()
            # executions = ep.get_executions()
            # for e in executions:
            #     print(e)
            #     print('EXE {side} {price} {size} {exec_date}'.format(**e))

            tickers = ep.get_tickers()
            for t in tickers:
                # print(t)
                # print('TIK {ltp} {best_bid}({best_bid_size})/{best_ask}({best_ask_size}) {timestamp}'.format(**t))
                data = t
                _col = MongoClient(host=conf_["host"], port=conf_["port"], username=conf_["username"], password=conf_["password"])[conf_["database"]][conf_["collection"]]
                _col.insert_one(data)
            # boards = ep.get_boards()
            # for board in boards:
            #     for bid in board['bids']:
            #         print('BID {price} {size}'.format(**bid))
            #     for ask in board['asks']:
            #         print('ASK {price} {size}'.format(**ask))

        except (KeyboardInterrupt, SystemExit):
            break

    streaming.stop()