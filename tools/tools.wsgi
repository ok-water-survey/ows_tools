import os
if os.uname()[1] == 'fire.rccc.ou.edu':
    basedir = '/scratch/www/wsgi_sites/'
else:
    basedir = '/var/www/apps/'

activate_this = basedir + 'tools/virtpy/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import site
site.addsitedir(basedir + 'tools')
import cherrypy
from cherrypy import wsgiserver
from views import Root

    
application = cherrypy.Application(Root(), script_name=None, config = None )

if __name__ == '__main__':
    wsgi_apps = [('/tools', application)]
    server = wsgiserver.CherryPyWSGIServer(('localhost', 8080), wsgi_apps, server_name='localhost')
    try:
        server.start()
    except KeyboardInterrupt():
        server.stop()


