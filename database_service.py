import time
import signal
import sys
from flask import Flask, render_template
from flask.ext.mysql import MySQL
from flask.ext.socketio import SocketIO, emit

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

@app.route('/index')
def index():
    return render_template('columbia_shuttle_services.html')

@app.route('/viewbookings')
def viewbookings():
    return render_template('viewbookings.html')

@socketio.on('findbooking')
def findbooking(message):
    bookingid = message['bookingid'];
    booking_query = 'SELECT booking_id, uni, schedule_no, source_station, dest_station FROM BookingHistory WHERE Booking_id="' + bookingid + '"'
    cursor.execute(booking_query)
    data = cursor.fetchone()
    socketio.emit('foundbooking', {'booking': data})
    #socketio.emit('foundbooking', {'BID': data[0], 'UNI': data[1], 'SNO': data[2], 'SS': data[3], 'DS': data[4]}) 

if __name__ == '__main__':
    socketio.run(app)
