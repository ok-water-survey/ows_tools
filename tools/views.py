import json
import os
import urllib2
import urllib

import cherrypy


#import urllib
#import pickle
#from celery.result import AsyncResult
#from celery.execute import send_task
#from celery.task.control import inspect
from json_handler import handler
from pymongo import Connection
#from datetime import datetime
from Cheetah.Template import Template
from sets import Set
from datetime import datetime
from urllib2 import urlopen
from csv import DictReader

templatepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))


def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)

        return wrapper

    return decorate


class Root(object):
    def __init__(self, mongoHost='localhost', port=27017, database='ows',
                 ws_url='http://waterservices.usgs.gov/nwis/site/?format=rdb&sites=%s&seriesCatalogOutput=true'):
        sources = urlopen("http://data.oklahomawatersurvey.org/catalog/db_find/ows-portal/data/%7B'spec':%7B'model':'Source'%7D,'fields':['hassubs','value','parent','sub'],'sort':[('order',1)]%7D/")
        temp = {}
        data = json.load(sources)
        #print data
        for src in data:
            if src['sub']:
                temp[src['value']] = src['parent']
            else:
                temp[src['value']] = src['value']
        #print temp
        self.source = temp
        self.db = Connection(mongoHost, port)
        self.database = database
        self.ws_url = ws_url
        #self.collection = collection

    @cherrypy.expose
    def index(self):
        return 'Create list of tools available - To do list!!'

    @cherrypy.expose
    @mimetype('application/json')
    def cropland(self, huc, callback=None, **kwargs):
        lookup = []
        data = []
        for row in self.db.ows.cropdata_lookup.find():
            lookup.append(row)
        total_acre = 0.0
        for row in self.db.ows.cropdata.find({'HUC': int(huc)}).sort('cdl_acres', -1):
            total_acre = float(row["cdl_acres"]) + total_acre
            data.append(row)
        for row in data:
            row['percent_watershed'] = float(row["cdl_acres"]) / total_acre * 100
            for lu in lookup:
                if lu['cdl_code'] == row['cdl_class']:
                    row['crop'] = lu['crop']
                    break

        serialized = json.dumps(data, default=handler, sort_keys=True, indent=4)
        if callback is not None:
            return str(callback) + '(' + serialized + ')'
        else:
            return serialized

    def get_wqp_metadata(self, site):

        url = "http://www.waterqualitydata.us/Result/search?siteid=%s&countrycode=US&mimeType=csv" % (site)
        datafile = urlopen(url)
        data = []
        for row in DictReader(datafile):
            data.append(row)
        metadata = {}
        for itm in data:
            if itm['CharacteristicName'] not in metadata:
                metadata[itm['CharacteristicName']] = {
                    'ResultMeasure/MeasureUnitCode': itm['ResultMeasure/MeasureUnitCode'],
                    'MinActivityStartDate': itm['ActivityStartDate'],
                    #'MinActivityStartTime':itm['ActivityStartTime/Time'],
                    'MaxActivityStartDate': itm['ActivityStartDate'],
                    #'MaxActivityStartTime':itm['ActivityStartTime/Time'],
                    'USGSPCode': itm['USGSPCode'],
                    'samplecount': 1}
            else:
                if metadata[itm['CharacteristicName']]['MinActivityStartDate'] > itm['ActivityStartDate']:
                    metadata[itm['CharacteristicName']]['MinActivityStartDate'] = itm['ActivityStartDate']
                if metadata[itm['CharacteristicName']]['MaxActivityStartDate'] < itm['ActivityStartDate']:
                    metadata[itm['CharacteristicName']]['MaxActivityStartDate'] = itm['ActivityStartDate']
                metadata[itm['CharacteristicName']]['samplecount'] = metadata[itm['CharacteristicName']][
                                                                         'samplecount'] + 1
        return metadata


    @cherrypy.expose
    @mimetype('text/html')
    def usgs_metadata(self, site, source=None, type=None, **kwargs):
        """ Return Data Available for individual USGS SItes.
            site -  string site number
            type - optional - default html page, json for json data feed.
        """
        isource = self.source[source]
        if type == 'json':
            return json.dumps(self.get_metadata_site(site), sort_keys=True, indent=4)
        elif isource == 'OWRBMW':
            now = datetime.now()
            month = now.strftime("%m")
            year = now.strftime("%Y")
            day = now.strftime("%d")
            row = self.db.ows.owrb_monitor_sites.find_one({'WELL_ID': site})
            nameSpace = dict(groups=[], available=row, site=row['name'],
                             location=row['LATITUDE'] + ', ' + row['LONGITUDE'], day=day, year=year, month=month)
            t = Template(file=templatepath + '/available_data_owrbmw.tmpl', searchList=[nameSpace])
            return t.respond()
        elif isource == 'OWRBMWW':
            now = datetime.now()
            month = now.strftime("%m")
            year = now.strftime("%Y")
            day = now.strftime("%d")
            #print site
            row = self.db.ows.owrb_water_sites.find_one({'WELL_ID': int(site)})
            #print row
            nameSpace = dict(groups=[], available=row, site="OWRB Monitor Well Site: %d" % row['WELL_ID'],
                             location=str(row['LATITUDE']) + ', ' + str(row['LONGITUDE']), day=day, year=year, month=month)
            t = Template(file=templatepath + '/available_data_owrbmww.tmpl', searchList=[nameSpace])
            return t.respond()
        elif isource == 'MESONET':
            row = self.db.ows.mesonet_site.find_one({'stid': site})
            output = []
            nameSpace = dict(groups=[], available=row, site=row['name'], location=row['nlat'] + ', ' + row['elon'])
            t = Template(file=templatepath + '/available_data_meso.tmpl', searchList=[nameSpace])
            return t.respond()
        elif isource == 'OWRB_LOG':
            row = self.db.ows.owrb_well_logs.find_one({'WELL_ID': site})
            nameSpace = dict(groups=[], available=row, site=row['name'],
                             location=(str(row['LATITUDE']) + ', ' + str(row['LONGITUDE'])))
            t = Template(file=templatepath + '/available_data_owrb.tmpl', searchList=[nameSpace])
            return t.respond()
        elif isource == 'WQP':
            row = self.db.ows.water_quality_sites.find_one({'MonitoringLocationIdentifier': site})
            row['parameters'] = self.get_wqp_metadata(site)
            nameSpace = dict(groups=[], available=row, site=row['MonitoringLocationIdentifier'],
                             location=str(row['LatitudeMeasure']) + ', ' + str(row['LongitudeMeasure']))
            t = Template(file=templatepath + '/available_data_wqp.tmpl', searchList=[nameSpace])
            return t.respond()
        elif isource == "OCC":
	    row = self.db.ows.occ_site.find_one({'Location_id':site})
	    nameSpace = dict(groups=[], available=row,site=row['Location_id'],
			     location=str(row['Lat']) + ', ' + str(row['Long']))
	    t = Template(file=templatepath + '/available_data_occ.tmpl', searchList=[nameSpace]) 
	    return t.respond()
	else:
            output = self.get_metadata_site(site)
            if len(output) == 0:
                nameSpace = dict(groups=[], available=output, site='No Data Available', location='Site Number: ' + site)
            else:
                nameSpace = dict(groups=self.set_groups(output), available=output, site=output[0]['station_nm'],
                                 location=output[0]['dec_lat_va'] + ', ' + output[0]['dec_long_va'])
            t = Template(file=templatepath + '/available_data.tmpl', searchList=[nameSpace])
            return t.respond()


    def set_groups(self, data):
        wservice = Set()
        for i in data:
            wservice.add(i['data_type_cd'])
        out = []
        durl = 'http://waterdata.usgs.gov/nwis/inventory?agency_code=USGS&site_no=%s' % (data[0]['site_no'])
        if 'iv' in wservice:
            url = 'http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'iv', 'name': 'Current - Instantaneous values', 'webdata': url})
            wservice.remove('iv')
        if 'uv' in wservice:
            url = 'http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'uv', 'name': 'Current - Instantaneous values (Unit value)', 'webdata': url})
            wservice.remove('uv')
        if 'rt' in wservice:
            url = 'http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'rt', 'name': 'Current - Instantaneous values (Real-Time)', 'webdata': url})
            wservice.remove('rt')
        if 'dv' in wservice:
            url = 'http://waterdata.usgs.gov/nwis/dv?referred_module=sw&site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'dv', 'name': 'Daily Data', 'webdata': url})
            wservice.remove('dv')
        if 'pk' in wservice:
            url = 'http://nwis.waterdata.usgs.gov/usa/nwis/peak/?site_no=%s' % (data[0]['site_no'])
            if data[0]['site_tp_cd'] == 'ST':
                out.append({'code': 'pk', 'name': 'Peak streamflow', 'webdata': url})
            else:
                out.append({'code': 'pk', 'name': 'Peak water levels', 'webdata': url})
            wservice.remove('pk')
        if 'sv' in wservice:
            url = 'http://waterdata.usgs.gov/nwis/measurements/?site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'sv', 'name': 'Field measurements', 'webdata': url})
            wservice.remove('sv')
        if 'gw' in wservice:
            url = 'http://nwis.waterdata.usgs.gov/usa/nwis/gwlevels/?site_no=%s' % (data[0]['site_no'])
            out.append(
                {'code': 'gw', 'name': 'Groundwater levels measured at irregular, discrete intervals', 'webdata': url})
            wservice.remove('gw')
        if 'qw' in wservice:
            url = 'http://nwis.waterdata.usgs.gov/usa/nwis/qwdata/?site_no=%s' % (data[0]['site_no'])
            out.append({'code': 'qw', 'name': 'Field/Lab water-quality samples', 'webdata': url})
            wservice.remove('qw')
        if 'id' in wservice:
            url = 'http://ida.water.usgs.gov/ida/available_records.cfm?sn=%s' % (data[0]['site_no'])
            #out.append({'code':'id','name':'Instantaneous-Data Archive','webdata':url})
            wservice.remove('id')
        if 'aw' in wservice:
            url = 'http://groundwaterwatch.usgs.gov/AWLSites.asp?S=%s' % (data[0]['site_no'])
            out.append({'code': 'aw', 'name': 'USGS Active Groundwater Level Network', 'webdata': url})
            wservice.remove('aw')
        if 'ad' in wservice:
            for row in data:
                if row['data_type_cd'] == 'ad':
                    bd = int(row['begin_date'])
                    ct = int(row['count_nu'])
                    break
            temp = {}
            temp_encode = {}
            yrs = []
            for year in range(bd, bd + ct):
                url = 'http://wdr.water.usgs.gov/wy%d/pdfs/%s.%d.pdf' % (year, data[0]['site_no'], year)
                temp[year] = url  #
                temp_encode[year] = urllib.quote(url, '')
                yrs.append(year)
            out.append(
                {'code': 'ad', 'name': 'Annual Water-Data Report (pdf)', 'webdata': temp, 'webdata_encode': temp_encode,
                 'years': yrs})
            wservice.remove('ad')
        for remain in wservice:
            out.append({'code': remain, 'name': remain, 'webdata': durl})
        return out

    def get_metadata_site(self, site):
        url = self.ws_url % (site)
        f1 = urllib2.urlopen(url)
        temp = '#'
        head = ''
        output = []
        while (temp[0] == "#"):
            temp = f1.readline()
            if temp[0] != '#':
                head = temp.strip('\r\n').split('\t')
        f1.readline()
        for row in f1:
            temp = row.strip('\r\n').split('\t')
            data = dict(zip(head, temp))
            try:
                param = self.db[self.database]['parameters'].find_one({'parameter_cd': data['parm_cd']})
                data['parameter'] = {'group_name': param['parameter_group_nm'], 'name': param['parameter_nm'],
                                     'units': param['parameter_units']}
            except:
                data['parameter'] = {'group_name': '', 'name': '', 'units': ''}
            if data['data_type_cd'] == 'ad':
                data['parameter'] = {'group_name': '', 'name': 'USGS Annual Water Data Reports', 'units': ''}
            if data['data_type_cd'] == 'id':
                data['parameter'] = {'group_name': '', 'name': 'Historical instantaneous values', 'units': ''}
            if data['data_type_cd'] == 'pk':
                data['parameter'] = {'group_name': '', 'name': 'Peak measurements of water levels and streamflow',
                                     'units': ''}

            output.append(data)
        return output


cherrypy.tree.mount(Root())
application = cherrypy.tree
if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()

