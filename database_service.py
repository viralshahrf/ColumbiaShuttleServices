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
    print bname
    bname_clause = ''
    avenue_clause = ''
    if street == '':
        socketio.emit('foundError', {'error': 'Street Number is a required field'})
    else:
        if bname:
            bname_clause = " \
             and Route.source_stop = ANY (select stop_id from ClosestStop where building_id = (Select building_id from Buildings where building_name like \"%" + bname + "%\")) \
            " 
        if avenue:
            avenue_clause = " and (avenue like \"%" + avenue + "%\")"
        
        findDestQuery = "Select Route.line, source_stop, dest_stop, S.street, S.avenue, Distance from Route, Stations S \
        where source_stop = ANY(select stop_id from Stations where Street = \"" + street + "\"" \
                             + avenue_clause + ")" \
           + "and S.stop_id = dest_stop" + bname_clause
        cursor.execute(findDestQuery)
        col = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        data_to_send = [[str(i) for i in j] for j in data]
        socketio.emit('foundDest', {'dest_list': data_to_send})
        

if __name__ == '__main__':
    socketio.run(app)
