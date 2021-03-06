"""
MagPy
Intermagnet input filter
Written by Roman Leonhardt December 2012
- contains test, read and write functions for
        IMF 1.22,1.23
        IAF
        ImagCDF
        IYFV    (yearly means)
        DKA     (k values)d
        BLV     (baseline data)
"""
from __future__ import print_function

from magpy.stream import *

def isIMF(filename):
    """
    Checks whether a file is ASCII IMF 1.22,1.23 minute format.
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    try:
        if not 63 <= len(temp) <= 65:  # Range which regards any variety of return
            return False
        if temp[3] == ' ' and temp[11] == ' ' and temp[29] == ' ' and temp[45] == ' ' and temp[46] == 'R':
            pass
        else:
            return False
    except:
        return False

    print("Found IMF data")
    return True


def isIMAGCDF(filename):
    """
    Checks whether a file is ImagCDF format.
    """
    try:
        temp = cdf.CDF(filename)
    except:
        return False
    try:
        form = temp.attrs['FormatDescription']
        if not form[0].startswith('INTERMAGNET'):
            return False
    except:
        return False
    return True


def isIAF(filename):
    """
    Checks whether a file is BIN IAF INTERMAGNET Archive format.
    """

    try:
        temp = open(filename, 'rb').read(64)
        data= struct.unpack('<4s4l4s4sl4s4sll4s4sll', temp)
    except:
        return False
    try:
        date = str(data[1])
        if not len(date) == 7:
            return False
    except:
        return False
    try:
        datetime.strptime(date,"%Y%j")
    except:
        return False

    return True


def isBLV(filename):
    """
    Checks whether a file is ASCII IMF 1.22,1.23 minute format.
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    try:
        if not 63 <= len(temp) <= 65:  # Range which regards any variety of return
            return False
        if temp[3] == ' ' and temp[11] == ' ' and temp[29] == ' ' and temp[45] == ' ' and temp[46] == 'R':
            pass
        else:
            return False
    except:
        return False
    return True


def isIYFV(filename):
    """
    Checks whether a file is ASCII IYFV 1.01 yearly mean format.

    _YYYY.yyy_DDD_dd.d_III_ii.i_HHHHHH_XXXXXX_YYYYYY_ZZZZZZ_FFFFFF_A_EEEE_NNNCrLf
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    try:
        searchstr = ['ANNUAL MEAN VALUES', 'Annual Mean Values', 'annual mean values']
        for elem in searchstr:
            if temp.find(elem) > 0:
                return True
    except:
        return False
    return False


def isDKA(filename):
    """
    Checks whether a file is ASCII DKA k value format.

                               AAA
                  Geographical latitude:    43.250 N
                  Geographical longitude:   76.920 E

            K-index values for 2010     (K9-limit =  300 nT)
    """
    ok = False
    try:
        fh = open(filename, 'rt')
        temp1 = fh.readline()
        temp2 = fh.readline()
        temp3 = fh.readline()
        temp4 = fh.readline()
        temp5 = fh.readline()
        temp6 = fh.readline()
    except:
        return False
    try:
        searchstr = ['latitude', 'LATITUDE']
        for elem in searchstr:
            if temp2.find(elem) > 0:
                ok = True
        if not ok:
            return False
        searchstr = ['K-index values', 'K-INDEX VALUES']
        for elem in searchstr:
            if temp5.find(elem) > 0:
                return True
    except:
        return False
    return False


def readIAF(filename, headonly=False, **kwargs):
    """
    DESCRIPTION:
        Reading Intermagnet archive data format
    PARAMETER:
        resolution      (string) one of day,hour,minute,k   - default is minute

    """
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    resolution = kwargs.get('resolution')

    getfile = True
    gethead = True

    if not resolution:
        resolution = 'minutes'
    stream = DataStream()
    # Check whether header infromation is already present

    headers = {}

    data = []
    key = None

    if starttime:
        begin = stream._testtime(starttime)
    if endtime:
        end = stream._testtime(endtime)

    x,y,z,f,xho,yho,zho,fho,xd,yd,zd,fd,k,ir = [],[],[],[],[],[],[],[],[],[],[],[],[],[]
    datelist = []

    fh = open(filename, 'rb')
    while True:
      try:
        getline = True
        start = fh.read(64)
        head = struct.unpack('<4s4l4s4sl4s4sll4s4sll', start)
        date = datetime.strptime(str(head[1]),"%Y%j")
        datelist.append(date)
        if starttime:
            if date < begin:
                getline = False
        if endtime:
            if date > end:
                getline = False
        if getline:
            # unpack header
            if gethead:
                stream.header['StationIAGAcode'] = head[0].strip()
                headers['StationID'] = head[0].strip()
                #
                headers['DataAcquisitionLatitude'] = (90-float(head[2]))/1000.
                headers['DataAcquisitionLongitude'] = float(head[3])/1000.
                headers['DataElevation'] = head[4]
                headers['DataComponents'] = head[5].lower()
                for c in head[5].lower():
                    if c == 'g':
                        headers['col-df'] = 'dF'
                        headers['unit-col-df'] = 'nT'
                    else:
                        headers['col-'+c] = c
                        headers['unit-col-'+c] = 'nT'
                keystr = ','.join([c for c in head[5].lower()])
                if len(keystr) < 6:
                    keystr = keystr + ',f'
                keystr = keystr.replace('d','y')
                keystr = keystr.replace('g','df')
                keystr = keystr.replace('h','x')
                headers['StationInstitution'] = head[6]
                headers['DataConversion'] = head[7]
                headers['DataQuality'] = head[8]
                headers['SensorType'] = head[9]
                headers['StationK9'] = head[10]
                headers['DataDigitalSampling'] = head[11]
                headers['DataSensorOrientation'] = head[12].lower()
                pubdate = datetime.strptime(str(head[13]),"%y%m")
                headers['DataPublicationDate'] = pubdate
                gethead = False
            # get minute data
            xb = fh.read(5760)
            x.extend(struct.unpack('<1440l', xb))
            #x = np.asarray(struct.unpack('<1440l', xb))/10. # needs an extend
            yb = fh.read(5760)
            y.extend(struct.unpack('<1440l', yb))
            zb = fh.read(5760)
            z.extend(struct.unpack('<1440l', zb))
            fb = fh.read(5760)
            f.extend(struct.unpack('<1440l', fb))
            # get hourly means
            xhb = fh.read(96)
            xho.extend(struct.unpack('<24l', xhb))
            #xho = np.asarray(struct.unpack('<24l', xhb))/10.
            yhb = fh.read(96)
            yho.extend(struct.unpack('<24l', yhb))
            zhb = fh.read(96)
            zho.extend(struct.unpack('<24l', zhb))
            fhb = fh.read(96)
            fho.extend(struct.unpack('<24l', fhb))
            # get daily means
            xdb = fh.read(4)
            xd.extend(struct.unpack('<l', xdb))
            ydb = fh.read(4)
            yd.extend(struct.unpack('<l', ydb))
            zdb = fh.read(4)
            zd.extend(struct.unpack('<l', zdb))
            fdb = fh.read(4)
            fd.extend(struct.unpack('<l', fdb))
            kb = fh.read(32)
            k.extend(struct.unpack('<8l', kb))
            ilb = fh.read(16)
            ir.extend(struct.unpack('<4l', ilb))
      except:
        break
    fh.close()

    #x = np.asarray([val for val in x if not val > 888880])/10.   # use a pythonic way here
    x = np.asarray(x)/10.
    x[x > 88880] = float(nan)
    y = np.asarray(y)/10.
    y[y > 88880] = float(nan)
    z = np.asarray(z)/10.
    z[z > 88880] = float(nan)
    f = np.asarray(f)/10.
    f[f > 88880] = float(nan)
    f[f < -44440] = float(nan)
    xho = np.asarray(xho)/10.
    xho[xho > 88880] = float(nan)
    yho = np.asarray(yho)/10.
    yho[yho > 88880] = float(nan)
    zho = np.asarray(zho)/10.
    zho[zho > 88880] = float(nan)
    fho = np.asarray(fho)/10.
    fho[fho > 88880] = float(nan)
    fho[fho < -44440] = float(nan)
    xd = np.asarray(xd)/10.
    xd[xd > 88880] = float(nan)
    yd = np.asarray(yd)/10.
    yd[yd > 88880] = float(nan)
    zd = np.asarray(zd)/10.
    zd[zd > 88880] = float(nan)
    fd = np.asarray(fd)/10.
    fd[fd > 88880] = float(nan)
    fd[fd < -44440] = float(nan)
    k = np.asarray(k).astype(float)
    k[k > 880] = float(nan)
    ir = np.asarray(ir)

    # ndarray
    def data2array(arlist,keylist,starttime,sr):
        array = [[] for key in KEYLIST]
        ta = []
        val = starttime
        for ind, elem in enumerate(arlist[0]):
            ta.append(date2num(val))
            val = val+timedelta(seconds=sr)
        array[0] = np.asarray(ta)
        for idx,ar in enumerate(arlist):
            pos = KEYLIST.index(keylist[idx])
            array[pos] = np.asarray(ar)

        return np.asarray(array)

    if resolution in ['day','days','Day','Days','DAY','DAYS']:
        ndarray = data2array([xd,yd,zd,fd],keystr.split(','),min(datelist),sr=86400)
        headers['DataSamplingRate'] = '86400 sec'
    elif resolution in ['hour','hours','Hour','Hours','HOUR','HOURS']:
        ndarray = data2array([xho,yho,zho,fho],keystr.split(','),min(datelist)+timedelta(minutes=30),sr=3600)
        headers['DataSamplingRate'] = '3600 sec'
    elif resolution in ['k','K']:
        ndarray = data2array([k,ir],['var1','var2'],min(datelist)+timedelta(minutes=90),sr=10800)
        headers['DataSamplingRate'] = '10800 sec'
    else:
        ndarray = data2array([x,y,z,f],keystr.split(','),min(datelist),sr=60)
        headers['DataSamplingRate'] = '60 sec'

    return DataStream([LineStruct()], headers, ndarray)


def writeIAF(datastream, filename, **kwargs):
    """
    Writing Intermagnet archive format (2.1)
    """

    kvals = kwargs.get('kvals')
    mode = kwargs.get('mode')

    df=False
    # Check whether data is present at all
    if not len(datastream.ndarray[0]) > 0:
        print("writeIAF: No data found - check ndarray")
        return False
    # Check whether minute file
    sr = datastream.samplingrate()
    if not int(sr) == 60:
        print("writeIAF: Minute data needs to be provided")
        return False
    # check whether data covers one month
    tdiff = int(np.round(datastream.ndarray[0][-1]-datastream.ndarray[0][0]))
    if not tdiff >= 28:
        print("writeIAF: Data needs to cover one month")
        return False

    try:
        # Convert data to XYZ if HDZ
        if datastream.header['DataComponents'].startswith('HDZ'):
            datastream = datastream.hdz2xyz()
    except:
        print("writeIAF: HeaderInfo on DataComponents seems to be missing")
        return False

    try:
        # Preserve sampling filter of original data
        dsf = datastream.header['DataSamplingFilter']
    except:
        dsf = ''

    # Check whether f is contained (or delta f)
    # if f calc delta f
    dfpos = KEYLIST.index('df')
    fpos = KEYLIST.index('f')
    dflen = len(datastream.ndarray[dfpos])
    flen = len(datastream.ndarray[fpos])
    if not dflen == len(datastream.ndarray[0]):
        #check for F and calc
        if not flen == len(datastream.ndarray[0]):
            df=False
        else:
            datastream = datastream.delta_f()
            df=True
            if datastream.header['DataComponents'] in ['HDZ','XYZ']:
                datastream.header['DataComponents'] += 'G'
            if datastream.header['DataSensorOrientation'] in ['HDZ','XYZ']:
                datastream.header['DataSensorOrientation'] += 'F'
    else:
        df=True
        if datastream.header['DataComponents'] in ['HDZ','XYZ']:
            datastream.header['DataComponents'] += 'G'
        if datastream.header['DataSensorOrientation'] in ['HDZ','XYZ']:
            datastream.header['DataSensorOrientation'] += 'F'

    # Eventually converting Locations data
    proj = datastream.header.get('DataLocationReference','')
    longi = datastream.header.get('DataAcquisitionLongitude',' ')
    lati = datastream.header.get('DataAcquisitionLatitude',' ')
    if not longi=='' or lati=='':
        if proj == '':
            pass
        else:
            if proj.find('EPSG:') > 0:
                epsg = int(proj.split('EPSG:')[1].strip())
                if not epsg==4326:
                    longi,lati = convertGeoCoordinate(float(longi),float(lati),'epsg:'+str(epsg),'epsg:4326')
    datastream.header['DataAcquisitionLongitude'] = longi
    datastream.header['DataAcquisitionLatitude'] = lati
    datastream.header['DataLocationReference'] = 'WGS84, EPSG:4326'

    # Check whether all essential header info is present
    requiredinfo = ['StationIAGAcode','StartDate','DataAcquisitionLatitude', 'DataAcquisitionLongitude', 'DataElevation', 'DataComponents', 'StationInstitution', 'DataConversion', 'DataQuality', 'SensorType', 'StationK9', 'DataDigitalSampling', 'DataSensorOrientation', 'DataPublicationDate','FormatVersion','Reserved']

    # cycle through data - day by day
    t0 = int(datastream.ndarray[0][1])
    output = ''
    kstr=[]
    for i in range(tdiff):
        dayar = datastream._select_timerange(starttime=t0+i,endtime=t0+i+1)
        if len(dayar[0]) > 1440:
            print ("format_IMF: found {} datapoints (expected are 1440) - assuming last value(s) to represent next month".format(len(dayar[0])))
            dayar = np.asarray([elem[:1440] for elem in dayar])
        # get all indicies
        temp = DataStream([LineStruct],datastream.header,dayar)
        temp = temp.filter(filter_width=timedelta(minutes=60), resampleoffset=timedelta(minutes=30), filter_type='flat')

        head = []
        reqinfotmp = requiredinfo
        for elem in requiredinfo:
            try:
                if elem == 'StationIAGAcode':
                    value = datastream.header['StationIAGAcode']
                    value = value[:3]
                    #print value
                elif elem == 'StartDate':
                    value = int(datetime.strftime(num2date(datastream.ndarray[0][1]),'%Y%j'))
                elif elem == 'DataAcquisitionLatitude':
                    if not float(datastream.header['DataAcquisitionLatitude']) < 90 and float(datastream.header['DataAcquisitionLatitude']) > -90:
                        print("Latitude and Longitude need to be provided in Degree")
                        x=1/0
                    value = int(np.round((90-float(datastream.header['DataAcquisitionLatitude']))*1000))
                elif elem == 'DataAcquisitionLongitude':
                    value = int(np.round(float(datastream.header['DataAcquisitionLongitude'])*1000))
                elif elem == 'DataElevation':
                    value = int(np.round(float(datastream.header['DataElevation'])))
                    datastream.header['DataElevation'] = value
                elif elem == 'DataConversion':
                    value = int(np.round(float(datastream.header['DataConversion'])))
                elif elem == 'DataPublicationDate':
                    print (datastream.header['DataPublicationDate'])
                    value = datetime.strftime(datastream._testtime(datastream.header['DataPublicationDate']),'%y%m')
                elif elem == 'FormatVersion':
                    value = 3
                elif elem == 'StationK9':
                    value = int(np.round(float(datastream.header['StationK9'])))
                elif elem == 'DataDigitalSampling':
                    try:
                        value = int(datastream.header['DataDigitalSampling'])
                    except:
                        value = 1234
                elif elem == 'Reserved':
                    value = 0
                else:
                    value = datastream.header[elem]
                head.append(value)
                reqinfotmp = [el for el in reqinfotmp if not el==elem]
            except:
                if elem == 'DataPublicationDate':
                    print("DataPublicationDate --  appending current date")
                    value = datetime.strftime(datetime.utcnow(),'%y%m')
                    head.append(value)
                else:
                    print("Check {}: eventually missing in datastream header".format(reqinfotmp))
                    print("  --  critical information missing in data header  --")
                    print("  ---------------------------------------------------")
                    print(" Please provide: StationIAGAcode, DataAcquisitionLatitude, ")
                    print(" DataAcquisitionLongitude, DataElevation, DataConversion, ")
                    print(" DataComponents, StationInstitution, DataQuality, SensorType, ")
                    print(" StationK9, DataDigitalSampling, DataSensorOrientation")
                    print(" e.g. data.header['StationK9'] = 750")
                    return False

        # Constructing header Info
        packcode = '4s4l4s4sl4s4sll4s4sll' # fh.read(64)
        head_bin = struct.pack(packcode,*head)

        #print ("0:", len(head))
        # add minute values
        packcode += '1440l' # fh.read(64)
        xvals = np.asarray([elem if not isnan(elem) else 99999.9 for elem in dayar[1]])
        xvals = np.asarray(xvals*10).astype(int)
        head.extend(xvals)
        #print ("0a:", len(head))
        packcode += '1440l' # fh.read(64)
        yvals = np.asarray([elem if not isnan(elem) else 99999.9 for elem in dayar[2]])
        yvals = np.asarray(yvals*10).astype(int)
        head.extend(yvals)
        packcode += '1440l' # fh.read(64)
        zvals = np.asarray([elem if not isnan(elem) else 99999.9 for elem in dayar[3]])
        zvals = np.asarray(zvals*10).astype(int)
        head.extend(zvals)
        #print ("0c:", len(head))
        packcode += '1440l' # fh.read(64)
        if df:
            dfvals = np.asarray([elem if not isnan(elem) else 99999.9 for elem in dayar[dfpos]])
            dfvals = np.asarray(dfvals*10).astype(int)
        else:
            dfvals = np.asarray([888888]*len(dayar[0])).astype(int)
        head.extend(dfvals)

        # add hourly means
        packcode += '24l'
        xhou = np.asarray([elem if not isnan(elem) else 99999.9 for elem in temp.ndarray[1]])
        xhou = np.asarray(xhou*10).astype(int)
        head.extend(xhou)
        packcode += '24l'
        yhou = np.asarray([elem if not isnan(elem) else 99999.9 for elem in temp.ndarray[2]])
        yhou = np.asarray(yhou*10).astype(int)
        head.extend(yhou)
        packcode += '24l'
        zhou = np.asarray([elem if not isnan(elem) else 99999.9 for elem in temp.ndarray[3]])
        zhou = np.asarray(zhou*10).astype(int)
        head.extend(zhou)
        packcode += '24l'
        if df:
            dfhou = np.asarray([elem if not isnan(elem) else 99999.9 for elem in temp.ndarray[dfpos]])
            dfhou = np.asarray(dfhou*10).astype(int)
        else:
            dfhou = np.asarray([888888]*24).astype(int)
        head.extend(dfhou)

        #print ("2:", len(head))

        # add daily means
        packcode += '4l'
        # -- drop all values above 88888
        xvalid = np.asarray([elem for elem in xvals if elem < 888880])
        yvalid = np.asarray([elem for elem in yvals if elem < 888880])
        zvalid = np.asarray([elem for elem in zvals if elem < 888880])
        if len(xvalid)>0.9*len(xvals):
            head.append(int(np.mean(xvalid)))
        else:
            head.append(999999)
        if len(xvalid)>0.9*len(xvals):
            head.append(int(np.mean(yvalid)))
        else:
            head.append(999999)
        if len(xvalid)>0.9*len(xvals):
            head.append(int(np.mean(zvalid)))
        else:
            head.append(999999)
        if df:
            dfvalid = np.asarray([elem for elem in dfvals if elem < 88888])
            if len(dfvalid)>0.9*len(dfvals):
                head.append(int(np.mean(dfvalid)))
            else:
                head.append(999999)
        else:
            head.append(888888)

        #print("3:", len(head))

        # add k values
        if kvals:
            dayk = kvals._select_timerange(starttime=t0+i,endtime=t0+i+1)
            kdat = dayk[KEYLIST.index('var1')]
            kdat = [el if not np.isnan(el) else 999 for el in kdat]
            #print(len(kdat), t0+i,t0+i+1,kdat,dayk[0])
            packcode += '8l'
            if not len(kdat) == 8:
                ks = [999]*8
            else:
                ks = kdat
            sumk = int(sum(ks))
            if sumk > 999:
                sumk = 999
            linestr = "  {0}   {1}".format(datetime.strftime(num2date(t0+i),'%d-%b-%y'), datetime.strftime(num2date(t0+i),'%j'))
            tup = tuple([str(int(elem)) for elem in ks])
            linestr += "{0:>6}{1:>5}{2:>5}{3:>5}{4:>7}{5:>5}{6:>5}{7:>5}".format(*tup)
            linestr += "{0:>9}".format(str(sumk))
            kstr.append(linestr)
            head.extend(ks)
        else:
            packcode += '8l'
            ks = [999]*8
            head.extend(ks)
        # add reserved
        packcode += '4l'
        reserved = [0,0,0,0]
        head.extend(reserved)

        #print(len(ks))
        #print [num2date(elem) for elem in temp.ndarray[0]]
        line = struct.pack(packcode,*head)
        output = output + line

    path = os.path.split(filename)
    filename = os.path.join(path[0],path[1].upper())

    if len(kstr) > 0:
        station=datastream.header['StationIAGAcode']
        k9=datastream.header['StationK9']
        lat=datastream.header['DataAcquisitionLatitude']
        lon=datastream.header['DataAcquisitionLongitude']
        year=str(int(datetime.strftime(num2date(datastream.ndarray[0][1]),'%y')))
        ye=str(int(datetime.strftime(num2date(datastream.ndarray[0][1]),'%Y')))
        kfile = os.path.join(path[0],station.upper()+year+'K.DKA')
        print("Writing k summary file:", kfile)
        head = []
        if not os.path.isfile(kfile):
            head.append("{0:^66}".format(station.upper()))
            head2 = '                  Geographical latitude: {:>10.3} N'.format(lat)
            head3 = '                  Geographical longitude:{:>10.3} E'.format(lon)
            head4 = '            K-index values for {0}     (K9-limit = {1:>4} nT)'.format(ye, k9)
            head5 = '  DA-MON-YR  DAY #    1    2    3    4      5    6    7    8       SK'
            emptyline = ''
            head.append("{0:<50}".format(head2))
            head.append("{0:<50}".format(head3))
            head.append("{0:<50}".format(emptyline))
            head.append("{0:<50}".format(head4))
            head.append("{0:<50}".format(emptyline))
            head.append("{0:<50}".format(head5))
            head.append("{0:<50}".format(emptyline))
            with open(kfile, "wb") as myfile:
                for elem in head:
                    myfile.write(elem+'\r\n')
                #print elem
        # write data
        with open(kfile, "a") as myfile:
            for elem in kstr:
                myfile.write(elem+'\r\n')
                #print elem

    print("Writing monthly IAF data format:", path[1].upper())
    if os.path.isfile(filename):
        if mode == 'append':
            with open(filename, "a") as myfile:
                myfile.write(output)
        else: # overwrite mode
            os.remove(filename)
            myfile = open(filename, "wb")
            myfile.write(output)
            myfile.close()
    else:
        myfile = open(filename, "wb")
        myfile.write(output)
        myfile.close()

    print("Creating README from header info:", path[1].upper())
    readme = True
    if readme:
        requiredhead = ['StationName','StationInstitution', 'StationStreet','StationCity','StationPostalCode','StationCountry','StationWebInfo', 'StationEmail','StationK9']
        acklist = ['StationName','StationInstitution', 'StationStreet','StationCity','StationPostalCode','StationCountry','StationWebInfo' ]
        conlist = ['StationName','StationInstitution', 'StationStreet','StationCity','StationPostalCode','StationCountry', 'StationEmail']

        for h in requiredhead:
            try:
                test = datastream.header[h]
            except:
                print ("README file could not be generated")
                print ("Info on {0} is missing".format(h))
                return True
        ack = []
        contact = []
        for a in acklist:
            try:
                ack.append("               {0}".format(datastream.header[a]))
            except:
                pass
        for c in conlist:
            try:
                contact.append("               {0}".format(datastream.header[c]))
            except:
                pass

        # 1. Check completeness of essential header information
        station=datastream.header['StationIAGAcode']
        stationname = datastream.header['StationName']
        k9=datastream.header['StationK9']
        lat=datastream.header['DataAcquisitionLatitude']
        lon=datastream.header['DataAcquisitionLongitude']
        ye=str(int(datetime.strftime(num2date(datastream.ndarray[0][1]),'%Y')))
        rfile = os.path.join(path[0],"README."+station.upper())
        head = []
        print("Writing README file:", rfile)

        if not os.path.isfile(rfile):
            emptyline = ''
            head.append("{0:^66}".format(station.upper()))
            head.append("{0:<50}".format(emptyline))
            head.append("{0:>23} OBSERVATORY INFOMATION {1:>5}".format(stationname.upper(), ye))
            head.append("{0:<50}".format(emptyline))
            head.append("ACKNOWLEDGEMT: Users of {0:}-data should acknowledge:".format(station.upper()))
            for elem in ack:
                head.append(elem)
            head.append("{0:<50}".format(emptyline))
            head.append("STATION ID   : {0}".format(station.upper()))
            head.append("LOCATION     : {0}, {1}".format(datastream.header['StationCity'],datastream.header['StationCountry']))
            head.append("ORGANIZATION : {0:<50}".format(datastream.header['StationInstitution']))
            head.append("CO-LATITUDE  : {:.2} Deg.".format(90-float(lat)))
            head.append("LONGITUDE    : {:.2} Deg. E".format(float(lon)))
            head.append("ELEVATION    : {0} meters".format(int(datastream.header['DataElevation'])))
            head.append("{0:<50}".format(emptyline))
            head.append("ABSOLUTE")
            head.append("INSTRUMENTS  : please insert manually")
            head.append("RECORDING")
            head.append("VARIOMETER   : please insert manually")
            head.append("ORIENTATION  : {0}".format(datastream.header['DataSensorOrientation']))
            head.append("{0:<50}".format(emptyline))
            head.append("DYNAMIC RANGE: please insert manually")
            head.append("RESOLUTION   : please insert manually")
            head.append("SAMPLING RATE: please insert manually")
            head.append("FILTER       : {0}".format(dsf))
            # Provide method with head of kvals
            head.append("K-NUMBERS    : Computer derived (FMI method, MagPy)")
            head.append("K9-LIMIT     : {0:>4} nT".format(k9))
            head.append("{0:<50}".format(emptyline))
            head.append("GINS         : please insert manually")
            head.append("SATELLITE    : please insert manually")
            head.append("OBSERVER(S)  : please insert manually")
            head.append("ENGINEER(S)  : please insert manually")
            head.append("CONTACT      : ")
            for elem in contact:
                head.append(elem)
            with open(rfile, "wb") as myfile:
                for elem in head:
                    myfile.write(elem+'\r\n')
            myfile.close()

    return True


def readIMAGCDF(filename, headonly=False, **kwargs):
    """
    Reading Intermagnet CDF format (1.1)
    """

    print("FOUND IMAGCDF")

    cdfdat = cdf.CDF(filename)
    # get Attribute list
    attrslist = [att for att in cdfdat.attrs]
    # get Data list
    datalist = [att for att in cdfdat]
    headers={}

    arraylist = []
    array = [[] for elem in KEYLIST]
    startdate = cdfdat[datalist[-1]][0]

    #  #################################
    # Get header info:
    #  #################################
    if 'FormatDescription' in attrslist:
        form = cdfdat.attrs['FormatDescription']
        headers['DataFormat'] = str(cdfdat.attrs['FormatDescription'])
    if 'FormatVersion' in attrslist:
        vers = cdfdat.attrs['FormatVersion']
        headers['DataFormat'] = str(form) + '; ' + str(vers)
    if 'Title' in attrslist:
        pass
    if 'IagaCode' in attrslist:
        headers['StationIAGAcode'] = str(cdfdat.attrs['IagaCode'])
        headers['StationID'] = str(cdfdat.attrs['IagaCode'])
    if 'ElementsRecorded' in attrslist:
        headers['DataComponents'] = str(cdfdat.attrs['ElementsRecorded'])
    if 'PublicationLevel' in attrslist:
        headers['DataPublicationLevel'] = str(cdfdat.attrs['PublicationLevel'])
    if 'PublicationDate' in attrslist:
        headers['DataPublicationDate'] = str(cdfdat.attrs['PublicationDate'])
    if 'ObservatoryName' in attrslist:
        headers['StationName'] = str(cdfdat.attrs['ObservatoryName'])
    if 'Latitude' in attrslist:
        headers['DataAcquisitionLatitude'] = str(cdfdat.attrs['Latitude'])
    if 'Longitude' in attrslist:
        headers['DataAcquisitionLongitude'] = str(cdfdat.attrs['Longitude'])
    if 'Elevation' in attrslist:
        headers['DataElevation'] = str(cdfdat.attrs['Elevation'])
    if 'Institution' in attrslist:
        headers['StationInstitution'] = str(cdfdat.attrs['Institution'])
    if 'VectorSensOrient' in attrslist:
        headers['DataSensorOrientation'] = str(cdfdat.attrs['VectorSensOrient'])
    if 'StandardLevel' in attrslist:
        headers['DataStandardLevel'] = str(cdfdat.attrs['StandardLevel'])
    if 'StandardName' in attrslist:
        headers['DataStandardName'] = str(cdfdat.attrs['StandardName'])
    if 'StandardVersion' in attrslist:
        headers['DataStandardVersion'] = str(cdfdat.attrs['StandardVersion'])
    if 'PartialStandDesc' in attrslist:
        headers['DataPartialStandDesc'] = str(cdfdat.attrs['PartialStandDesc'])
    if 'Source' in attrslist:
        headers['DataSource'] = str(cdfdat.attrs['Source'])
    if 'TermsOfUse' in attrslist:
        headers['DataTerms'] = str(cdfdat.attrs['TermsOfUse'])
    if 'References' in attrslist:
        headers['DataReferences'] = str(cdfdat.attrs['References'])
    if 'UniqueIdentifier' in attrslist:
        headers['DataID'] = str(cdfdat.attrs['UniqueIdentifier'])
    if 'ParentIdentifiers' in attrslist:
        headers['SensorID'] = str(cdfdat.attrs['ParentIdentifier'])
    if 'ReferenceLinks' in attrslist:
        headers['StationWebInfo'] = str(cdfdat.attrs['ReferenceLinks'])

    #  #################################
    # Get data:
    #  #################################

    # Reorder datalist and Drop time column
    # #########################################################
    # 1. Get the amount of Times columns and associated lengths
    # #########################################################
    #print "Analyzing file structure and returning values"
    #print datalist
    mutipletimerange = False
    newdatalist = []
    tllist = []
    for elem in datalist:
        if elem.endswith('Times'):
            #print "Found Time Column"
            # Get length
            tl = int(str(cdfdat[elem]).split()[1].strip('[').strip(']'))
            #print "Length", tl
            tllist.append([tl,elem])
    if len(tllist) < 1:
        #print "No time column identified"
        # Check for starttime and sampling rate in header
        if 'StartTime' in attrslist and 'SamplingPeriod' in attrslist:
            # TODO Write that function
            st = str(cdfdat.attrs['StartTime'])
            sr = str(cdfdat.attrs['SamplingPeriod'])
        else:
            print("No Time information available - aborting")
            return
    elif len(tllist) > 1:
        tl = [el[0] for el in tllist]
        if not max(tl) == min(tl):
            print("Time columns of different length. Choosing longest as basis")
            newdatalist.append(max(tllist)[1])
            mutipletimerange = True
        else:
            print("Equal length time axes found - assuming identical time")
            if 'GeomagneticVectorTimes' in datalist:
                newdatalist.append(['time','GeomagneticVectorTimes'])
            else:
                newdatalist.append(['time',tllist[0][1]]) # Take the first one
    else:
        #print "Single time axis found in file"
        newdatalist.append(['time',tllist[0][1]])

    datalist = [elem for elem in datalist if not elem.endswith('Times')]

    # #########################################################
    # 2. Sort the datalist according to KEYLIST
    # #########################################################
    for key in KEYLIST:
        possvals = [key]
        if key == 'x':
            possvals.extend(['h','i'])
        if key == 'y':
            possvals.extend(['d','e'])
        if key == 'df':
            possvals.append('g')
        for elem in datalist:
            try:
                label = cdfdat[elem].attrs['LABLAXIS'].lower()
                if label in possvals:
                    newdatalist.append([key,elem])
            except:
                pass # for lines which have no Label

    if not len(datalist) == len(newdatalist)-1:
        print("error encountered in key assignment - please check")

    # 3. Create equal length array reducing all data to primary Times and filling nans for non-exist
    # (4. eventually completely drop time cols and just store start date and sampling period in header)
    # Deal with scalar data (independent or whatever

    for elem in newdatalist:
        if elem[0] == 'time':
            ar = date2num(cdfdat[elem[1]][...])
            arraylist.append(ar)
            ind = KEYLIST.index('time')
            array[ind] = ar
        else:
            ar = cdfdat[elem[1]][...]
            if elem[0] in NUMKEYLIST:
                ar[ar > 88880] = float(nan)
                ind = KEYLIST.index(elem[0])
                headers['col-'+elem[0]] = cdfdat[elem[1]].attrs['LABLAXIS'].lower()
                headers['unit-col-'+elem[0]] = cdfdat[elem[1]].attrs['UNITS']
                array[ind] = ar
                arraylist.append(ar)

    ndarray = np.array(array)

    stream = DataStream()
    stream = [LineStruct()]
    #stream = array2stream(arraylist,'time,x,y,z')

    #t2 = datetime.utcnow()
    #print "Duration for conventional stream assignment:", t2-t1

    return DataStream(stream,headers,ndarray)


def writeIMAGCDF(datastream, filename, **kwargs):
    """
    Writing Intermagnet CDF format (1.1)
    """

    print("Writing IMAGCDF Format", filename)
    mode = kwargs.get('mode')
    skipcompression = kwargs.get('skipcompression')

    if os.path.isfile(filename+'.cdf'):
        filename = filename+'.cdf'
    if os.path.isfile(filename):
        if mode == 'skip': # skip existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(exst,datastream)
            os.remove(filename)
            mycdf = cdf.CDF(filename, '')
        elif mode == 'replace': # replace existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(datastream,exst)
            os.remove(filename)
            mycdf = cdf.CDF(filename, '')
        elif mode == 'append':
            mycdf = cdf.CDF(filename, filename) # append????
        else: # overwrite mode
            #print filename
            os.remove(filename)
            mycdf = cdf.CDF(filename, '')
    else:
        mycdf = cdf.CDF(filename, '')

    keylst = datastream._get_key_headers()
    tmpkeylst = ['time']
    tmpkeylst.extend(keylst)
    keylst = tmpkeylst

    headers = datastream.header
    head, line = [],[]
    success = False

    ## Transfer MagPy Header to INTERMAGNET CDF attributes
    mycdf.attrs['FormatDescription'] = 'INTERMAGNET CDF format'
    mycdf.attrs['FormatVersion'] = '1.1'
    mycdf.attrs['Title'] = 'Geomagnetic time series data'
    for key in headers:
        if key == 'StationIAGAcode' or key == 'IagaCode':
            mycdf.attrs['IagaCode'] = headers[key]
        if key == 'DataComponents' or key == 'ElementsRecorded':
            mycdf.attrs['ElementsRecorded'] = headers[key].upper()
        if key == 'DataPublicationLevel' or key == 'PublicationLevel':
            mycdf.attrs['PublicationLevel'] = headers[key]
        if key == 'StationName' or key == 'ObservatoryName':
            mycdf.attrs['ObservatoryName'] = headers[key]
        if key == 'DataElevation' or key == 'Elevation':
            mycdf.attrs['Elevation'] = headers[key]
        if key == 'StationInstitution' or key == 'Institution':
            mycdf.attrs['Institution'] = headers[key]
        if key == 'DataSensorOrientation' or key == 'VectorSensOrient':
            mycdf.attrs['VectorSensOrient'] = headers[key].upper()
        if key == 'DataStandardVersion' or key == 'StandardVersion':
            mycdf.attrs['StandardVersion'] = headers[key]
        if key == 'DataPartialStandDesc' or key == 'PartialStandDesc':
            if headers['DataStandardLevel'] in ['partial','Partial']:
                print("writeIMAGCDF: Add PartialStandDesc items like IMOM-11,IMOM-12,IMOM-13")
            mycdf.attrs['PartialStandDesc'] = headers[key]
        if key == 'DataTerms' or key == 'TermsOfUse':
            mycdf.attrs['TermsOfUse'] = headers[key]
        if key == 'DataReferences' or key == 'References':
            mycdf.attrs['References'] = headers[key]
        if key == 'DataID' or key == 'UniqueIdentifier':
            mycdf.attrs['UniqueIdentifier'] = headers[key]
        if key == 'SensorID'or key == 'ParentIdentifier':
            mycdf.attrs['ParentIdentifier'] = headers[key]
        if key == 'StationWebInfo' or key == 'ReferenceLinks':
            mycdf.attrs['ReferenceLinks'] = headers[key]

    if not headers.get('DataPublicationDate','') == '':
        try:
            pubdate = cdf.datetime_to_tt2000(datastream._testtime(headers.get('DataPublicationDate','')))
        except:
            try:
                pubdate = datetime.strftime(datastream._testtime(headers.get('DataPublicationDate','')),"%Y-%m-%dT%H:%M:%S.%f")
            except:
                pubdate = datetime.strftime(datetime.utcnow(),"%Y-%m-%dT%H:%M:%S.%f")
        mycdf.attrs['PublicationDate'] = pubdate
    else:
        try:
            pubdate = cdf.datetime_to_tt2000(datetime.utcnow())
        except:
            pubdate = datetime.strftime(datetime.utcnow(),"%Y-%m-%dT%H:%M:%S.%f")
        mycdf.attrs['PublicationDate'] = pubdate

    if not headers.get('DataSource','')  == '':
        if headers.get('DataSource','') in ['INTERMAGNET', 'WDC']:
            mycdf.attrs['Source'] = headers.get('DataSource','')
        else:
            mycdf.attrs['Source'] = headers.get('DataSource','')
    else:
        mycdf.attrs['Source'] = headers.get('StationInstitution','')

    if not headers.get('DataStandardLevel','') == '':
        if headers[key] in ['None','none','Partial','partial','Full','full']:
            mycdf.attrs['StandardLevel'] = headers.get('DataStandardLevel','')
        else:
            print("writeIMAGCDF: StandardLevel not defined - please specify by yourdata.header['DataStandardLevel'] = ['None','Partial','Full']")
            mycdf.attrs['StandardLevel'] = 'None'
        if headers[key] in ['partial','Partial']:
            print("writeIMAGCDF: Don't forget - Add PartialStandDesc items like IMOM-11,IMOM-12,IMOM-13")
    else:
        print("writeIMAGCDF: StandardLevel not defined - please specify by yourdata.header['DataStandardLevel'] = ['None','Partial','Full']")
        mycdf.attrs['StandardLevel'] = 'None'

    if not headers.get('DataStandardName','') == '':
        mycdf.attrs['StandardName'] = headers.get('DataStandardName','')
    else:
        try:
            samprate = float(str(headers.get('DataSamplingRate',0)).replace('sec','').strip())
            if int(samprate) == 1:
                stdadd = 'INTERMAGNET_1-Second'
            elif int(samprate) == 60:
                stdadd = 'INTERMAGNET_1-Minute'
            if int(headers.get('DataPublicationLevel',0)) == 3:
                stdadd += '_QD'
                mycdf.attrs['StandardName'] = stdadd
            elif int(headers.get('DataPublicationLevel',0)) == 4:
                mycdf.attrs['StandardName'] = stdadd
        except:
            print ("writeIMAGCDF: Asigning StandardName Failed")

    proj = headers.get('DataLocationReference','')
    longi = headers.get('DataAcquisitionLongitude','')
    lati = headers.get('DataAcquisitionLatitude','')
    if not longi=='' or lati=='':
        if proj == '':
            mycdf.attrs['Latitude'] = lati
            mycdf.attrs['Longitude'] = longi
        else:
            if proj.find('EPSG:') > 0:
                epsg = int(proj.split('EPSG:')[1].strip())
                if not epsg==4326:
                    longi,lati = convertGeoCoordinate(float(longi),float(lati),'epsg:'+str(epsg),'epsg:4326')
            mycdf.attrs['Latitude'] = lati
            mycdf.attrs['Longitude'] = longi

    if not 'StationIagaCode' in headers and 'StationID' in headers:
        mycdf.attrs['IagaCode'] = headers.get('StationID','')

    def checkEqualIvo(lst):
        # http://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
        return not lst or lst.count(lst[0]) == len(lst)

    def checkEqual3(lst):
        return lst[1:] == lst[:-1]

    ndarray = False
    if len(datastream.ndarray[0]>0):
        ndarray = True

    for key in keylst:
        if key in ['time','sectime','x','y','z','f','dx','dy','dz','df','t1','t2']:
            ind = KEYLIST.index(key)
            if ndarray and len(datastream.ndarray[ind])>0:
                col = datastream.ndarray[ind]
            else:
                col = datastream._get_column(key)

            if not False in checkEqual3(col):
                print("Found identical values only:", key)
                col = col[:1]
            if key == 'time':
                key = 'GeomagneticVectorTimes'
                try: ## requires spacepy >= 1.5
                    mycdf[key] = np.asarray([cdf.datetime_to_tt2000(num2date(elem).replace(tzinfo=None)) for elem in col])
                except:
                    mycdf[key] = np.asarray([num2date(elem).replace(tzinfo=None) for elem in col])
            elif len(col) > 0:
                comps = datastream.header.get('DataComponents','')
                keyup = key.upper()
                if key in ['t1','t2']:
                    cdfkey = key.upper().replace('T','Temperature')
                else:
                    cdfkey = 'GeomagneticField'+key.upper()
                if not comps == '':
                    try:
                        if key == 'x':
                            compsupper = comps[0].upper()
                        elif key == 'y':
                            compsupper = comps[1].upper()
                        elif key == 'z':
                            compsupper = comps[2].upper()
                        else:
                            compsupper = key.upper()
                        cdfkey = 'GeomagneticField'+compsupper
                        keyup = compsupper
                    except:
                        cdfkey = 'GeomagneticField'+key.upper()
                        keyup = key.upper()
                #print(len(col), keyup, key)
                nonetest = [elem for elem in col if not elem == None]
                if len(nonetest) > 0:
                    mycdf[cdfkey] = col

                    mycdf[cdfkey].attrs['DEPEND_0'] = "GeomagneticVectorTimes"
                    mycdf[cdfkey].attrs['DISPLAY_TYPE'] = "time_series"
                    mycdf[cdfkey].attrs['LABLAXIS'] = keyup
                    mycdf[cdfkey].attrs['FILLVAL'] = np.nan
                    if key in ['x','y','z','h','e','g','t1','t2']:
                        mycdf[cdfkey].attrs['VALIDMIN'] = -88880.0
                        mycdf[cdfkey].attrs['VALIDMAX'] = 88880.0
                    elif key == 'i':
                        mycdf[cdfkey].attrs['VALIDMIN'] = -90.0
                        mycdf[cdfkey].attrs['VALIDMAX'] = 90.0
                    elif key == 'd':
                        mycdf[cdfkey].attrs['VALIDMIN'] = -360.0
                        mycdf[cdfkey].attrs['VALIDMAX'] = 360.0
                    elif key in ['f','s']:
                        mycdf[cdfkey].attrs['VALIDMIN'] = 0.0
                        mycdf[cdfkey].attrs['VALIDMAX'] = 88880.0


                for keydic in headers:
                    if keydic == ('col-'+key):
                        if key in ['x','y','z','f','dx','dy','dz','df']:
                            try:
                                mycdf[cdfkey].attrs['FIELDNAM'] = "Geomagnetic Field Element "+key.upper()
                            except:
                                pass
                        if key in ['t1','t2']:
                            try:
                                mycdf[cdfkey].attrs['FIELDNAM'] = "Temperature"+key.replace('t','')
                            except:
                                pass
                    if keydic == ('unit-col-'+key):
                        if key in ['x','y','z','f','dx','dy','dz','df','t1','t2']:
                            try:
                                if 'unit-col-'+key == 'deg C':
                                    #mycdf[cdfkey].attrs['FIELDNAM'] = "Temperature "+key.upper()
                                    unit = 'Celsius'
                                elif 'unit-col-'+key == 'deg':
                                    unit = 'Degrees of arc'
                                else:
                                    unit = headers.get('unit-col-'+key,'')
                                mycdf[cdfkey].attrs['UNITS'] = unit
                            except:
                                pass
            success = True

    if not skipcompression:
        try:
            mycdf.compress(cdf.const.GZIP_COMPRESSION, 5)
        except:
            print ("writeIMAGCDF: Compression failed for unknown reason - storing uncompresed data")
            pass
    mycdf.close()
    return success


def readIMF(filename, headonly=False, **kwargs):
    """
    Reading Intermagnet data format (IMF1.23)
    """
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    getfile = True

    fh = open(filename, 'rt')
    # read file and split text into channels
    stream = DataStream()
    # Check whether header infromation is already present
    #if stream.header is None:
    #    headers = {}
    #else:
    #    headers = stream.header
    headers = {}
    data = []
    key = None

    theday = extractDateFromString(filename)
    try:
        if starttime:
            if not theday[-1] >= datetime.date(stream._testtime(starttime)):
                getfile = False
            #if not theday >= datetime.date(stream._testtime(starttime)):
            #    getfile = False
        if endtime:
            #if not theday <= datetime.date(stream._testtime(endtime)):
            #    getfile = False
            if not theday[0] <= datetime.date(stream._testtime(endtime)):
                getfile = False
    except:
        # Date format not recognized. Need to read all files
        getfile = True

    if getfile:
        for line in fh:
            if line.isspace():
                # blank line
                continue
            elif line[29] == ' ':
                # data info
                block = line.split()
                #print block
                headers['StationID'] = block[0]
                headers['DataAcquisitionLatitude'] = float(block[7][:4])/10
                headers['DataAcquisitionLongitude'] = float(block[7][4:])/10
                headers['DataComponents'] = block[4]
                headers['DataSensorAzimuth'] = float(block[8])/10/60
                headers['DataSamplingRate'] = '60 sec'
                headers['DataType'] = block[5]
                datehh = block[1] + '_' + block[3]
                #print float(block[7][:4])/10, float(block[7][4:])/10, float(block[8])/10/60
                minute = 0
            elif headonly:
                # skip data for option headonly
                return
            else:
                # data entry - may be written in multiple columns
                # row beinhaltet die Werte eine Zeile
                data = line.split()
                for i in range(2):
                    try:
                        row = LineStruct()
                        time = datehh+':'+str(minute+i)
                        row.time=date2num(datetime.strptime(time,"%b%d%y_%H:%M"))
                        index = int(4*i)
                        if not int(data[0+index]) > 999990:
                            row.x = float(data[0+index])/10
                        else:
                            row.x = float(nan)
                        if not int(data[1+index]) > 999990:
                            row.y = float(data[1+index])/10
                        else:
                            row.y = float(nan)
                        if not int(data[2+index]) > 999990:
                            row.z = float(data[2+index])/10
                        else:
                            row.z = float(nan)
                        if not int(data[3+index]) > 999990:
                            row.f = float(data[3+index])/10
                        else:
                            row.f = float(nan)
                        row.typ = block[4].lower()
                        stream.add(row)
                    except:
                        logging.error('format_imf: problem with dataformat - check block header')
                        return DataStream(stream, headers)
                minute = minute + 2

    fh.close()

    return DataStream(stream, headers)


def writeIMF(datastream, filename, **kwargs):
    """
    Writing Intermagnet format data.
    """

    mode = kwargs.get('mode')
    version = kwargs.get('version')
    gin = kwargs.get('gin')
    datatype = kwargs.get('datatype')

    success = False
    # 1. check whether datastream corresponds to minute file
    if not 0.9 < datastream.get_sampling_period()*60*24 < 1.1:
        print ("format-imf: Data needs to be minute data for Intermagent - filter it accordingly")
        return False

    # 2. check whether file exists and according to mode either create, append, replace
    if os.path.isfile(filename):
        if mode == 'skip': # skip existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(exst,datastream)
            myFile= open( filename, "wb" )
        elif mode == 'replace': # replace existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(datastream,exst)
            myFile= open( filename, "wb" )
        elif mode == 'append':
            myFile= open( filename, "ab" )
        else: # overwrite mode
            #os.remove(filename)  ?? necessary ??
            myFile= open( filename, "wb" )
    else:
        myFile= open( filename, "wb" )

    # 3. Get essential header info
    header = datastream.header
    if not gin:
        gin = 'EDI'
    if not datatype:
        datatype = 'R' # reported; can also be 'A', 'Q', 'D'
    try:
        idc = header['StationID']
    except:
        print ("format-imf: No station code specified. Setting to XYZ ...")
        idc = 'XYZ'
        #return False
    try:
        colat = 90 - float(header['DataAcquisitionLatitude'])
        longi = float(header['DataAcquisitionLongitude'])
    except:
        print ("format-imf: No location specified. Setting 99,999 ...")
        colat = 99.9
        longi = 999.9
        #return False
    try:
        decbas = float(header['DataSensorAzimuth'])
    except:
        print ("format-imf: No orientation angle specified. Setting 999.9 ...")
        decbas = 999.9
        #return False

    # 4. Data
    dataline,blockline = '',''
    minuteprev = 0

    elemtype = 'XYZF'
    try:
        elemtpye = datastream.header['']
    except:
        pass

    fulllength = datastream.length()[0]
    ndtype = False
    if len(datastream.ndarray[0]) > 0:
        ndtype = True

    xind = KEYLIST.index('x')
    yind = KEYLIST.index('y')
    zind = KEYLIST.index('z')
    find = KEYLIST.index('f')
    for i in range(fulllength):
        if not ndtype:
            elem = datastream[i]
            elemx = elem.x
            elemy = elem.y
            elemz = elem.z
            elemf = elem.f
            timeval = elem.time
        else:
            elemx = datastream.ndarray[xind][i]
            elemy = datastream.ndarray[yind][i]
            elemz = datastream.ndarray[zind][i]
            elemf = datastream.ndarray[find][i]
            timeval = datastream.ndarray[0][i]

        date = num2date(timeval).replace(tzinfo=None)
        doy = datetime.strftime(date, "%j")
        day = datetime.strftime(date, "%b%d%y")
        hh = datetime.strftime(date, "%H")
        minute = int(datetime.strftime(date, "%M"))
        strcola = '%3.f' % (colat*10)
        strlong = '%3.f' % (longi*10)
        decbasis = str(int(np.round(decbas*60*10)))
        blockline = "%s %s %s %s %s %s %s %s%s %s %s\r\n" % (idc.upper(),day.upper(),doy, hh, elemtype, datatype, gin, strcola.zfill(4), strlong.zfill(4), decbasis.zfill(6),'RRRRRRRRRRRRRRRR')
        if minute == 0 and not i == 0:
            #print blockline
            myFile.writelines( blockline )
            pass
        if i == 0:
            #print blockline
            myFile.writelines( blockline )
            if not minute == 0:
                j = 0
                while j < minute:
                    if j % 2: # uneven
                         #AAAAAAA_BBBBBBB_CCCCCCC_FFFFFF__AAAAAAA_BBBBBBB_CCCCCCC_FFFFFFCrLf
                        dataline += '  9999999 9999999 9999999 999999'
                    else: # even
                        dataline = '9999999 9999999 9999999 999999'
                    j = j+1
        if not isnan(elemx):
            x = elemx*10
        else:
            x = 999999
        if not isnan(elemy):
            y = elemy*10
        else:
            y = 999999
        if not isnan(elemz):
            z = elemz*10
        else:
            z = 999999
        if not isnan(elemf):
            f = elemf*10
        else:
            f = 999999
        if minute > minuteprev + 1:
            while minuteprev+1 < minute:
                if minuteprev+1 % 2: # uneven
                    dataline += '  9999999 9999999 9999999 999999\r\n'
                    myFile.writelines( dataline )
                    #print minuteprev+1, dataline
                else: # even
                    dataline = '9999999 9999999 9999999 999999'
                minuteprev = minuteprev + 1
        minuteprev = minute
        if minute % 2: # uneven
            if len(dataline) < 10: # if record starts with uneven minute then
                dataline = '9999999 9999999 9999999 999999'
            dataline += '  %7.0f%8.0f%8.0f%7.0f\r\n' % (x, y, z, f)
            myFile.writelines( dataline )
            #print minute, dataline
        else: # even
            dataline = '%7.0f%8.0f%8.0f%7.0f' % (x, y, z, f)

    minute = minute + 1
    if not minute == 59:
        while minute < 60:
            if minute % 2: # uneven
                dataline += '  9999999 9999999 9999999 999999\r\n'
                myFile.writelines( dataline )
                #print minute, dataline
            else: # even
                dataline = '9999999 9999999 9999999 999999'
            minute = minute + 1

    myFile.close()

    return True



def readBLV(filename, headonly=False, **kwargs):
    """
    Reading Intermagnet data format (IMF1.23)
    """
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    getfile = True

    fh = open(filename, 'rt')
    # read file and split text into channels
    stream = DataStream()
    # Check whether header infromation is already present
    if stream.header is None:
        headers = {}
    else:
        headers = stream.header
    headers = {}

    data = []
    key = None

    # get day from filename (platform independent)
    theday = extractDateFromString(filename)
    try:
        if starttime:
            if not theday[-1] >= datetime.date(stream._testtime(starttime)):
                getfile = False
        if endtime:
            if not theday[0] <= datetime.date(stream._testtime(endtime)):
                getfile = False
    except:
        # Date format not recognized. Need to read all files
        getfile = True

    if getfile:
        for line in fh:
            if line.isspace():
                # blank line
                continue
            elif line[29] == ' ':
                # data info
                block = line.split()
                #print block
                headers['StationID'] = block[0]
                headers['DataAcquisitionLatitude'] = float(block[7][:4])/10
                headers['DataAcquisitionLongitude'] = float(block[7][4:])/10
                headers['DataComponents'] = block[4]
                headers['DataSensorAzimuth'] = float(block[8])/10/60
                headers['DataSamplingRate'] = '60 sec'
                headers['DataType'] = block[5]
                datehh = block[1] + '_' + block[3]
                #print float(block[7][:4])/10, float(block[7][4:])/10, float(block[8])/10/60
                minute = 0
            elif headonly:
                # skip data for option headonly
                return
            else:
                # data entry - may be written in multiple columns
                # row beinhaltet die Werte eine Zeile
                data = line.split()
                for i in range(2):
                    try:
                        row = LineStruct()
                        time = datehh+':'+str(minute+i)
                        row.time=date2num(datetime.strptime(time,"%b%d%y_%H:%M"))
                        index = int(4*i)
                        if not int(data[0+index]) > 999990:
                            row.x = float(data[0+index])/10
                        else:
                            row.x = float(nan)
                        if not int(data[1+index]) > 999990:
                            row.y = float(data[1+index])/10
                        else:
                            row.y = float(nan)
                        if not int(data[2+index]) > 999990:
                            row.z = float(data[2+index])/10
                        else:
                            row.z = float(nan)
                        if not int(data[3+index]) > 999990:
                            row.f = float(data[3+index])/10
                        else:
                            row.f = float(nan)
                        row.typ = block[4].lower()
                        stream.add(row)
                    except:
                        logging.error('format_imf - blv: problem with dataformat - check block header')
                        return DataStream(stream, headers)
                stream.add(row)
                minute = minute + 2

    fh.close()

    return DataStream(stream, headers)


def writeBLV(datastream, filename, **kwargs):
    """
    DESCRIPTION:
        Writing Intermagnet - baseline data.
        uses baseline function
    PARAMETERS:
        datastream      : (DataStream) basevalue data stream
        filename        : (string) path

      Optional:
        deltaF          : (float) average field difference in nT between DI pier and F
                          measurement position. If provided, this value is assumed to
                          represent the adopted value for all days: If not, then the baseline
                          function is assumed to be used.
        diff            : (ndarray) array containing dayly averages of delta F values between
                          variometer and F measurement
    """

    baselinefunction = kwargs.get('baselinefunction')
    fitfunc = kwargs.get('fitfunc')
    fitdegree = kwargs.get('fitdegree')
    knotstep = kwargs.get('knotstep')
    extradays = kwargs.get('extradays')
    mode = kwargs.get('mode')
    year = kwargs.get('year')
    meanh = kwargs.get('meanh')
    meanf = kwargs.get('meanf')
    keys = kwargs.get('keys')
    deltaF = kwargs.get('deltaF')
    diff = kwargs.get('diff')
    # add list for baseline data/jumps -> extract from db
    #  list contains time ranges and parameters for baselinecalc
    baseparam =  kwargs.get('baseparam')

    if not year:
        year = datetime.strftime(datetime.utcnow(),'%Y')
        t1 = date2num(datetime.strptime(str(int(year))+'-01-01','%Y-%m-%d'))
        t2 = date2num(datetime.utcnow())
    else:
        t1 = date2num(datetime.strptime(str(int(year))+'-01-01','%Y-%m-%d'))
        t2 = date2num(datetime.strptime(str(int(year)+1)+'-01-01','%Y-%m-%d'))

    absinfoline = []
    if diff:
        if diff.length()[0] > 1:
            absinfo = diff.header.get('DataAbsInfo','')
            if not absinfo == '':
                print("writeBLV: Getting Absolute info from header of provided dailymean file") 
                absinfoline = absinfo.split('_')
                extradays= int(absinfoline[2])
                fitfunc = absinfoline[3]
                fitdegree = int(absinfoline[4])
                knotstep = float(absinfoline[5])
                keys = ['dx','dy','dz']#,'df'] # absinfoline[6]

    if not extradays:
        extradays = 15
    if not fitfunc:
        fitfunc = 'spline'
    if not fitdegree:
        fitdegree = 5
    if not knotstep:
        knotstep = 0.1
    if not keys:
        keys = ['dx','dy','dz']#,'df']

    # 2. check whether file exists and according to mode either create, append, replace
    if os.path.isfile(filename):
        if mode == 'skip': # skip existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(exst,datastream)
            myFile= open( filename, "wb" )
        elif mode == 'replace': # replace existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(datastream,exst)
            myFile= open( filename, "wb" )
        elif mode == 'append':
            myFile= open( filename, "ab" )
        else: # overwrite mode
            #os.remove(filename)  ?? necessary ??
            myFile= open( filename, "wb" )
    else:
        myFile= open( filename, "wb" )

    print("writeBLV: file:", filename)

    # 3. check whether datastream corresponds to an absolute file and remove unreasonable inputs
    #     - check whether F measurements were performed at the main pier - delta F's are available

    try:
        if not datastream.header['DataFormat'] == 'MagPyDI':
            print("writeBLV: Format not recognized - needs to be MagPyDI")
            return False
    except:
        print("writeBLV: Format not recognized - should be MagPyDI")
        print("writeBLV: is not yet assigned during database access")
        #return False

    indf = KEYLIST.index('df')
    if len([elem for elem in datastream.ndarray[indf] if not np.isnan(float(elem))]) > 0:
        keys = ['dx','dy','dz','df']
    else:
        if not deltaF:
            array = np.asarray([88888.00]*len(datastream.ndarray[0]))
            datastream = datastream._put_column(array, 'df')
        else:
            array = np.asarray([deltaF]*len(datastream.ndarray[0]))
            datastream = datastream._put_column(array, 'df')

    # 4. create dummy stream with time range
    dummystream = DataStream()
    array = [[] for key in KEYLIST]
    row1, row2 = LineStruct(), LineStruct()
    row1.time = t1
    row2.time = t2
    array[0].append(row1.time)
    array[0].append(row2.time)
    indx = KEYLIST.index('dx')
    indy = KEYLIST.index('dy')
    indz = KEYLIST.index('dz')
    indf = KEYLIST.index('df')
    indFtype = KEYLIST.index('str4')
    for i in range(0,2):
        array[indx].append(0.0)
        array[indy].append(0.0)
        array[indz].append(0.0)
        array[indf].append(0.0)
    dummystream.add(row1)
    dummystream.add(row2)
    for idx, elem in enumerate(array):
        array[idx] = np.asarray(array[idx])
    dummystream.ndarray = np.asarray(array)

    #print("1", row1.time, row2.time)

    # 5. Extract the data for one year and calculate means
    backupabsstream = datastream.copy()
    if not len(datastream.ndarray[0]) > 0:
        backupabsstream = backupabsstream.linestruct2ndarray()

    datastream = datastream.trim(starttime=t1, endtime=t2)
    try:
        comps = datastream.header['DataComponents']
        if comps in ['IDFF','idff','idf','IDF']:
            datastream = datastream.idf2xyz()
            datastream = datastream.xyz2hdz()
        elif comps in ['XYZF','xyzf','xyz','XYZ']:
            datastream = datastream.xyz2hdz()
        comps = 'HDZF'
    except:
        # assume idf orientation
        datastream = datastream.idf2xyz()
        datastream = datastream.xyz2hdz()
        comps = 'HDZF'

    if not meanf:
        meanf = datastream.mean('f')
    if not meanh:
        meanh = datastream.mean('x')

    ##### ###########################################################################
    print("TODO: cycle through parameter baseparam here")
    print(" baseparam contains time ranges their valid baseline function parameters")
    print(" -> necessary for discontiuous fits")
    print(" join the independent year stream, and create datelist for marking jumps with d")
    ##### ###########################################################################

    # 6. calculate baseline function
    basefunction = dummystream.baseline(backupabsstream,keys=keys, fitfunc=fitfunc,fitdegree=fitdegree,knotstep=knotstep,extradays=extradays)

    yar = [[] for key in KEYLIST]
    datelist = [day+0.5 for day in range(int(t1),int(t2))]
    for idx, elem in enumerate(yar):
        if idx == 0:
            yar[idx] = np.asarray(datelist)
        elif idx in [indx,indy,indz,indf]:
            yar[idx] = np.asarray([0]*len(datelist))
        else:
            yar[idx] = np.asarray(yar[idx])


    yearstream = DataStream([LineStruct()],datastream.header,np.asarray(yar))
    yearstream = yearstream.func2stream(basefunction,mode='addbaseline',keys=keys)

    #print("writeBLV:", yearstream.length())

    #print "writeBLV: Testing deltaF (between Pier and F):"
    #print "adopted diff is yearly average"
    #print "adopted average daily delta F comes from diff of vario and scalar"
    #pos = KEYLIST.index('df')
    #dfl = [val for val in datastream.ndarray[pos] if not isnan(val)]
    #meandf = datastream.mean('df')
    #print "Mean df", meandf, mean(dfl)

    # 7. Get essential header info
    header = datastream.header
    try:
        idc = header['StationID']
    except:
        print("formatBLV: No station code specified. Aborting ...")
        logging.error("formatBLV: No station code specified. Aborting ...")
        return False
    headerline = '%s %5.f %5.f %s %s' % (comps.upper(),meanh,meanf,idc,year)
    myFile.writelines( headerline+'\r\n' )

    #print "writeBLV:", headerline

    # 8. Basevalues
    if len(datastream.ndarray[0]) > 0:
        for idx, elem in enumerate(datastream.ndarray[0]):
            if t2 >= elem >= t1:
                day = datetime.strftime(num2date(elem),'%j')
                x = float(datastream.ndarray[indx][idx])
                y = float(datastream.ndarray[indy][idx])*60.
                z = float(datastream.ndarray[indz][idx])
                df = float(datastream.ndarray[indf][idx])
                ftype = datastream.ndarray[indFtype][idx]
                if np.isnan(x):
                    x = 99999.00
                if np.isnan(y):
                    y = 99999.00
                if np.isnan(z):
                    z = 99999.00
                if np.isnan(df) or ftype.startswith('Fext'):
                    df = 99999.00
                line = '%s %9.2f %9.2f %9.2f %9.2f\r\n' % (day,x,y,z,df)
                myFile.writelines( line )
    else:
        datastream = datastream.trim(starttime=t1, endtime=t2)
        for elem in datastream:
            #DDD_aaaaaa.aa_bbbbbb.bb_zzzzzz.zz_ssssss.ssCrLf
            day = datetime.strftime(num2date(elem.time),'%j')
            if np.isnan(elem.x):
                x = 99999.00
            else:
                if not elem.typ == 'idff':
                    x = elem.x
                else:
                    x = elem.x*60
            if np.isnan(elem.y):
                y = 99999.00
            else:
                if elem.typ == 'xyzf':
                    y = elem.y
                else:
                    y = elem.y*60
            if np.isnan(elem.z):
                z = 99999.00
            else:
                z = elem.z
            if np.isnan(elem.df):
                f = 99999.00
            else:
                f = elem.df
            line = '%s %9.2f %9.2f %9.2f %9.2f\r\n' % (day,x,y,z,f)
            myFile.writelines( line )

    # 9. adopted basevalues
    myFile.writelines( '*\r\n' )
    #TODO: deltaf and continuity parameter from db
    parameter = 'c' # corresponds to m
    for idx, t in enumerate(yearstream.ndarray[0]):
        #001_AAAAAA.AA_BBBBBB.BB_ZZZZZZ.ZZ_SSSSSS.SS_DDDD.DD_mCrLf
        day = datetime.strftime(num2date(t),'%j')
        if np.isnan(yearstream.ndarray[indx][idx]):
            x = 99999.00
        else:
            if not comps.lower() == 'idff':
                x = yearstream.ndarray[indx][idx]
            else:
                x = yearstream.ndarray[indx][idx]*60.
        if np.isnan(yearstream.ndarray[indy][idx]):
            y = 99999.00
        else:
            if comps.lower() == 'xyzf':
                y = yearstream.ndarray[indy][idx]
            else:
                y = yearstream.ndarray[indy][idx]*60.
        if np.isnan(yearstream.ndarray[indz][idx]):
            z = 99999.00
        else:
            z = yearstream.ndarray[indz][idx]
        if deltaF:
            f = deltaF
        elif np.isnan(yearstream.ndarray[indf][idx]):
            f = 99999.00
        else:
            f = yearstream.ndarray[indf][idx]
        if diff:
            posdf = KEYLIST.index('df')
            indext = [i for i,tpos in enumerate(diff.ndarray[0]) if num2date(tpos).date() == num2date(t).date()]
            #print("Hello", posdf, diff.ndarray[0], diff.ndarray[posdf], len(diff.ndarray[0]),indext, t)
            #                                                     []       365           [0] 735599.5
            if len(indext) > 0:
                df = diff.ndarray[posdf][indext[0]]
                if np.isnan(df):
                    df = 999.00
            else:
                df = 999.00
        else:
            df = 888.00
        line = '%s %9.2f %9.2f %9.2f %9.2f %7.2f %s\r\n' % (day,x,y,z,f,df,parameter)
        myFile.writelines( line )

    # 9. comments
    myFile.writelines( '*\r\n' )
    myFile.writelines( 'Comments:\r\n' )
    absinfoline = dummystream.header.get('DataAbsInfo','').split('_')
    print ("Infoline", absinfoline)
    funcline1 = 'Baselinefunction: %s\r\n' % absinfoline[3]
    funcline2 = 'Degree: %s, Knots: %s\r\n' % (absinfoline[4],absinfoline[5])
    funcline3 = 'For adopted values the fit has been applied between\r\n'
    funcline4 = '%s and %s\r\n' % (str(num2date(float(absinfoline[0])).replace(tzinfo=None)),str(num2date(float(absinfoline[1])).replace(tzinfo=None)))
    # get some data:
    infolist = [] # contains all provided information for comment section
    db = False
    if not db:
        posst1 = KEYLIST.index('str2')
        infolist.append(datastream[-1].str2)
        infolist.append(datastream[-1].str3)
        infolist.append(datastream[-1].str4)
        #
    funcline5 = 'Measurements conducted primarily with:\r\n'
    funcline6 = 'DI: %s\r\n' % infolist[0]
    funcline7 = 'Scalar: %s\r\n' % infolist[1]
    funcline8 = 'Variometer: %s\r\n' % infolist[2]
    # additional text with pier, instrument, how f difference is defined, which are the instruments etc
    summaryline = '-- analysis supported by MagPy\r\n'
    myFile.writelines( '-'*40 + '\r\n' )
    myFile.writelines( funcline1 )
    myFile.writelines( funcline2 )
    myFile.writelines( funcline3 )
    myFile.writelines( funcline4 )
    myFile.writelines( funcline5 )
    myFile.writelines( funcline6 )
    myFile.writelines( funcline7 )
    myFile.writelines( '-'*40 + '\r\n' )
    myFile.writelines( summaryline )

    myFile.close()
    return True


def readIYFV(filename, headonly=False, **kwargs):
    """
    DESCRIPTION:
        Reads annual mean values. Elements given in column ELE are imported.
        Other components are calculated and checked against file content.
    PARAMETER:

                      ANNUAL MEAN VALUES

                      ALMA-ATA, AAA, KAZAKHSTAN

  COLATITUDE: 46.75   LONGITUDE: 76.92 E   ELEVATION: 1300 m

  YEAR        D        I       H      X      Y      Z      F   * ELE Note
           deg min  deg min    nT     nT     nT     nT     nT

 2005.500   4 46.6  62 40.9  25057  24970   2087  48507  54597 A XYZF   1
 2006.500   4 47.5  62 42.9  25044  24957   2092  48552  54631 A XYZF   1
 2007.500   4 47.8  62 45.8  25017  24930   2092  48603  54664 A XYZF   1

    """
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')

    endtime = kwargs.get('endtime')

    getfile = True

    stream = DataStream()
    headers = {}
    data = []
    key = None

    array = [[] for key in KEYLIST]

    fh = open(filename, 'rt')
    ok = True
    cnt = 0
    paracnt = 999998
    roworder=['d','i','h','x','y','z','f']
    jumpx,jumpy,jumpz,jumpf=0,0,0,0
    tsel = 'A' # Use only all days rows
    tprev = tsel # For jump treatment
    lc = KEYLIST.index('var5')  ## store the line number of each loaded line here
                                ## this is used by writeIYFV to add at the correct position
    newarray = []

    if ok:
        for line in fh:
            cnt = cnt+1
            if line.isspace():
                # blank line
                pass
            elif line.find('ANNUAL') > 0 or line.find('annual') > 0:
                pass
            elif cnt == 3:
                # station info
                block = line.split()
                #print(block)
                headers['StationName'] = block[0]
                headers['StationID'] = block[1]
                headers['StationCountry'] = block[2]
            elif line.find('COLATITUDE') > 0:
                loc = line.split()
                headers['DataAcquisitionLatitude'] = 90.0-float(loc[1])
                headers['DataAcquisitionLongitude'] = float(loc[3])
                headers['DataElevation'] = float(loc[3])
            elif line.find('COLATITUDE') > 0:
                loc = line.split()
                headers['DataAcquisitionLatitude'] = 90.0-float(loc[1])
                headers['DataAcquisitionLongitude'] = float(loc[3])
                headers['DataElevation'] = float(loc[3])
            elif line.find(' YEAR ') > 0:
                paracnt = cnt
                para = line.split()
                para = [elem.lower() for elem in para[1:8]]
            elif cnt == paracnt+1:
                units = line.split()
                tmp = ['deg','deg']
                tmp.extend(units[4:10])
                units = tmp
            elif line.startswith(' 1') or line.startswith(' 2'): # Upcoming year 3k problem ;)
                if not headonly:
                    # get data
                    data = line.split()
                    test = True
                    if test:
                        #try:
                        if not len(data) >= 12:
                            print("readIYFV: inconsistency of file format - ", len(data))
                        ye = data[0].split('.')
                        dat = ye[0]+'-06-01'
                        row = []
                        ti = date2num(datetime.strptime(dat,"%Y-%m-%d"))
                        row.append(dms2d(data[1]+':'+data[2]))
                        row.append(dms2d(data[3]+':'+data[4]))
                        row.append(float(data[5]))
                        row.append(float(data[6]))
                        row.append(float(data[7]))
                        row.append(float(data[8]))
                        row.append(float(data[9]))
                        t =  data[10]
                        ele =  data[11]
                        headers['DataComponents'] = ele
                        # transfer
                        if len(data) == 13:
                            note =  data[12]
                        if t == tsel:
                            array[0].append(ti)
                            array[lc].append(cnt)
                            """
                            for comp in ele.lower():
                                if comp in ['x','h','i']:
                                    headers['col-x'] = comp
                                    headers['unit-col-x'] = units[para.index(comp)]
                                    array[1].append(row[para.index(comp)]-jumpx)
                                elif comp in ['y','d']:
                                    headers['col-y'] = comp
                                    headers['unit-col-y'] = units[para.index(comp)]
                                    array[2].append(row[para.index(comp)]-jumpy)
                                elif comp in ['i','z']:
                                    headers['col-z'] = comp
                                    headers['unit-col-z'] = units[para.index(comp)]
                                    array[3].append(row[para.index(comp)]-jumpz)
                                elif comp in ['f']:
                                    headers['col-f'] = comp
                                    headers['unit-col-f'] = units[para.index(comp)]
                                    array[4].append(row[para.index(comp)]-jumpf)
                            """
                            headers['col-x'] = 'x'
                            headers['unit-col-x'] = units[para.index('x')]
                            headers['col-y'] = 'y'
                            headers['unit-col-y'] = units[para.index('y')]
                            headers['col-z'] = 'z'
                            headers['unit-col-z'] = units[para.index('z')]
                            headers['col-f'] = 'f'
                            headers['unit-col-f'] = units[para.index('f')]
                            array[1].append(row[para.index('x')]-jumpx)
                            array[2].append(row[para.index('y')]-jumpy)
                            array[3].append(row[para.index('z')]-jumpz)
                            array[4].append(row[para.index('f')]-jumpf)

                            checklist = coordinatetransform(array[1][-1],array[2][-1],array[3][-1],'xyz')
                            diffs = (np.array(row) - np.array(checklist))
                            for idx,el in enumerate(diffs):
                                goodval = True
                                if idx in [0,1]: ## Angular values
                                    if el > 0.008:
                                        goodval = False
                                else:
                                    if el > 0.8:
                                        goodval = False
                            if not goodval:
                                print("readIYFV: verify conversions between components !")
                                print("readIYFV: found:", np.array(row))
                                print("readIYFV: expected:", np.array(checklist))
                        elif t == 'J' and tprev == tsel:
                            jumpx = jumpx + row[para.index('x')]
                            jumpy = jumpy + row[para.index('y')]
                            jumpz = jumpz + row[para.index('z')]
                            jumpf = jumpf + row[para.index('f')]
                        tprev = tsel
    fh.close()

    array = [np.asarray(ar) for ar in array]
    stream = DataStream([LineStruct()], headers, np.asarray(array))

    if not ele.lower().startswith('xyz'):
        stream = stream._convertstream('xyz2'+ele.lower()[:3])

    return stream


def writeIYFV(datastream,filename, **kwargs):
    """
    DESCRIPTION:
        IYFV requires a datastream containing one year of data (if not kind='Q' or 'D' are given).
        Method calculates mean values and adds them to an eventually existing yearly mean file.
        Please note: jumps (J) need to be defined manually within the ASCII mean file.
    PARAMETERS:
        datastream:     (DataStream) containing the header info and one year of data.
                                     DataComponents should be provided in header.
                                     If data

        kind:           (string) One of Q,D,A -> default is A
        comment:        (string) a comment related to the datastream

    """

    kind = kwargs.get('kind')
    comment = kwargs.get('comment')

    if not kind in ['A','Q','D','q','d']:
        kind = 'A'
    else:
        kind = kind.upper()
    if comment:
        print (" writeIYFV: Comments not yet supported")
        #identify next note and add comment at the send of the file
        pass
    else:
        note = 0

    # check datastream
    if not datastream.length()[0] > 1:
        print (" writeIYFV: Datastream does not contain data")
        return False
    if not len(datastream.ndarray[1]) > 1:
        print (" writeIYFV: Datastream does not contain data")
        return False
    # check time range
    tmin, tmax = datastream._find_t_limits()
    tmin = date2num(tmin)
    tmax = date2num(tmax)
    meant = mean([tmin,tmax])
    if tmax-tmin < 365*0.9: # 90% of one year
        print (" writeIYFV: Datastream does not cover at least 90% of one year")
        return False
    # if timerange covers more than one year ??????
    # should be automatically called with coverage='year' and filenamebegins='yearmean',
    # filenameends=Obscode

    header = datastream.header
    comp = header.get('DataComponents','')
    comp = comp.lower()
    print(("writeIYFV: components found: ", comp))
    if not comp in ['hdz','xyz','idf','hez', 'hdzf','xyzf','idff','hezf', 'hdzg','xyzg','idfg','hezg']:
        print (" writeIYFV: valid DataComponents could not be read from header - assuming xyz data")
        comp = 'xyz'
    elif comp.startswith('hdz'):
        datastream = datastream.hdz2xyz()
    elif comp.startswith('idf'):
        datastream = datastream.idf2xyz()
    elif comp.startswith('hez'):
        alpha = header.get('DataSensorAzimuth','')
        if not is_number(alpha):
            print (" writeIYFV: hez provided but no DataSensorAzimuth (usually the declination while sensor installation - aborting")
            return False
        datastream = datastream.rotation(alpha=alpha)

    # Obtain means   ( drop nans ):
    meanx = datastream.mean('x',percentage=90)
    meany = datastream.mean('y',percentage=90)
    meanz = datastream.mean('z',percentage=90)
    if isnan(meanx) or isnan(meany) or isnan(meanz):
        print (" writeIYFV: found more then 10% of NaN values - setting minimum requirement to 40% data recovery and change kind to I (incomplete)")
        meanx = datastream.mean('x',percentage=40)
        meany = datastream.mean('y',percentage=40)
        meanz = datastream.mean('z',percentage=40)
        kind = 'I'
        if isnan(meanx) or isnan(meany) or isnan(meanz):
            print (" writeIYFV: less then 40% of data - skipping")
            return False
    meanyear = int(datetime.strftime(num2date(meant),"%Y"))
    # create datalist
    datalist = [meanyear]
    reslist = coordinatetransform(meanx,meany,meanz,'xyz')
    datalist.extend(reslist)

    #print ( "writeIYFV:", datalist )
    #print ( "writeIYFV: kind", kind )
    #print ( "writeIYFV: comment", comment )
    #kind = 'Q'
    #meanyear = '2011'

    #_YYYY.yyy_DDD_dd.d_III_ii.i_HHHHHH_XXXXXX_YYYYYY_ZZZZZZ_FFFFFF_A_EEEE_NNNCrLf
    decsep= str(datalist[1]).split('.')
    incsep= str(datalist[2]).split('.')
    newline = " {0}.500 {1:>3} {2:4.1f} {3:>3} {4:4.1f} {5:>6} {6:>6} {7:>6} {8:>6} {9:>6} {10:>1} {11:>4} {12:>3}\r\n".format(meanyear,decsep[0],float('0.'+str(decsep[1]))*60.,incsep[0],float('0.'+str(incsep[1]))*60.,int(datalist[3]),int(datalist[4]),int(datalist[5]),int(datalist[6]),int(datalist[7]), kind, comp.upper(), int(note))

    # create dummy header (check for existing values) and add data
    # inform observer to modify/check head
    def createhead(filename, locationname,coordlist,newline):
        """
        internal method to create header info for yearmean file
        """
        if not len(coordlist) == 3:
            print ("writeIYFV: Coordinates missing")
            if len(coordlist) == 2:
                coordlist.append(np.nan)
            else:
                return False

        empty = "\r\n"
        content = []
        content.append("{:^70}\r\n".format("ANNUAL MEAN VALUES"))
        content.append(empty)
        content.append("{:^70}\r\n".format(locationname))
        content.append(empty)
        content.append("  COLATITUDE: {a:.2f}   LONGITUDE: {b:.2f} E   ELEVATION: {c:.0f} m\r\n".format(a=coordlist[0],b=coordlist[1],c=coordlist[2]))
        content.append(empty)
        content.append("  YEAR        D        I       H      X      Y      Z      F   * ELE Note\r\n")
        content.append("           deg min  deg min    nT     nT     nT     nT     nT\r\n")
        content.append(empty)
        content.append(newline)
        content.append(empty)
        content.append("* A = All days\r\n")
        content.append("* Q = Quiet days\r\n")
        content.append("* D = Disturbed days\r\n")
        content.append("* I = Incomplete\r\n")
        content.append("* J = Jump:         jump value = old site value - new site value\r\n")

        f = open(filename, "w")
        contents = "".join(content)
        f.write(contents)
        f.close()
        """
                      ANNUAL MEAN VALUES

                      ALMA-ATA, AAA, KAZAKHSTAN

  COLATITUDE: 46.75   LONGITUDE: 76.92 E   ELEVATION: 1300 m

  YEAR        D        I       H      X      Y      Z      F   * ELE Note
           deg min  deg min    nT     nT     nT     nT     nT

* A = All days
* Q = Quet days
* D = Disturbed days
* I = Incomplete
* J = Jump:         jump value = old site value - new site value
        """

    def addline(filename, newline, kind, year):
        """
        internal method to insert new yearly means in a file
        """
        content = []
        fh = open(filename, 'r')
        for line in fh:
            content.append(line)
        fh.close()

        yearlst = []
        foundcomm = False

        for idx,elem in enumerate(content):
            ellst = elem.split()
            if len(ellst)>11:
                if ellst[10] == kind:
                    # get years
                    yearlst.append([idx, int(ellst[0].split('.')[0])])
            if elem.startswith('*') and not foundcomm: # begin of comment section
                foundcomm = True
                commidx = idx

        if not foundcomm: # No comment section - append at the end of file
            commidx = idx

        if not len(yearlst) > 0: # e.g. kind not yet existing
            # add line just above footer
            content.insert(commidx, '')
            content.insert(commidx, newline)
        else:
            years = [el[1] for el in yearlst]
            indicies = [el[0] for el in yearlst]
            if year in years:
                idx= indicies[years.index(year)]
                content[idx] = newline
            elif int(year) > np.max(years):
                idx= indicies[years.index(max(years))]
                content.insert(idx+1, newline)
            elif int(year) < np.min(years):
                idx= indicies[years.index(min(years))]
                content.insert(idx, newline)
            elif int(year) > np.min(years) and int(year) < np.max(years):
                for i,y in enumerate(years):
                    if int(y) > int(year):
                        break
                idx = indicies[i]
                content.insert(idx, newline)

        f = open(filename, "w")
        contents = "".join(content)
        f.write(contents)
        f.close()

    if os.path.isfile(filename):
        addline(filename, newline, kind, meanyear)
    else:
        name = header.get('StationName',' ')
        co = header.get('StationIAGAcode',' ')
        coun = header.get('StationCountry',' ')
        locationname = "{a:>34}, {b}, {c:<23}".format(a=name[:35],b=co,c=coun[:25])
        lat = header.get('DataAcquisitionLatitude',np.nan)
        lon = header.get('DataAcquisitionLongitude',np.nan)
        elev = header.get('DataElevation',np.nan)
        coordlist = [float(lat), float(lon), float(elev)]
        createhead(filename, locationname, coordlist, newline)

    return True

def readDKA(filename, headonly=False, **kwargs):
    """
                               AAA
                  Geographical latitude:    43.250 N
                  Geographical longitude:   76.920 E

            K-index values for 2010     (K9-limit =  300 nT)

  DA-MON-YR  DAY #    1    2    3    4      5    6    7    8       SK

  01-JAN-10   001     0    1    0    0      0    1    1    2        5
  02-JAN-10   002     0    1    2    1      1    1    0    0        6
  03-JAN-10   003     0    0    1    2      2    2    0    1        8
  04-JAN-10   004     1    1    1    1      1    0    1    1        7
    """

    getfile = True

    stream = DataStream()
    headers = {}
    data = []
    key = None

    array = [[] for key in KEYLIST]

    fh = open(filename, 'rt')
    ok = True
    cnt = 0
    datacoming = 0
    kcol = KEYLIST.index('var1')

    if ok:
        for line in fh:
            cnt = cnt+1
            block = line.split()
            if line.isspace():
                # blank line
                pass
            elif cnt == 1:
                # station info
                headers['StationID'] = block[0]
                headers['StationIAGAcode'] = block[0]
            elif line.find('latitude') > 0 or line.find('LATITUDE') > 0:
                headers['DataAcquisitionLatitude'] = float(block[-2])
            elif line.find('longitude') > 0 or line.find('LONGITUDE') > 0:
                headers['DataAcquisitionLongitude'] = float(block[-2])
            elif line.find('K9-limit') > 0:
                headers['StationK9'] = float(block[-2])
            elif line.find('DA-MON-YR') > 0:
                datacoming = cnt
            elif cnt > datacoming:
                if len(block) > 9:
                    for i in range(8):
                        ti = datetime.strptime(block[0],"%d-%b-%y") + timedelta(minutes=90) + timedelta(minutes=180*i)
                        val = float(block[2+i])
                        array[0].append(date2num(ti))
                        if val < 990:
                            array[kcol].append(val)
                        else:
                            array[kcol].append(np.nan)

    fh.close()
    headers['col-var1'] = 'K'
    headers['unit-col-var1'] = ''

    array = [np.asarray(ar) for ar in array]
    stream = DataStream([LineStruct()], headers, np.asarray(array))

    # Eventually add trim
    return stream


def writeDKA(datastream, filename, **kwargs):
    pass
