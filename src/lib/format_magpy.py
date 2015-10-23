"""
MagPy
MagPy input/output filters 
Written by Roman Leonhardt June 2012
- contains test and read function, toDo: write function
"""

from stream import *

import gc


# K0 (Browsing - not for Serious Science) ACE-EPAM data from the OMNI database:
k0_epm_KEYDICT = {#'H_lo',			# H (0.48-0.97 MeV)	(UNUSED)
		'Ion_very_lo': 'var1',		# Ion (47-65 keV) 1/(cm2 s ster MeV)
		'Ion_lo': 'var2',		# Ion (310-580 keV) 1/(cm2 s ster MeV)
		'Ion_mid': 'var3',		# Ion (310-580 keV) 1/(cm2 s ster MeV)
		'Ion_hi': 'var5',		# Ion (1060-1910 keV) 1/(cm2 s ster MeV)
		'Electron_lo': 'z',		# Electron (38-53 keV) 1/(cm2 s ster MeV)
		'Electron_hi': 'f'		# Electron (175-315 keV) 1/(cm2 s ster MeV)
		   }
# H1 (Level 2 final 5min data) ACE-EPAM data from the OMNI database:
h1_epm_KEYDICT = {
		'P1': 'var1',			# Ion (47-65 keV) 1/(cm2 s ster MeV)
		'P3': 'var2',			# Ion (115-195 keV) 1/(cm2 s ster MeV)
		'P5': 'var3',			# Ion (310-580 keV) 1/(cm2 s ster MeV)
		'P7': 'var5',			# Ion (1060-1910 keV) 1/(cm2 s ster MeV)
		'DE1': 'z',			# Electron (38-53 keV) 1/(cm2 s ster MeV)
		'DE4': 'f'			# Electron (175-315 keV) 1/(cm2 s ster MeV)
		# (... Many, MANY other unused keys.)
		   }
# H0 (Level 2 final 64s data) ACE-SWEPAM data from the OMNI database:
h0_swe_KEYDICT = {
		'Np': 'var1',			# H_Density #/cc
		'Vp': 'var2',			# SW_H_Speed km/s
		'Tpr': 'var3',			# H_Temp_radial Kelvin
		# (... Many other keys unused.)
		   }
# H0 (Level 2 final 16s data) ACE-MAG data from the OMNI database:
h0_mfi_KEYDICT = {
		'Magnitude': 'f',		# B-field total magnitude (Bt)
		'BGSM': ['x','y','z'],		# B-field in GSM coordinates (Bx, By, Bz)
		#'BGSEc': ['x','y','z'],	# B-field in GSE coordinates
		# (... Many other keys unused.)
		   }

def isPYCDF(filename):
    """
    Checks whether a file is Nasa CDF format.
    """
    try:
        temp = cdf.CDF(filename)
    except:
        return False
    try:
        if not 'Epoch' in temp:
            if not 'time' in temp:
                return False
    except:
        return False

    #loggerlib.debug("format_magpy: Found PYCDF file %s" % filename)
    return True


def isPYSTR(filename):
    """
    Checks whether a file is ASCII PyStr format.
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    if not temp.startswith(' # MagPy - ASCII'):
        return False

    #loggerlib.debug("format_magpy: Found PYSTR file %s" % filename)
    return True


def isPYASCII(filename):
    """
    Checks whether a file is ASCII PyStr format.
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    if not temp.startswith(' # MagPy ASCII'):
        return False

    #loggerlib.debug("format_magpy: Found PYSTR file %s" % filename)
    return True


def isPYBIN(filename):
    """
    Checks whether a file is binary PyStr format.
    """
    try:
        temp = open(filename, 'rt').readline()
    except:
        return False
    if not temp.startswith('# MagPyBin'):
        return False

    #loggerlib.debug("format_magpy: Found PYBIN file %s" % filename)
    return True


def readPYASCII(filename, headonly=False, **kwargs):
    """
    Reading basic ASCII format data.
    Should look like:
	 # MagPy ASCII
	Time-days,Time,Temp[deg],Voltage[V]
	734928.0416666666,2013-03-01T01:00:00.000000,14061.940719529965,6.8539941994665305,11.869002442573095

    """
    stream = DataStream([],{})

    array = [[] for key in KEYLIST]

    # Check whether header infromation is already present
    if stream.header == None:
        headers = {}
    else:
        headers = stream.header

    loggerlib.info('readPYASCII: Reading %s' % (filename))
    qFile= file( filename, "rb" )
    csvReader= csv.reader( qFile )
    keylst = []
    timeconv = False
    timecol = -1

    for elem in csvReader:
        if elem==[]:
            # blank line
            pass
        elif elem[0].startswith('#'):
            # blank header
            pass
        elif elem[0].startswith(' #') and not elem[0].startswith(' # MagPy ASCII'):
            # attributes - assign header values
            headlst = elem[0].strip(' # ').split(':')
            headkey = headlst[0]
            headval = headlst[1]
            if not headkey.startswith('Column'):
                headers[headkey] = headval.strip()
        elif elem[0].startswith(' # MagPy ASCII'):
            # blank header
            pass
        elif elem[0].startswith('Time'): # extract column info and keys            
            for i in range(len(elem)):
                #print elem[i]
                if not elem[i].startswith('Time'):
                    try:  # neglecte columns without units (e.g. text)
                         headval = elem[i].split('[')                
                         colval = headval[0]
                         unitval = headval[1].strip(']')
                         exec('headers["col-'+NUMKEYLIST[len(keylst)]+'"] = colval')
                         exec('headers["unit-col-'+NUMKEYLIST[len(keylst)]+'"] = unitval')
                         keylst.append(i)
                    except:
                         pass
                elif elem[i] == 'Time' and not timecol > 0:
                    timecol = i
                    timeconv = True
                elif elem[i] == 'Time-days':
                    timecol = i
                    timeconv = False
            if len(keylst) > len(NUMKEYLIST):
                keylst = keylist[:len(NUMKEYLIST)]
        elif headonly:
            # skip data for option headonly
            continue
        else:
            try:
                if timeconv:
                    ti = date2num(stream._testtime(elem[timecol]))
                else:
                    ti = elem[timecol]
                array[0].append(ti)
                for idx,i in enumerate(keylst):
                    array[idx+1].append(float(elem[i]))
                    #print NUMKEYLIST[idx]
            except ValueError:
                pass
    qFile.close()

    #print np.asarray(array[0])
    #print np.asarray(array[1])
    #print np.asarray(array[2])
    #print headers
    # Clean up the file contents
    def checkEqual3(lst):
        return lst[1:] == lst[:-1]

    for idx,ar in enumerate(array):
        if len(ar) > 0:
            if KEYLIST[idx] in NUMKEYLIST:
                tester = float('nan')
            else:
                tester = '-'
            array[idx] = np.asarray(array[idx])
            if not False in checkEqual3(array[idx]) and ar[0] == tester:
                array[idx] = np.asarray([])

    return DataStream([LineStruct()], headers, np.asarray(array).astype(object))    



def readPYSTR(filename, headonly=False, **kwargs):
    """
    Reading ASCII PyMagStructure format data.
    """
    stream = DataStream([],{})

    array = [[] for key in KEYLIST]

    # Check whether header infromation is already present
    headers={}

    loggerlib.info('readPYSTR: Reading %s' % (filename))
    qFile= file( filename, "rb" )
    csvReader= csv.reader( qFile )

    for elem in csvReader:
        if elem==[]:
            # blank line
            pass
        elif elem[0].startswith('#'):
            # blank header
            pass
        elif elem[0].startswith(' #') and not elem[0].startswith(' # MagPy - ASCII'):
            # attributes - assign header values
            headlst = elem[0].strip(' # ').split(':')
            headkey = headlst[0]
            headval = headlst[1]
            if not headkey.startswith('Column'):
                headers[headkey] = headval.strip()
        elif elem[0].startswith(' # MagPy - ASCII'):
            # blank header
            pass
        elif elem[0]=='Epoch[]' or elem[0]=='-[]' or elem[0]=='time[]':
            for i in range(len(elem)):
                headval = elem[i].split('[')                
                colval = headval[0]
                unitval = headval[1].strip(']')
                exec('headers["col-'+KEYLIST[i]+'"] = colval')
                exec('headers["unit-col-'+KEYLIST[i]+'"] = unitval')
        elif headonly:
            # skip data for option headonly
            continue
        else:
            try:
                if not len(elem) == len(KEYLIST):
                    print "readPYSTR: Warning file contents does not fit to KEYLIST"
                for idx, key in enumerate(KEYLIST):
                    if key.find('time') >= 0:
                        try:
                            ti = date2num(datetime.strptime(elem[idx],"%Y-%m-%d-%H:%M:%S.%f"))
                        except:
                            try:
                                ti = date2num(datetime.strptime(elem[idx],"%Y-%m-%dT%H:%M:%S.%f"))
                            except:
                                ti = elem[idx]
                                pass
                                #raise ValueError, "Wrong date format in file %s" % filename
                        array[idx].append(ti)
                    else:
                        if key in NUMKEYLIST:
                            array[idx].append(float(elem[idx]))
                        else:
                            #if elem[idx] == '':
                            #    elem[idx] = '-'
                            array[idx].append(elem[idx])
            except ValueError:
                pass
    qFile.close()

    # Clean up the file contents
    def checkEqual3(lst):
        return lst[1:] == lst[:-1]

    for idx,ar in enumerate(array):
        if KEYLIST[idx] in NUMKEYLIST:
            tester = float('nan')
        else:
            tester = '-'
        array[idx] = np.asarray(array[idx])
        if not False in checkEqual3(array[idx]) and ar[0] == tester:
            array[idx] = np.asarray([])

    return DataStream([LineStruct()], headers, np.asarray(array).astype(object))    


def readPYCDF(filename, headonly=False, **kwargs):
    """
    Reading CDF format data - DTU type.
    """
    #stream = DataStream()
    #stream = DataStream([],{})
    stream = DataStream([],{},np.asarray([[] for key in KEYLIST]))

    array = [[] for key in KEYLIST]
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    oldtype = kwargs.get('oldtype')
    getfile = True

    #oldtype=True
    # Some identification parameters used by Juergs
    jind = ["H0", "D0", "Z0", "F0", "HNscv", "HEscv", "Zscv", "Basetrig", "time", \
"HNvar", "HEvar", "Zvar", "T1", "T2", "timeppm", "timegps", \
"timefge", "Fsc", "HNflag", "HEflag", "Zflag", "Fscflag", "FscQP", \
"T1flag", "T2flag", "Timeerr", "Timeerrtrig"]

    # Check whether header infromation is already present
    headskip = False
    if stream.header == None:
        stream.header.clear()
    else:
        headskip = True

    theday = extractDateFromString(filename)
    try:
        if starttime:
            if not theday >= datetime.date(stream._testtime(starttime)):
                getfile = False
        if endtime:
            if not theday <= datetime.date(stream._testtime(endtime)):
                getfile = False
    except:
        # Date format not recognized. Need to read all files
        getfile = True 
    logbaddata = False

    # Get format type:
    # Juergens DTU type is using different date format (MATLAB specific)
    # MagPy type is using datetime objects
    if getfile:
        try:
            cdf_file = cdf.CDF(filename)
        except:
            return stream
        try:
            cdfformat = cdf_file.attrs['DataFormat']
        except:
            logging.info("No format specification in CDF - passing")
            cdfformat = 'Unknown'
            pass
        OMNIACE = False
        try:
            title = str(cdf_file.attrs['TITLE'])
            if 'ACE' in title:
                OMNIACE = True
        except:
            pass
        
        if headskip:
            for key in cdf_file.attrs:
                if not key == 'DataAbsFunctionObject':
                    stream.header[key] = str(cdf_file.attrs[key])
                else:
                    print "Found DataAbsFunctionObject - loading and unpickling"
                    func = pickle.loads(str(cdf_file.attrs[key]))
                    stream.header[key] = func

        #if headonly:
        #    cdf_file.close()
        #    return DataStream(stream, stream.header)    

        loggerlib.info('Read: %s Format: %s ' % (filename, cdfformat))

        for key in cdf_file:
            #print key
            #try:
            #    print key, cdf_file[key].attrs['LABLAXIS'], cdf_file[key].attrs['UNITS']
            #except:
            #    print key
            # first get time or epoch column
            #lst = cdf_file[key]
            #print key
            if key.find('time')>=0 or key == 'Epoch':
                #ti = cdf_file[key][...]
                #row = LineStruct()
                if str(cdfformat) == 'MagPyCDF':
                    if not oldtype:
                        if not key == 'sectime':
                            ind = KEYLIST.index('time')
                        else:
                            ind = KEYLIST.index('sectime')
                        try:
                            array[ind] = np.asarray(date2num(cdf_file[key][...]))                        
                        except:
                            array[ind] = np.asarray([])
                            pass ### catches exceptions if sectime is nan
                    else:
                        #ti = [date2num(elem) for elem in ti]
                        #stream._put_column(ti,'time')
                        for elem in cdf_file[key][...]:
                            row = LineStruct()
                            row.time = date2num(elem)
                            stream.add(row)
                            del row
                else:
                    if not oldtype:
                        if key  == 'time':
                            ind = KEYLIST.index(key)
                            array[ind] = np.asarray(cdf_file[key][...]) + 730120.
                    else:
                        for elem in cdf_file[key][...]:
                            row = LineStruct()
                            # correcting matlab day (relative to 1.1.2000) to python day (1.1.1)
                            if type(elem) in [float,np.float64]:
                                row.time = 730120. + elem
                            else:
                                row.time = date2num(elem)
                            stream.add(row)
                            del row
                #del ti
            elif key == 'HNvar' or key == 'x':
                x = cdf_file[key][...]
                if len(x) == 1:
                    # This is the case if identical data is found
                    try:
                        length = len(cdf_file['Epoch'][...])         
                    except:
                        length = len(cdf_file['time'][...])         
                    x = [x[0]] * length
                if len(x) > 0:
                    if not oldtype:
                        ind = KEYLIST.index('x')
                        array[ind] = np.asarray(x)
                    else:
                        stream._put_column(x,'x')
                    del x
                    #if not headskip:
                    stream.header['col-x'] = 'x'
                    try:
                        stream.header['col-x'] = cdf_file['x'].attrs['name']
                    except:
                        pass
                    try:
                        stream.header['unit-col-x'] = cdf_file['x'].attrs['units']
                    except:
                        # Apply default unit:
                        stream.header['unit-col-x'] = 'nT'
                        pass
            elif key == 'HEvar' or key == 'y':
                y = cdf_file[key][...]
                if len(y) == 1:
                    # This is the case if identical data is found
                    try:
                        length = len(cdf_file['Epoch'][...])         
                    except:
                        length = len(cdf_file['time'][...])         
                    y = [y[0]] * length
                if len(y) > 0:
                    if not oldtype:
                        ind = KEYLIST.index('y')
                        array[ind] = np.asarray(y)
                    else:
                        stream._put_column(y,'y')
                    del y
                    try:
                        stream.header['col-y'] = cdf_file['y'].attrs['name']
                    except:
                        stream.header['col-y'] = 'y'
                    try:
                        stream.header['unit-col-y'] = cdf_file['y'].attrs['units']
                    except:
                        # Apply default unit:
                        stream.header['unit-col-y'] = 'nT'
                        pass
            elif key == 'Zvar' or key == 'z':
                z = cdf_file[key][...]
                if len(z) == 1:
                    # This is the case if identical data is found
                    try:
                        length = len(cdf_file['Epoch'][...])         
                    except:
                        length = len(cdf_file['time'][...])         
                    z = [z[0]] * length
                if len(z) > 0:
                    if not oldtype:
                        ind = KEYLIST.index('z')
                        array[ind] = np.asarray(z)
                    else:
                        stream._put_column(z,'z')
                    del z
                    try:
                        stream.header['col-z'] = cdf_file['z'].attrs['name']
                    except:
                        stream.header['col-z'] = 'z'
                    try:
                        stream.header['unit-col-z'] = cdf_file['z'].attrs['units']
                    except:
                        # Apply default unit:
                        stream.header['unit-col-z'] = 'nT'
                        pass
            elif key == 'Fsc' or key == 'f':
                f = cdf_file[key][...]
                if len(f) == 1:
                    # This is the case if identical data is found
                    try:
                        length = len(cdf_file['Epoch'][...])         
                    except:
                        length = len(cdf_file['time'][...])         
                    f = [f[0]] * length
                if len(f) > 0:
                    if not oldtype:
                        ind = KEYLIST.index('f')
                        array[ind] = np.asarray(f)
                    else:
                        stream._put_column(f,'f')
                    del f
                    try:
                        stream.header['col-f'] = cdf_file['f'].attrs['name']
                    except:
                        stream.header['col-f'] = 'f'
                    try:
                        stream.header['unit-col-f'] = cdf_file['f'].attrs['units']
                    except:
                        # Apply default unit:
                        stream.header['unit-col-f'] = 'nT'
                        pass
            elif key.endswith('scv'): # solely found in juergs files - now define magpy header info
                try:
                    # Please note: using only the last value to identify scalevalue 
                    # - a change of scale values should leed to a different cdf archive !!
                    stream.header['DataScaleX'] = cdf_file['HNscv'][...][-1]
                    stream.header['DataScaleY'] = cdf_file['HEscv'][...][-1]
                    stream.header['DataScaleZ'] = cdf_file['Zscv'][...][-1]
                    stream.header['DataSensorOrientation'] = 'hdz'
                except:
                    # print "error while interpreting header"
                    pass
            elif key in h0_mfi_KEYDICT and OMNIACE: # MAG DATA (H0)
                data = cdf_file[key][...]
                flag = cdf_file['Q_FLAG'][...]
                #for i in range(0,len(data)):
                #    f = flag[i]
                #    if f != 0:
                #        data[i] = float('nan')
                if key == 'BGSM':  
                    skey_x = h0_mfi_KEYDICT[key][0]
                    skey_y = h0_mfi_KEYDICT[key][1]
                    skey_z = h0_mfi_KEYDICT[key][2]
                    splitdata = np.hsplit(data, 3)
                    stream._put_column(splitdata[0],skey_x)
                    stream.header['col-'+skey_x] = 'Bx'
                    stream.header['unit-col-'+skey_x] = 'nT'
                    stream._put_column(splitdata[1],skey_y)
                    stream.header['col-'+skey_y] = 'By'
                    stream.header['unit-col-'+skey_y] = 'nT'
                    stream._put_column(splitdata[2],skey_z)
                    stream.header['col-'+skey_z] = 'Bz'
                    stream.header['unit-col-'+skey_z] = 'nT'
                elif key == 'Magnitude':
                    skey = h0_mfi_KEYDICT[key]
                    stream.header['col-'+skey] = 'Bt'
                    stream.header['unit-col-'+skey] = cdf_file[key].attrs['UNITS']
                    stream._put_column(data,skey)
            elif key in h1_epm_KEYDICT and OMNIACE: # EPAM DATA (H1)
                data = cdf_file[key][...]
                badval = cdf_file[key].attrs['FILLVAL']
                for i in range(0,len(data)):
                    d = data[i]
                    if d == badval:
                        data[i] = float('nan')
                skey = h1_epm_KEYDICT[key]
                stream.header['col-'+skey] = cdf_file[key].attrs['LABLAXIS']
                stream.header['unit-col-'+skey] = cdf_file[key].attrs['UNITS']
                stream._put_column(data,skey)
            elif key in k0_epm_KEYDICT and OMNIACE: # EPAM DATA (K0)
                data = cdf_file[key][...]
                badval = cdf_file[key].attrs['FILLVAL']
                for i in range(0,len(data)):
                    d = data[i]
                    if d == badval:
                        data[i] = float('nan')
                skey = k0_epm_KEYDICT[key]
                stream.header['col-'+skey] = cdf_file[key].attrs['LABLAXIS']
                stream.header['unit-col-'+skey] = cdf_file[key].attrs['UNITS']
                stream._put_column(data,skey)
            elif key in h0_swe_KEYDICT and OMNIACE: # SWEPAM DATA
                data = cdf_file[key][...]
                badval = cdf_file[key].attrs['FILLVAL']
                for i in range(0,len(data)):
                    d = data[i]
                    if d == badval:
                        data[i] = float('nan')
                skey = h0_swe_KEYDICT[key]
                stream.header['col-'+skey] = cdf_file[key].attrs['LABLAXIS']
                stream.header['unit-col-'+skey] = cdf_file[key].attrs['UNITS']
                stream._put_column(data,skey)
            else:
                if key.lower() in KEYLIST:
                    arkey = cdf_file[key][...]
                    if len(arkey) == 1:
                        # This is the case if identical data is found
                        try:
                            length = len(cdf_file['Epoch'][...])         
                        except:
                            length = len(cdf_file['time'][...])         
                        arkey = [arkey[0]] * length
                    if len(arkey) > 0:
                        if not oldtype:
                            ind = KEYLIST.index(key.lower())
                            array[ind] = np.asarray(arkey).astype(object)
                        else:
                            stream._put_column(arkey,key.lower())
                        stream.header['col-'+key.lower()] = key.lower()
                        try:
                            stream.header['unit-col-'+key.lower()] = cdf_file[key.lower()].attrs['units']
                        except:
                            # eventually apply default deg C for temperatures if not provided in header
                            if key.lower() in ['t1','t2']:
                                stream.header['unit-col-'+key.lower()] = "*C"
                            pass
                        try:
                            stream.header['col-'+key.lower()] = cdf_file[key.lower()].attrs['name']
                        except:
                            pass

        cdf_file.close()
        del cdf_file

    if not oldtype:
        return DataStream([LineStruct()], stream.header,np.asarray(array))   
    else:
        return DataStream(stream, stream.header,stream.ndarray)   

def readPYBIN(filename, headonly=False, **kwargs):
    """
    Read binary format of the MagPy package
    Binary formatted data consists of an ascii header line and a binary body containing data
    The header line contains the following space separated inputs:
        1. Format specification: preset to 'MagPyBin' -> used to identify file type in MagPy
        2. SensorID: required 
        3. MagPy-Keys: list defining the related magpy keys under which data is stored e.g. ['x','y','z','t1','var5'] - check KEYLIST for available keys  
        4. ListSpecification: list defining the variables stored under the keys e.g. ['H','D','Z','DewPoint','Kp']  
        5. UnitSpecification: list defining units e.g. ['nT','deg','nT','deg C','']
        6. Multiplier: list defining multipiers used before packing of columns - value divided by multipl. returns correct units in 5 e.g. [100,100,100,1000,1]
        7. Packingcode: defined by pythons struct.pack always starts with 6hL e.g. 6hLLLLLL
        8. Packingsize: size of packing code
        9. Special format specification - optional
            in this case ... (important for high frequency records)
            to be written
        Important: lists 3,4,5,6 must be of identical length
    The data section is packed accoring to the packing code using struct.pack
    """
    keylist = kwargs.get('keylist') # required for very old format, does not affect other formats
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    oldtype = kwargs.get('oldtype')

    getfile = True

    stream = DataStream([],{},[[] for key in KEYLIST])

    theday = extractDateFromString(filename)
    try:
        if starttime:
            if not theday >= datetime.date(stream._testtime(starttime)):
                getfile = False
        if endtime:
            if not theday <= datetime.date(stream._testtime(endtime)):
                getfile = False
    except:
        # Date format not recognized. Need to read all files
        getfile = True 
    logbaddata = False

    if getfile:
        loggerlib.info("read: %s Format: PYCDF" % filename)
        fh = open(filename, 'rb')
        # read header line and extract packing format
        header = fh.readline()
        # some cleaning actions for false header inputs
        header = header.replace(', ',',')
        header = header.replace('deg C','deg')
        h_elem = header.strip().split()
        if not h_elem[1] == 'MagPyBin':
            print 'readPYBIN: No MagPyBin format - aborting'
            return
        #print "Length ", len(h_elem), h_elem[2]

        #Test whether element 3,4,5 (and 6) are lists of equal length 
        if len(h_elem) == 8:
            #print "Very old import format"
            nospecial = True
            try:
                if not keylist:
                    loggerlib.error('readPYBIN: keylist of length(elemlist) needs to be specified')
                    return stream
                elemlist = h_elem[3].strip('[').strip(']').split(',')
                unitlist = h_elem[4].strip('[').strip(']').split(',')
                multilist = map(float,h_elem[5].strip('[').strip(']').split(','))
            except:
                print "readPYBIN: Could not extract lists from header - check format - aborting..."
                return stream
            if not len(keylist) == len(elemlist) or not len(keylist) == len(unitlist) or not  len(keylist) == len(multilist):
                loggerlib.error("readPYBIN: Provided lists from header of differenet lengths - check format - aborting...")
                return stream
        elif len(h_elem) == 9:
            #print "The current format"
            nospecial = True
            try:
                keylist = h_elem[3].strip('[').strip(']').split(',')
                elemlist = h_elem[4].strip('[').strip(']').split(',')
                unitlist = h_elem[5].strip('[').strip(']').split(',')
                multilist = map(float,h_elem[6].strip('[').strip(']').split(','))
            except:
                loggerlib.error("readPYBIN: Could not extract lists from header - check format - aborting...")
                return stream
            if not len(keylist) == len(elemlist) or not len(keylist) == len(unitlist) or not  len(keylist) == len(multilist):
                loggerlib.error("readPYBIN: Provided lists from header of differenet lengths - check format - aborting...")
                return stream
        elif len(h_elem) == 10:
            #print "Special format"
	    loggerlib.debug("readPYBIN: Special format detected. May not be able to read file.")
            nospecial = False
	    if h_elem[2][:5] == 'ENV05' or h_elem[2] == 'Env05':
                keylist = h_elem[3].strip('[').strip(']').split(',')
                elemlist = h_elem[4].strip('[').strip(']').split(',')
                unitlist = h_elem[5].strip('[').strip(']').split(',')
                multilist = map(float,h_elem[7].strip('[').strip(']').split(','))
                nospecial = True
        else:
            loggerlib.error('readPYBIN: No valid MagPyBin format, inadequate header length - aborting')
            return stream
            
        packstr = '<'+h_elem[-2]+'B'
        lengthcode = struct.calcsize(packstr)
        lengthgiven = int(h_elem[-1])+1
        length = lengthgiven
        if not lengthcode == lengthgiven:
            loggerlib.debug("readPYBIN: Check your packing code!")
            if lengthcode < lengthgiven:
                missings = lengthgiven-lengthcode
                for i in range(missings):
                    packstr += 'B'
                    length = lengthgiven
            else:
                length = lengthcode

        line = fh.read(length)
        stream.header['SensorID'] = h_elem[2]
        stream.header['SensorElements'] = ','.join(elemlist)
        stream.header['SensorKeys'] = ','.join(keylist)
        lenel = len([el for el in elemlist if el in KEYLIST]) # If elemlist and Keylist are disorderd
        lenke = len([el for el in keylist if el in KEYLIST])
        if lenel > lenke:
            keylist = elemlist

        array = [[] for key in KEYLIST]
        if nospecial:
            for idx, elem in enumerate(keylist):
                stream.header['col-'+elem] = elemlist[idx]
                stream.header['unit-col-'+elem] = unitlist[idx]
                # Header info
                pass
            while not line == "":
                try:
                    data= struct.unpack(packstr, line)
                except:
                    print "readPYBIN: struct error", filename, packstr, struct.calcsize(packstr)
                try:                    
                    time = datetime(data[0],data[1],data[2],data[3],data[4],data[5],data[6])
                    if not oldtype:
                        array[0].append(date2num(stream._testtime(time)))
                        # check elemlist and keylist
                        for idx, elem in enumerate(keylist):
                            try:
                                index = KEYLIST.index(elem)
                                if not elem.endswith('time'):
                                    array[index].append(data[idx+7]/float(multilist[idx]))
                                else:
                                    try:
                                        sectime = datetime(data[idx+7],data[idx+8],data[idx+9],data[idx+10],data[idx+11],data[idx+12],data[idx+13])
                                        array[index].append(date2num(stream._testtime(sectime)))
                                    except:
                                        pass
                            except:
                                if elem.endswith('time'):
                                    try:
                                        sectime = datetime(data[idx+7],data[idx+8],data[idx+9],data[idx+10],data[idx+11],data[idx+12],data[idx+13])
                                        index = KEYLIST.index('sectime')
                                        array[index].append(date2num(stream._testtime(sectime)))
                                    except:
                                        pass
                    else:
                        row = LineStruct()
                        row.time = date2num(stream._testtime(time))
                        for idx, elem in enumerate(keylist):
                            exec('row.'+keylist[idx]+' = data[idx+7]/float(multilist[idx])')
                        stream.add(row)
                    if logbaddata == True:
                        loggerlib.error("readPYBIN: Good data resumes with: %s" % str(data))
                        logbaddata = False
                except:
                    loggerlib.error("readPYBIN: Error in line while reading data file. Last line at: %s" % str(lastdata))
                    logbaddata = True
                lastdata = data
                line = fh.read(length)
        else:
            print "To be done ..."
            pass

        array = np.asarray([np.asarray(el) for el in array])
        stream.ndarray = array
        if len(stream.ndarray[0]) > 0:
            print "readPYBIN: Imported bin as ndarray"
            stream.container = [LineStruct()]
            # if unequal lengths are found, then usually txt and bin files are loaded together

    return stream 


def writePYSTR(datastream, filename, **kwargs):
    """
    Function to write structural ASCII data 
    """

    mode = kwargs.get('mode')
    loggerlib.info("writePYSTR: Writing file to %s" % filename)

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
        else:
            myFile= open( filename, "wb" )
    else:
        myFile= open( filename, "wb" )
    wtr= csv.writer( myFile )
    headdict = datastream.header
    head, line = [],[]
    if not mode == 'append':
        wtr.writerow( [' # MagPy - ASCII'] )
        for key in headdict:
            if not key.find('col') >= 0 and not key == 'DataAbsFunctionObject':
                line = [' # ' + key +':  ' + str(headdict[key]).strip()]
                wtr.writerow( line )
        wtr.writerow( ['# head:'] )
        for key in KEYLIST:
            title = headdict.get('col-'+key,'-') + '[' + headdict.get('unit-col-'+key,'') + ']'
            head.append(title)
        wtr.writerow( head )
        wtr.writerow( ['# data:'] )

    if len(datastream.ndarray[0]) > 0:
        for i in range(len(datastream.ndarray[0])):
            row = []
            for idx,el in enumerate(datastream.ndarray):
                if len(datastream.ndarray[idx]) > 0:
                    if KEYLIST[idx].find('time') >= 0:
                        #print el[i]
                        row.append(datetime.strftime(num2date(float(el[i])).replace(tzinfo=None), "%Y-%m-%dT%H:%M:%S.%f") )
                    else:
                        if not KEYLIST[idx] in NUMKEYLIST: # Get String and replace all non-standard ascii characters
                            try:
                                valid_chars='-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                                el[i] = ''.join([e for e in list(el[i]) if e in list(valid_chars)])  
                            except:
                                pass
                        row.append(el[i])
                else:
                    if KEYLIST[idx] in NUMKEYLIST:
                        row.append(float('nan'))
                    else:
                        row.append('-')
            wtr.writerow(row)
    else:
        for elem in datastream:
            row = []
            for key in KEYLIST:
                if key.find('time') >= 0:
                    try:
                        row.append( datetime.strftime(num2date(eval('elem.'+key)).replace(tzinfo=None), "%Y-%m-%dT%H:%M:%S.%f") )
                    except:
                        row.append( float('nan') )
                        pass
                else:
                    row.append(eval('elem.'+key))
            wtr.writerow( row )
    myFile.close()
    return True


def writePYCDF(datastream, filename, **kwargs):
    # check for nan and - columns
    #for key in KEYLIST:
    #    title = headdict.get('col-'+key,'-') + '[' + headdict.get('unit col-'+key,'') + ']'
    #    head.append(title)

    #print datastream.ndarray, len(datastream.ndarray[0])
    #print "WriteFormat length 0", len(datastream.ndarray[0])
    # Test for file content
    #if not len(datastream) > 0 and not len(datastream.ndarray)

    if not len(datastream.ndarray[0]) > 0 and not len(datastream) > 0:
        return False

    mode = kwargs.get('mode')

    if os.path.isfile(filename+'.cdf'):
        if mode == 'skip': # skip existing inputs
            exst = read(path_or_url=filename+'.cdf')
            datastream = joinStreams(exst,datastream,extend=True)
            os.remove(filename+'.cdf')
            mycdf = cdf.CDF(filename, '')
        elif mode == 'replace': # replace existing inputs
            #print filename
            exst = read(path_or_url=filename+'.cdf')
            datastream = joinStreams(datastream,exst,extend=True)
            os.remove(filename+'.cdf')
            mycdf = cdf.CDF(filename, '')
        elif mode == 'append':
            mycdf = cdf.CDF(filename, filename) # append????
        else: # overwrite mode
            #print filename
            os.remove(filename+'.cdf')
            mycdf = cdf.CDF(filename, '')
    else:
        mycdf = cdf.CDF(filename, '')

    keylst = datastream._get_key_headers()
    #print "writeCDF", keylst
    if not 'flag' in keylst:
        keylst.append('flag')
    #print keylst
    if not 'comment' in keylst:
        keylst.append('comment')
    if not 'typ' in keylst:
        keylst.append('typ')
    tmpkeylst = ['time']
    tmpkeylst.extend(keylst)
    keylst = tmpkeylst 

    headdict = datastream.header
    head, line = [],[]

    if not mode == 'append':
        for key in headdict:
            if not key.find('col') >= 0:
                #print key, headdict[key]
                if not key == 'DataAbsFunctionObject':
                    mycdf.attrs[key] = headdict[key]
                else:
                    print "Found DataAbsFunctionObject - pickle and dump "
                    pfunc = pickle.dumps(headdict[key])
                    mycdf.attrs[key] = pfunc
                 
    mycdf.attrs['DataFormat'] = 'MagPyCDF'

    #def checkEqualIvo(lst):
    #    # http://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
    #    return not lst or lst.count(lst[0]) == len(lst)
    def checkEqual3(lst):
        return lst[1:] == lst[:-1]

    ndtype = False
    try:
        if len(datastream.ndarray[0]) > 0:
            ndtype = True
    except:
        pass

    #print "writing keys", keylst
    #print "WriteFormat length 1", len(datastream.ndarray[0])
    for key in keylst:
        if ndtype:
            ind = KEYLIST.index(key)
            col = datastream.ndarray[ind]
            if not key in NUMKEYLIST:
                if not key == 'time':
                    #print "converting"
                    col = np.asarray(col)
        else:
            col = datastream._get_column(key)

        # Sort out columns only containing nan's
        try:
            test = [elem for elem in col if not isnan(elem)]
            if not len(test) > 0:
                col = np.asarray([])
        except:
            pass
        if not False in checkEqual3(col) and len(col) > 0:
            print "Found identical values only: %s" % key
            col = col[:1]
            #if not col[0] in ['nan', float('nan'),NaN,'-',None,'']: #remove place holders 
            #- better not!!! 2015-10-14 --- if two files are loaded, one with flags, one without, then column lengths will not fit 
            #    col = col[:1]
            #else:
            #    col = np.asarray([])
        if key.find('time') >= 0:
            if key == 'time':
                key = 'Epoch'
                #col = col.astype
                mycdf[key] = np.asarray([num2date(elem).replace(tzinfo=None) for elem in col.astype(float)])
                #print "Last time saved", col[-1]
            elif key == 'sectime':
                mycdf[key] = np.asarray([num2date(elem).replace(tzinfo=None) for elem in col.astype(float)])
        elif len(col) > 0:
            #print "writing", np.asarray(col)
            if not key in NUMKEYLIST:
                col = list(col)
                col = ['' if el is None else el for el in col]
                col = np.asarray(col) # to get string conversion
            else:
                #print col, key
                col = np.asarray([float(nan) if el is None else el for el in col])
                col = col.astype(float)
            mycdf[key] = col

            for keydic in headdict:
                if keydic == ('col-'+key):
                    try:
                        mycdf[key].attrs['name'] = headdict.get('col-'+key,'')
                    except:
                        pass
                if keydic == ('unit-col-'+key):
                    try:
                        mycdf[key].attrs['units'] = headdict.get('unit-col-'+key,'')
                    except:
                        pass
                    
    mycdf.close()
    return True


def writePYASCII(datastream, filename, **kwargs):
    """
    Function to write basic ASCII data 
    """

    mode = kwargs.get('mode')
    loggerlib.info("writePYASCII: Writing file to %s" % filename)

    if os.path.isfile(filename):
        if mode == 'skip': # skip existing inputs
            exst = read(path_or_url=filename)
            datastream = joinStreams(exst,datastream,extend=True)
            myFile= open( filename, "wb" )
        elif mode == 'replace': # replace existing inputs
            print "write ascii filename", filename
            exst = read(path_or_url=filename)
            datastream = joinStreams(datastream,exst,extend=True)
            myFile= open( filename, "wb" )
        elif mode == 'append':
            myFile= open( filename, "ab" )
        else:
            myFile= open( filename, "wb" )
    else:
        myFile= open( filename, "wb" )
    wtr= csv.writer( myFile )
    headdict = datastream.header
    head, line = [],[]

    keylst = datastream._get_key_headers()
    keylst[:0] = ['time']

    if not mode == 'append':
        for key in keylst:
            title = headdict.get('col-'+key,'-') + '[' + headdict.get('unit-col-'+key,'') + ']'
            head.append(title)
        head[0] = 'Time'
        headnew = ['Time-days']
        headnew.extend(head)
        head = headnew
        wtr.writerow( [' # MagPy ASCII'] )
        wtr.writerow( head )
    if len(datastream.ndarray[0]) > 0:
        for i in range(len(datastream.ndarray[0])):
            row = []
            for idx,el in enumerate(datastream.ndarray):
                if len(datastream.ndarray[idx]) > 0:
                    if KEYLIST[idx].find('time') >= 0:
                        #print el[i]
                        row.append(float(el[i]))
                        row.append(datetime.strftime(num2date(float(el[i])).replace(tzinfo=None), "%Y-%m-%dT%H:%M:%S.%f") )
                    else:
                        if not KEYLIST[idx] in NUMKEYLIST: # Get String and replace all non-standard ascii characters
                            try:
                                valid_chars='-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                                el[i] = ''.join([e for e in list(el[i]) if e in list(valid_chars)])  
                            except:
                                pass
                        row.append(el[i])
            wtr.writerow(row)
    else:
        for elem in datastream:
            row = []
            for key in keylst:
                if key.find('time') >= 0:
                    row.append(elem.time)
                    try:
                        row.append( datetime.strftime(num2date(eval('elem.'+key)).replace(tzinfo=None), "%Y-%m-%dT%H:%M:%S.%f") )
                    except:
                        row.append( float('nan') )
                        pass
                else:
                    row.append(eval('elem.'+key))
            wtr.writerow( row )
    myFile.close()
    return True

