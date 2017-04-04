# Copyright 2015 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from flask import Flask, jsonify, redirect, url_for, request
from flask_cors import CORS, cross_origin
import unirest
from random import randint
import MySQLdb

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

app = Flask(__name__)
CORS(app)
@app.route('/newuser', methods = ['POST'])
def newuser():
    accno = request.get_json(force=True)
    print accno['accountno']
    response = unirest.get("https://retailbanking.mybluemix.net/banking/icicibank/balanceenquiry", headers={ "Accept": "application/json" }, params={ "client_id": "andrew2moses@gmail.com", "token": "fbc5f3df1504", "accountno": accno['accountno'] })
    try:
        if response.body[1]['balance']:
            #valid acc number
            pubkey = random_with_N_digits(10)
            privatekey = random_with_N_digits(10)
            currentbalance = response.body[1]['balance']
            outman = {'pubkey': pubkey, 'privatekey': privatekey, 'currentbalance': currentbalance}
            return jsonify(outman)
    except Exception as e:
        #invalid acc number
        print e
        return "invalid"
    #going to simulate as though block chain was used.
    # going to return a publickey and private.

@app.route('/nearby', methods = ['POST'])
def nearby():
    location = request.get_json(force=True)
    print location
    #simulate sample nearby guys
    guys = []
    dic1 = {'avatar':'boy1', 'nickname': 'Andy', 'vpa': '9443344556', 'amount': '500'}
    dic2 = {'avatar':'girl1', 'nickname': 'Adele', 'vpa': '9009988776', 'amount': '250'}
    dic3 = {'avatar':'man1', 'nickname': 'Rayman', 'vpa': '7588996312', 'amount': '1880'}
    guys.append(dic1)
    guys.append(dic2)
    guys.append(dic3)
    if guys:
        return jsonify(guys = guys)
    else:
        return "empty"
@app.route('/extradata', methods = ['POST'])
def extradata():
    try:
        fulldata = request.get_json(force=True)
        print fulldata
        db = MySQLdb.connect(host='localhost', user='root', passwd='kakavarumahillaya', db='wallet')
        cur = db.cursor()
        cur.execute( """INSERT INTO users(avatar,nickname,type,vpa,lat,lng) values(%s,%s,%s,%s,%s,%s)""", (fulldata['avatar'], fulldata['nickname'], fulldata['type'], fulldata['vpa'], fulldata['lat'], fulldata['lng']))
        db.commit()
        db.close()
        return 'success'
    except Exception as e:
        print e
        return 'failed'
@app.errorhandler(404)
def page_not_found(e):
    return 404
@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

@app.route('/myapp')
def WelcomeToMyapp():
    return 'Welcome again to my app running on Bluemix!'

@app.route('/api/people')
def GetPeople():
    list = [
        {'name': 'John', 'age': 28},
        {'name': 'Bill', 'val': 26}
    ]
    return jsonify(results=list)

@app.route('/api/people/<name>')
def SayHello(name):
    message = {
        'message': 'Hello ' + name
    }
    return jsonify(results=message)

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
