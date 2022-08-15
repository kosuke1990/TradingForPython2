import sys
import time
import math
import copy
import pymongo
from pymongo import MongoClient
from traceback import print_exc
from ticker import bFWebSocketIO



conf_ = {"host": "localhost",
         "port": 27017,
         "username": "root",
         "password": "example",
         "database": "ticker",
         "collection": "ETH_JPY"}

def get_stat():
    _db = MongoClient(host=conf_["host"], port=conf_["port"], username=conf_["username"], password=conf_["password"])[conf_["database"]][conf_["collection"]]
    #_db.tickers.create_index('_id')
    print(_db.tickers.index_information())

def send_data():
    bf = bFWebSocketIO('ETH_JPY')
    pre_data = {}
    while True:
        data = bf.get_msg()
        if data:
            #data['inserted_time'] = math.floor(time.time()*10)/10
            data['inserted_time'] = math.floor(time.time())
        if data and pre_data:            
            if data['inserted_time'] != pre_data['inserted_time']:
                if data.get('_id',):
                    del data['_id']
                _col = MongoClient(host=conf_["host"], port=conf_["port"], username=conf_["username"], password=conf_["password"])[conf_["database"]][conf_["collection"]]
                _col.insert_one(data)
        pre_data=copy.copy(data)
        time.sleep(0.01)
    # skip document because it already exists in new collection

def set_index():
    print('Hello world')

def get_data():
    bf = bFWebSocketIO('ETH_JPY')
    while True:
        data = bf.get_msg()
        time.sleep(1)
        return data

if __name__ == "__main__":
    try:
        if sys.argv[1] == "stat":
            get_stat()
        elif sys.argv[1] == "send":
            send_data()
        elif sys.argv[1] == "set":
            set_index()
        # elif sys.argv[1] == "check":
        #     check_duplicated_content()
        else:
            raise Exception("unsupported")
    except:
        print_exc()
