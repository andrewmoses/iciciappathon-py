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
            #hit the icici data mapping to get the cust_id
            response2 = unirest.get("https://retailbanking.mybluemix.net/banking/icicibank/participantmapping", headers={ "Accept": "application/json" }, params={ "client_id":"andrew2moses@gmail.com"})
            pdmapping = response2.body
            for each in pdmapping:
                #find the cust_id of the accno.
                try:
                    if each['account_no']==accno['accountno']:
                        wantedcustid = each['cust_id']
                except:
                    print 'wow da'
            print 'custid:'+str(wantedcustid)
            pubkey = random_with_N_digits(10)
            privatekey = random_with_N_digits(10)
            db = MySQLdb.connect(host='localhost', user='root', passwd='', db='wallet')
            cur = db.cursor()
            #check if pubkey already exists or not
            while True:
                cur.execute("""SELECT * FROM users WHERE vpa=%s""", [pubkey])
                data = cur.fetchall()
                if data:
                    #regenerate the key and check again untill it is unique
                    pubkey = random_with_N_digits(10)
                else:
                    break
            currentbalance = response.body[1]['balance']
            outman = {'pubkey': pubkey, 'privatekey': privatekey, 'currentbalance': currentbalance}
            #insert into db
            cur.execute("""INSERT INTO users(vpa,accountnumber,cust_id) values(%s,%s,%s)""", (pubkey,accno['accountno'],wantedcustid))
            db.commit()
            db.close()
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
    db = MySQLdb.connect(host='localhost', user='root', passwd='', db='wallet')
    cur = db.cursor()
    cur.execute(""" SELECT * FROM users WHERE amount!=%s AND vpa!=%s """, ['',location['vpa']])
    data = cur.fetchall()
    if data:
        for each in data:
            dbdic = {}
            dbdic['avatar'] = each[1]
            dbdic['nickname'] = each[2]
            dbdic['vpa'] = each[4]
            dbdic['amount'] = each[8]
            guys.append(dbdic)
    db.close()
    if guys:
        return jsonify(guys = guys)
    else:
        return "empty"
@app.route('/extradata', methods = ['POST'])
def extradata():
    try:
        fulldata = request.get_json(force=True)
        print fulldata
        db = MySQLdb.connect(host='localhost', user='root', passwd='', db='wallet')
        cur = db.cursor()
        cur.execute( """UPDATE users set avatar=%s, nickname=%s, type=%s, lat=%s, lng=%s WHERE vpa=%s""", (fulldata['avatar'], fulldata['nickname'], fulldata['type'], fulldata['lat'], fulldata['lng'], fulldata['vpa']))
        db.commit()
        db.close()
        return 'success'
    except Exception as e:
        print e
        return 'failed'
@app.route('/payeeconfirm', methods = ['POST'])
def payeeconfirm():
    try:
        vpa = request.get_json(force=True)
        print 'payeeconfirm: '+str(vpa['payvpa'])
        #hit db and check whether it is valid
        db = MySQLdb.connect(host='localhost', user='root', passwd='', db='wallet')
        cur = db.cursor()
        cur.execute("""SELECT * FROM users WHERE vpa=%s""", [vpa['payvpa']])
        data = cur.fetchall()
        if data:
            #retrieve the avatar and nickname
            for each in data:
                pavatar = each[1]
                pnickname = each[2]
            outman = {'payeeavatar': pavatar, 'payeenickname': pnickname}
            db.close()
            return jsonify(outman)
        else:
            #no such vpa
            db.close()
            return "invalid"
    except Exception as e:
        print e
        return False
@app.route('/curbal', methods=['POST'])
def curbal():
    vpa = request.get_json(force=True)
    print 'vpa: '+str(vpa)
    #hit the mysql and get the acc number
    db=MySQLdb.connect(host='localhost', user='root', passwd='', db='wallet')
    cur = db.cursor()
    cur.execute("""SELECT * FROM users WHERE vpa=%s""", [vpa['vpa']])
    data = cur.fetchall()
    for each in data:
        curaccno = each[5]
    db.close()
    #nwo hit the icic for balance
    response = unirest.get("https://retailbanking.mybluemix.net/banking/icicibank/balanceenquiry", headers={ "Accept": "application/json" }, params={ "client_id": "andrew2moses@gmail.com", "token": "fbc5f3df1504", "accountno": curaccno })
    try:
        if response.body[1]['balance']:
            currentbalance = response.body[1]['balance']
            outman = {'curbal':currentbalance}
            return jsonify(outman)
    except Exception as e:
        print e
        return "invalid"

@app.route('/receiveamount', methods = ['POST'])
def receiveamount():
    delta = request.get_json(force=True)
    db = MySQLdb.connect(host='localhost', user = 'root', passwd='', db='wallet')
    cur = db.cursor()
    cur.execute( """UPDATE users set amount=%s WHERE vpa=%s""",(delta['ramt'], delta['vpa']) )
    db.commit()
    db.close()
    return 'success'

@app.route('/transfer', methods = ['POST'])
def transfer():
    payee = request.get_json(force=True)
    print payee
    #hit the mysql for the account details
    db = MySQLdb.connect(host='localhost', user = 'root', passwd='', db='wallet')
    cur = db.cursor()
    #for finding to the TO acc number
    cur.execute("""SELECT * FROM users WHERE vpa=%s""", [payee['vpa']])
    data = cur.fetchall()
    for each in data:
        accno = each[5]
        payeedesc = each[2]
    #for finding the From acc number
    cur.execute("""SELECT * FROM users WHERE vpa=%s""", [payee['fvpa']])
    data = cur.fetchall()
    for each in data:
        faccno = each[5]
        fcustid = each[9]
    db.close()
    #now hit the icici api for finding the payeeid
    response1 = unirest.get("https://retailbanking.mybluemix.net/banking/icicibank/listpayee", headers={"Accept": "application/json" }, params={ "client_id": "andrew2moses@gmail.com", "token": "fbc5f3df1504", "custid": fcustid})
    #find the wanted payeeid
    rgpayees = response1.body
    for each in rgpayees:
        try:
            if each['payeeaccountno'] == accno:
                wantedpayeeid = each['payeeid']
        except:
            print 'wow da'
    print 'payeeid: '+str(wantedpayeeid)
    #now hit the icici api for transfer
    response = unirest.get("https://retailbanking.mybluemix.net/banking/icicibank/fundTransfer", headers={"Accept": "application/json" }, params={ "client_id": "andrew2moses@gmail.com", "token": "fbc5f3df1504", "srcAccount":faccno, "destAccount": accno, "amt": payee['amount'], "payeeDesc": payeedesc, "payeeId": wantedpayeeid, "type_of_transaction": "school fee payment"})
    print response.body
    try:
        if response.body[1]['status'] == "SUCCESS":
            #AWESOME BRO
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

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
