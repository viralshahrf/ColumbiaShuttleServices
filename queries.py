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
        cursor.execute("SELECT building_name FROM Buildings")
        data = cursor.fetchall()
        return ([''] + [str(i[0]) for i in data])
    
    def get_loc_from_bname(self, cursor, bname):
        query = "SELECT DISTINCT street, avenue FROM Stations, Buildings, ClosestStop "\
                "WHERE building_name = \"" + bname + "\"" \
                "AND Stations.stop_id = ClosestStop.stop_id "\
                "AND ClosestStop.building_id = Buildings.building_id "
        cursor.execute(query)
        data = cursor.fetchall()
        data = [[str(i) for i in j] for j in data]
        return data[0]

    def get_dest(self, cursor, bname, street, avenue):
        bname_clause = " "
        avenue_clause = " "
        if bname:
            bname_clause = " AND Route.source_stop = "\
                           " ANY (SELECT stop_id FROM ClosestStop"\
                           " WHERE building_id = (SELECT building_id FROM Buildings "\
                           " WHERE building_name like \"%" + bname + "%\")) " 
        if avenue:
            avenue_clause = " AND (avenue like \"%" + avenue + "%\") "
        
        self.findDestWhereClause = " WHERE source_stop = "\
                       " ANY(SELECT stop_id FROM Stations "\
                       " WHERE street = \"" + street + "\"" + avenue_clause + ") "\
                        + bname_clause

        findDestQuery = "SELECT distinct S.street, S.avenue "\
                        "FROM Route, Stations S " + self.findDestWhereClause + \
                        "AND S.stop_id = dest_stop"         
        cursor.execute(findDestQuery)
        data = cursor.fetchall()
        return [[str(i) for i in j] for j in data]

    def get_schedule(self, cursor, source, dest_st, dest_ave):
        findAllSources = "ANY(SELECT source_stop FROM Route, Stations S "\
                          + self.findDestWhereClause + ")"
        findAllDests = "ANY(SELECT stop_id FROM Stations "\
                         "WHERE street = " + str(dest_st) + " AND avenue = \"" + dest_ave +"\")"
        findScQuery = "SELECT S.line, src.stop_id, dst.stop_id, src.schedule_no, S.street, "\
                      "S.avenue, src.time, timediff(dst.time,src.time) AS JourneyTime "\
                      "FROM Schedule src, Schedule dst, Stations S "\
                      "WHERE S.stop_id = src.stop_id "\
                      "AND S.line = (SELECT line FROM Stations WHERE stop_id = dst.stop_id) "\
                      "AND (dst.stop_id = " + findAllDests + ") "\
                      "AND (src.stop_id = " + findAllSources + ") "\
                      "AND (src.schedule_no = dst.schedule_no) "\
                      "AND abs(timediff(dst.time, src.time)) > time(000000) order by src.time" 
        cursor.execute(findScQuery)
        data = cursor.fetchall()
        return [[str(i) for i in j] for j in data]

    def registerBooking(self, cursor, uni, schedule):
        schedule_no = schedule[3]
        source = schedule[1]
        dest = schedule[2]        
        cursor.execute("SELECT 1 FROM Members WHERE uni = \"" + uni + "\"")
        result =  cursor.fetchone()
        if result == None:
            return [result, -1]
        cursor.execute("SELECT max(booking_id) FROM BookingHistory")
        curBookingID = int(cursor.fetchone()[0]) + 1

        insertQuery = "insert into BookingHistory values("\
                    + str(curBookingID) + ", now(), \"" + uni + "\", "\
                    + schedule_no + ", \"" + source + "\", \"" + dest + "\")"
        rowcnt = cursor.execute(insertQuery)
        if rowcnt == 1:
            return [curBookingID, 1]
        else:
            return [rowcnt, 0]

