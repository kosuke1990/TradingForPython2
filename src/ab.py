# -*- coding: utf-8 -*-
'''Realtime API for bitFlyer by Socket.IO(WebSocket)'''

import socketio

from .realtime import RealtimeAPI, Channels


class RealtimeAPI_SIO(RealtimeAPI):
    '''
    Realtime API for bitFlyer by Socket.IO
    *** The description of callback ***
    on_message is a callback for all messages.
    on_message_board, on_message_board_snapshot, on_message_ticker
    and on_message_executions are callbacks for each subscribed messages.
    '''

    CONNECTION_URL = 'https://io.lightstream.bitflyer.com'

    def __init__(self,
                 subscriptions,
                 *,
                 on_message=None,
                 on_message_board=None,
                 on_message_board_snapshot=None,
                 on_message_ticker=None,
                 on_message_executions=None):

        super().__init__(subscriptions,
                         on_message=on_message,
                         on_message_board=on_message_board,
                         on_message_board_snapshot=on_message_board_snapshot,
                         on_message_ticker=on_message_ticker,
                         on_message_executions=on_message_executions)

        # socket.io
        self._sio = socketio.Client()

    def start(self):
        '''start listening'''

        @self._sio.event
        def connect():      # for sio pylint: disable=unused-variable
            '''sio connect'''
            for sub in self._subscriptions:
                # pylint: disable=cell-var-from-loop
                if sub.channel == Channels.BOARD_SNAPSHOT:
                    self._sio.on(sub.subscription, handler=lambda msg: self._on_message_board_snapshot(sub.pair, msg))
                elif sub.channel == Channels.BOARD:
                    self._sio.on(sub.subscription, handler=lambda msg: self._on_message_board(sub.pair, msg))
                elif sub.channel == Channels.TICKER:
                    self._sio.on(sub.subscription, handler=lambda msg: self._on_message_ticker(sub.pair, msg))
                elif sub.channel == Channels.EXECUTIONS:
                    self._sio.on(sub.subscription, handler=lambda msg: self._on_message_executions(sub.pair, msg))

                self._sio.emit('subscribe', sub.subscription)

        @self._sio.event
        def disconnect():   # for sio pylint: disable=unused-variable
            '''sio disconnect'''
            for sub in self._subscriptions:
                self._sio.emit('unsubscribe', sub.subscription)

        # ***** start procedure *****
        if self._sio.eio.state == 'connected':
            self.stop()
        self._sio.connect(self.CONNECTION_URL, transports=['websocket'])
        self._sio.wait()

    def stop(self):
        '''stop listening'''
        self._sio.disconnect()