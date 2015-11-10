def get_dest(cursor, bname, street, avenue):
    bname_clause = " "
    avenue_clause = " "
    if bname:
        bname_clause = " and Route.source_stop = ANY (select stop_id from ClosestStop where building_id = (Select building_id from Buildings where building_name like \"%" + bname + "%\")) " 
    if avenue:
        avenue_clause = " and (avenue like \"%" + avenue + "%\") "
    
    findDestQuery = "Select distinct source_stop, dest_stop, S.street, S.avenue, Distance from Route, Stations S where source_stop = ANY(select stop_id from Stations where Street = \"" + street + "\"" + avenue_clause + ") and S.stop_id = dest_stop" + bname_clause
    
    print findDestQuery 
    cursor.execute(findDestQuery)
    return cursor.fetchall()

def get_schedule(cursor, source_stop, dest_stop):
    findScQuery = "select S.line, src.schedule_no, S.street, S.avenue, src.time, timediff(dst.time,src.time) as JourneyTime from Schedule src, Schedule dst, Stations S where S.line = (select line from Stations where stop_id=\"" + dest_stop + "\") and (src.stop_id = S.stop_id) and (dst.stop_id = \"" + dest_stop + "\") and (src.stop_id = \"" + source_stop + "\") and (src.schedule_no = dst.schedule_no) and timediff(dst.time, src.time) > time(000000)" 
    print findScQuery
    cursor.execute(findScQuery)
    data = cursor.fetchall()
    print data
    return [[str(i) for i in j] for j in data]

def registerBooking(cursor, uni, schedule, dest):
    cursor.execute("select 1 from Members where uni = \"" + uni + "\"")
    result =  cursor.fetchall()
    if len(result) <= 0:
        return [result, -1]
    if int(result[0][0]) != 1:
        return [int(result[0][0]), -1]
    cursor.execute("select max(booking_id) from BookingHistory")
    curBookingID = int(cursor.fetchone()[0]) + 1
    insertQuery = "insert into BookingHistory values(" + str(curBookingID) + ", now(), \"" + uni + "\", " + schedule[1] + ", \"" + dest[0] + "\", \"" + dest[1] + "\")"
    rowcnt = cursor.execute(insertQuery)
    print "rowcnt = ", rowcnt
    return [rowcnt, 1]
