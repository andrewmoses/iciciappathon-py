import MySQLdb

fulldata = {'nickname': 'andy', 'lng': '80.270718', 'vpa': '1381415413', 'avatar': 'boy2', 'lat': '13.082680', 'type': 'individual'}
db = MySQLdb.connect(host='localhost', user='root', passwd='kakavarumahillaya', db='wallet')
cur = db.cursor()
cur.execute( """INSERT INTO users(avatar,nickname,type,vpa,lat,lng) values(%s,%s,%s,%s,%s,%s)""", (fulldata['avatar'], fulldata['nickname'], fulldata['type'], fulldata['vpa'], fulldata['lat'], fulldata['lng']))
db.commit()
db.close()
