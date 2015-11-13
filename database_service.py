import time
import signal
import sys
from flask import Flask, render_template
from flask.ext.mysql import MySQL
from flask.ext.socketio import SocketIO, emit
from queries import make_bookings

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
    bookingid = message['bookingid']
    data = get_booking(cursor, bookingid)
    socketio.emit('foundbooking', {'booking': data})

@app.route('/makebookings')
def makebookings():
    global bookingFlag
    bookingFlag = 0
    return render_template('makebookings.html')

@socketio.on('findDest')
def findDest(message):
    global source, dest_list
    bname = message['source_bname']
    street = message['source_st']
    avenue = message['source_ave']
    source = [bname, street, avenue]
    if street == '':
        socketio.emit('foundError', {'error': 'Street Number is a required field', 'div':'destinations'})
    else:
        dest_list = session.get_dest(cursor, bname, street, avenue)
        if dest_list:
            socketio.emit('foundDest', {'dest_list': dest_list, 'div':'destinations'})
        else:
            socketio.emit('foundError', {'error':'Invalid combination. No destinations found !', 'div':'destinations'})

@socketio.on('findSchedule')
def findSchedule(message):
    global dest, schedule_list
    dest_id = int(message['dest_rownum'])
    dest = dest_list[dest_id]
    schedule_list = session.get_schedule(cursor, source, dest[0], dest[1])
    if schedule_list:
        socketio.emit('foundSchedule', {'schedule_list': schedule_list})
    else:
        socketio.emit('foundError', {'error': 'Error Occcured. Please try again !', 'div':'schedule'})

@socketio.on('logBooking')
def logBooking(message):
    global bookingFlag
    print bookingFlag
    if bookingFlag == 1:
        socketio.emit('foundError', {'error': 'You cannot do multiple bookings! Refresh the page for a new booking.', 'div':'message'})
        return
    schedule_id = int(message['schedule_id'])
    uni = message['uni']
    retstat = session.registerBooking(cursor, uni, schedule_list[schedule_id])
    if retstat[1] >= 1:
        conn.commit()
        bookingFlag = 1
        success_msg = "Booking Confirmed. Please note your booking id: " + str(retstat[0])
        socketio.emit('foundError', {'error': success_msg, 'div':'message'})
    elif retstat[1] == -1:
        socketio.emit('foundError', {'error': 'Please specify a valid UNI', 'div':'message'})
    else:
        socketio.emit('foundError', {'error': 'Unsuccessful! Please try booking again.', 'div':'message'})
        
if __name__ == '__main__':
    source = []
    dest_list = []
    dest = []
    schedule_list = []
    bookingFlag = 0
    session = make_bookings()
    socketio.run(app)
