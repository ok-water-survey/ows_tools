import cherrypy,urllib2,json

def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate

class Root(object):
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/data/proxy/")
    @cherrypy.expose
    @mimetype('text/html')
    def proxy(self,url=None,callback=None,**kwargs):
        if url:
            try:
                res= json.loads(urllib2.urlopen(url).read())
                serialized = json.dumps(res,indent=4)
                if callback is not None:
                    return str(callback) + '(' + serialized + ')'
                else:
                    return serialized
            except Exception as inst:
                raise inst
        else:
            return 'Data Proxy requires URL parameter. Please provide URL.'
cherrypy.tree.mount(Root())
application = cherrypy.tree
if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()

