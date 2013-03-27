import cherrypy
import json, os,urllib2 #, math,commands 
#import urllib
#import pickle
#from celery.result import AsyncResult
#from celery.execute import send_task
#from celery.task.control import inspect
from pymongo import Connection
from datetime import datetime
from Cheetah.Template import Template
from sets import Set
templatepath= os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate

class Root(object):
    def __init__(self,mongoHost='localhost',port=27017,database='ows',ws_url='http://waterservices.usgs.gov/nwis/site/?format=rdb&sites=%s&seriesCatalogOutput=true'):
        self.db = Connection(mongoHost,port)
        self.database = database
        self.ws_url=ws_url
        #self.collection = collection
    @cherrypy.expose
    def index(self):
        return 'Create list of tools available - To do list!!'
    @cherrypy.expose
    @mimetype('text/html')
    def usgs_metadata(self,site,type=None, **kwargs):
        ''' Return Data Available for individual USGS SItes.
            site -  string site number
            type - optional - default html page, json for json data feed.
        ''' 
        if type == 'json':
            return json.dumps(self.get_metadata_site(site),sort_keys=True,indent=4)
        else:
            output=self.get_metadata_site(site)
            if len(output)==0:
                nameSpace = dict(groups=[],available=output,site='No Data Available',location='Site Number: ' + site)
            else:
                nameSpace = dict(groups=self.set_groups(output),available=output,site=output[0]['station_nm'],location=output[0]['dec_lat_va'] + ', ' +  output[0]['dec_long_va'])
            t = Template(file = templatepath + '/available_data.tmpl', searchList=[nameSpace])
            return t.respond()
    def set_groups(self,data):
        wservice = Set()
        for i in data:
            wservice.add(i['data_type_cd'])
        out=[]
        durl='http://waterdata.usgs.gov/nwis/inventory?agency_code=USGS&site_no=%s' % (data[0]['site_no'])
        if 'iv'in wservice:
            url='http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'iv','name':'Current - Instantaneous values','webdata':url})
            wservice.remove('iv')
        if 'uv' in wservice:
            url='http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'uv','name':'Current - Instantaneous values (Unit value)','webdata':url})
            wservice.remove('uv')
        if 'rt' in wservice:
            url='http://waterdata.usgs.gov/nwis/uv?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'rt','name':'Current - Instantaneous values (Real-Time)','webdata':url})
            wservice.remove('rt')
        if 'dv' in wservice:
            url='http://waterdata.usgs.gov/nwis/dv?referred_module=sw&site_no=%s' % (data[0]['site_no'])
            out.append({'code':'dv','name':'Daily Data','webdata':url})
            wservice.remove('dv')
        if 'pk' in wservice:
            url='http://nwis.waterdata.usgs.gov/usa/nwis/peak/?site_no=%s' % (data[0]['site_no'])
            if data[0]['site_tp_cd']=='ST':
                out.append({'code':'pk','name':'Peak streamflow','webdata':url})
            else:
                out.append({'code':'pk','name':'Peak water levels','webdata':url})
            wservice.remove('pk')
        if 'sv' in wservice:
            url='http://waterdata.usgs.gov/nwis/measurements/?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'sv','name':'Field measurements','webdata':url})
            wservice.remove('sv')
        if 'gw' in wservice:
            url='http://nwis.waterdata.usgs.gov/usa/nwis/gwlevels/?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'gw','name':'Groundwater levels measured at irregular, discrete intervals','webdata':url})
            wservice.remove('gw')
        if 'qw' in wservice:
            url='http://nwis.waterdata.usgs.gov/usa/nwis/qwdata/?site_no=%s' % (data[0]['site_no'])
            out.append({'code':'qw','name':'Field/Lab water-quality samples','webdata':url})
            wservice.remove('qw')
        if 'id' in wservice:
            url='http://ida.water.usgs.gov/ida/available_records.cfm?sn=%s' % (data[0]['site_no'])
            out.append({'code':'id','name':'Instantaneous-Data Archive','webdata':url})
            wservice.remove('id')
        if 'ad' in wservice:
            for row in data:
                if row['data_type_cd'] == 'ad':
                    bd=int(row['begin_date'])
                    ct=int(row['count_nu'])
                    break
            temp={}
            yrs=[]
            for year in range(bd,bd+ct):
                url='http://wdr.water.usgs.gov/wy%d/pdfs/%s.%d.pdf' % (year,data[0]['site_no'],year)
                temp[year]=url
                yrs.append(year)
            out.append({'code':'ad','name':'Annual Water-Data Report (pdf)','webdata':temp,'years':yrs})
            wservice.remove('ad')
        for remain in wservice:
            out.append({'code':remain,'name':remain,'webdata':durl})
        return out
            
    def get_metadata_site(self,site):
        url= self.ws_url % (site)
        f1 = urllib2.urlopen(url)
        temp='#'
        head=''
        output=[]
        while (temp[0]=="#"):
            temp=f1.readline()
            if temp[0]!='#':
                head = temp.strip('\r\n').split('\t')
        f1.readline()
        for row in f1:
            temp=row.strip('\r\n').split('\t')
            data = dict(zip(head,temp))
            try:
                param = self.db[self.database]['parameters'].find_one({'parameter_cd': data['parm_cd']})
                data['parameter']={'group_name':param['parameter_group_nm'],'name':param['parameter_nm'],'units':param['parameter_units']}
            except:
                data['parameter']={'group_name':'','name':'','units':''}
            if data['data_type_cd']=='ad':
                data['parameter']={'group_name':'','name':'USGS Annual Water Data Reports','units':''}
            if data['data_type_cd']=='id':
                data['parameter']={'group_name':'','name':'Historical instantaneous values','units':''}
            if data['data_type_cd']=='pk':
                data['parameter']={'group_name':'','name':'Peak measurements of water levels and streamflow','units':''}
            
            output.append(data)
        return output


cherrypy.tree.mount(Root())
application = cherrypy.tree
if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()
