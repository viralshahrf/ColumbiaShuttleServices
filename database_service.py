import time
import signal
import sys
from flask import Flask, render_template
from flask.ext.mysql import MySQL
from flask.ext.socketio import SocketIO, emit
from make_bookings_query import *

app = Flask('ColumbiaShuttleServices')
app.config['DEBUG'] = True
app.config['secret'] = 'css'
app.config['MYSQL_DATABASE_USER'] = 'psp2133'
app.config['MYSQL_DATABASE_PASSWORD'] = 'horcrux1'
app.config['MYSQL_DATABASE_DB'] = 'cs4111'
app.config['MYSQL_DATABASE_HOST'] = 'shuttle.cfs9lab4dyj4.us-west-2.rds.amazonaws.com'
app.config['MYSQL_DATABASE_PORT'] = 3306

socketio = SocketIO(app)

mysql = MySQL()
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()

source = []
dest_list = []
dest = []

@app.route('/index')
def index():
    return render_template('columbia_shuttle_services.html')

@app.route('/viewbookings')
def viewbookings():
    return render_template('viewbookings.html')

@socketio.on('findbooking')
def findbooking(message):
    bookingid = message['bookingid']
    print "bookingid = ", bookingid
    booking_query = 'SELECT booking_id, uni, schedule_no, source_station, dest_station FROM BookingHistory WHERE Booking_id="' + bookingid + '"'
    cursor.execute(booking_query)
    data = cursor.fetchone()
    socketio.emit('foundbooking', {'booking': data})
    #socketio.emit('foundbooking', {'BID': data[0], 'UNI': data[1], 'SNO': data[2], 'SS': data[3], 'DS': data[4]}) 

@app.route('/makebooking')
def makebookings():
	return render_template('makebooking.html')	

@socketio.on('findDest')
def findDest(message):
    bname = message['source_bname']
    street = message['source_st']
    avenue = message['source_ave']
    global source
    source = [bname, street, avenue]
    if street == '':
        socketio.emit('foundError', {'error': 'Street Number is a required field'})
    else:
        global dest_list
        dest_list = get_dest(cursor, bname, street, avenue)
        socketio.emit('foundDest', {'dest_list': dest_list})

@socketio.on('findSchedule')
def findSchedule(message):
    dest_id = int(message['dest_rownum'])
    global dest
    dest = dest_list[dest_id]
    socketio.emit('foundSchedule', {'schedule_list': get_schedule(cursor, dest[0], dest[1])})
        
if __name__ == '__main__':
    socketio.run(app)
