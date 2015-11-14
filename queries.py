class view_bookings:
    def get_booking(self, cursor, bookingid):
        booking_query = 'SELECT booking_id, uni, schedule_no, source_station, dest_station FROM BookingHistory WHERE Booking_id="' + bookingid + '"'
        cursor.execute(booking_query)
        return cursor.fetchone()

class update_schedule:
    def authorize_uni(self, cursor, uni, line):
        uni_query = 'SELECT role FROM Staff WHERE uni="' + uni + '" AND line="' + line + '"'
        cursor.execute(uni_query)
        return cursor.fetchone()

    def find_line_stations(self, cursor, line):
        stations_query = 'SELECT stop_no FROM Stations WHERE line="' + line + '" ORDER BY stop_no'
        cursor.execute(stations_query)
        return cursor.fetchall()

    def find_line_schedules(self, cursor, line):
        schedules_query = 'SELECT DISTINCT schedule_no FROM Schedule, Stations WHERE Schedule.stop_id = Stations.stop_id AND line="' + line + '"'
        cursor.execute(schedules_query)
        return cursor.fetchall()

    def make_schedule_updates(self, cursor, uni, line, station, schedule, delay):
        update_query = 'INSERT into ScheduleUpdate'\
                       '(SELECT "' + uni + '", Stations.stop_id, ' + schedule + ', time, addtime(time, sec_to_time(' + delay + '*60)), now() '\
                       'FROM Schedule, Stations '\
                       'WHERE Stations.stop_id=Schedule.stop_id '\
                       'AND Stations.stop_id=ANY'\
                       '(SELECT stop_id FROM Stations WHERE line="' + line + '" AND stop_no>=' + station + ') '\
                       'AND schedule_no=' + schedule + ')'
        return (cursor.execute(update_query) >= 1)

    def make_schedule_changes(self, cursor, line, station, schedule, delay):
        changes_query = 'UPDATE Schedule SET time=addtime(time, sec_to_time(' + delay + '*60)) '\
                        'WHERE stop_id=ANY'\
                        '(SELECT stop_id FROM Stations WHERE line="' + line + '" AND stop_no>=' + station + ') '\
                        'AND schedule_no=' + schedule
        return (cursor.execute(changes_query) >= 1)

    def get_updated_schedule(self, cursor, line, schedule):
        updated_schedule_query = 'SELECT stop_no, time FROM Schedule, Stations WHERE Schedule.stop_id=Stations.stop_id AND line="' + line + '" AND schedule_no=' + schedule + ' ORDER BY stop_no'
        cursor.execute(updated_schedule_query)
        return [[str(i) for i in j] for j in cursor.fetchall()]

    def commit_changes(self, connection):
        connection.commit()


class make_bookings:
    def __init__(self):
        self.findDestWhereClause = ""

    def get_buildings(self, cursor):
        cursor.execute("Select building_name from Buildings")
        data = cursor.fetchall()
        return [str(i[0]) for i in data]

    def get_dest(self, cursor, bname, street, avenue):
        bname_clause = " "
        avenue_clause = " "
        if bname:
            bname_clause = " and Route.source_stop = ANY (select stop_id from ClosestStop where building_id = (Select building_id from Buildings where building_name like \"%" + bname + "%\")) " 
        if avenue:
            avenue_clause = " and (avenue like \"%" + avenue + "%\") "
        
        self.findDestWhereClause = " where source_stop = ANY(select stop_id from Stations where street = \"" + street + "\"" + avenue_clause + ") " + bname_clause

        findDestQuery = "Select distinct S.street, S.avenue from Route, Stations S " + self.findDestWhereClause + "and S.stop_id = dest_stop"         
        cursor.execute(findDestQuery)
        data = cursor.fetchall()
        return [[str(i) for i in j] for j in data]

    def get_schedule(self, cursor, source, dest_st, dest_ave):
        findAllSources = "ANY(select source_stop from Route, Stations S " + self.findDestWhereClause + ")"
        findAllStopids = "ANY(select stop_id from Stations where street = " + str(dest_st) + " and avenue = \"" + dest_ave +"\")"
        findScQuery = "select S.line, src.stop_id, dst.stop_id, src.schedule_no, S.street, S.avenue, src.time, timediff(dst.time,src.time) as JourneyTime from Schedule src, Schedule dst, Stations S where S.stop_id = src.stop_id and S.line = (select line from Stations where stop_id = dst.stop_id) and (dst.stop_id = " + findAllStopids + ") and (src.stop_id = " + findAllSources + ") and (src.schedule_no = dst.schedule_no) and abs(timediff(dst.time, src.time)) > time(000000) order by src.time" 
        cursor.execute(findScQuery)
        data = cursor.fetchall()
        return [[str(i) for i in j] for j in data]

    def registerBooking(self, cursor, uni, schedule):
        cursor.execute("select 1 from Members where uni = \"" + uni + "\"")
        result =  cursor.fetchall()
        if len(result) <= 0:
            return [result, -1]
        if int(result[0][0]) != 1:
            return [int(result[0][0]), -1]
        cursor.execute("select max(booking_id) from BookingHistory")
        curBookingID = int(cursor.fetchone()[0]) + 1
        insertQuery = "insert into BookingHistory values(" + str(curBookingID) + ", now(), \"" + uni + "\", " + schedule[3] + ", \"" + schedule[1] + "\", \"" + schedule[2] + "\")"
        rowcnt = cursor.execute(insertQuery)
        print "rowcnt = ", rowcnt
        if rowcnt == 1:
            return [curBookingID, 1]
        else:
            return [rowcnt, 0]

