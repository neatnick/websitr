"""
files or directories with a ! in front of them will not be copied into the project
files or directories with a ~ in front of them will not have a route added for them

TODO: should only explicit resource paths be generated?
this would allow for the second condition above for image files and fonts and stuff, 
or you could just change the regex to not match files with ~ in front of them
"""

# arguments:
# - path to put the generated site
# - whether to update non-local site files (i.e. bottle)
# - whether to start webserver
#
# - development flag:
#    + put generated site in tmp
#    + attempt to update non-local files (non-fatal exception if unable to)
#    + start webserver with development flag
#
# - deployment flag:
#    + put generated site in path (required argument for the flag)
#    + update non-local (?)
#    + start webserver with deploy flag


import os, sys, tempfile
import urllib.request
import shutil, argparse


########################################################################################################################
##### Command Line Interface ###########################################################################################
########################################################################################################################

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("-p", "--path", 
    type=str,
    default=tempfile.gettempdir(),
    help="the path to the desired location of the generated site")
args = parser.parse_args()



########################################################################################################################
##### Templates ########################################################################################################
########################################################################################################################

from string import Template

class MyTemplate(Template):
    def populate(self, filename, **kwargs):
        try:
            with open(filename, 'w') as f:
                f.write(self.sub(**kwargs))
        except Exception as exception:
            raise exception

    def sub(self, **kwargs):
        #todo, regex parse for headers/docstring
        for key, value in kwargs.items():
            if key.startswith("ph_"):
                kwargs[key] = self.get_primary_header(value)
            if key.startswith("sh_"):
                kwargs[key] = self.get_secondary_header(value)
        return super(MyTemplate, self).safe_substitute(**kwargs)

    def get_primary_header(header):
        header = ('#'*5) + ' ' + header.upper() + ' '
        header += ('#'*(121-len(header)))
        return '\\n\\n' + ('#'*121) + '\\n' + header + "\\n" + ('#'*121)

    def get_secondary_header(header):
        header = ('#'*3) + ' ' + header + ' '
        header += ('#'*(121-len(header)))
        return header


APP_PY_TEMPLATE = MyTemplate("""\
${doc_string}
from bottle import run, route, request   
from bottle import static_file, template 
import argparse                      

${ph_commandline}

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )                                
parser.add_argument('-d', '--deploy',
    action='store_true' 
    help='Run server for deployment' )       
parser.add_argument('-l', '--local', 
    help='Run server for development testing on a local network' ) 
args = parser.parse_args()                                                                     

${ph_main_routes}

@route('/')
def load_index():
    return template('index')

${main_routes}

${ph_static_routes}
${static_routes}
${sh_font_routes}
@get('/fonts/<filepath:path>')
def fonts(filename):
    return static_file(filename, root='static/fonts')

${sh_favicon_routes}
@get('/favicon/<filepath:path>')
def favicon(filename):
    return static_file(filename, root='static/favicon')

${sh_general_routes}
@get('/<filename:re:.*\.(jpg|png|gif|svg)>')
def images(filename):
    return static_file(filename, root='static/img')

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root='static/css')

@get('/<filename:re:.*\.js>')
def javascript(filename):
    return static_file(filename, root='static/js')

${ph_run_server}

if args.deploy:
    run(host=args.ip, port=args.port, server='cherrypy') #deployment
else:
    run(host=args.ip, port=args.port, debug=True, reloader=True) #development """ )


MAIN_ROUTE_TEMPLATE = MyTemplate("""\
@route('/${path}')
def ${method_name}():
    return template('${template}')
""" )


STATIC_ROUTE_TEMPLATE = MyTemplate("""\
@get('/${path}')
def ${method_name}():
    return static_file('${file}', root='${root}')
""" )


########################################################################################################################
##### Script Body ######################################################################################################
########################################################################################################################

SCRIPT_DIR      = os.getcwd()
PROJECT_NAME    = os.path.relpath(SCRIPT_DIR, "..")
API_KEY         = 'adee4e8e0dc7c5fcc929047cf747f01b44bae8e5'


def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if (message): print(message)
    print("Exception: ", exception)
    if (cleanup):
        try:
            os.chdir(args.path)
            shutil.rmtree('wwww')
        except Exception as e:
            print(e)
    sys.exit(1)


def get_routes_for_directory(directory, destination): #TODO: do not include directories like .DS_STORE
    try:
        routes = []
        destination = os.path.join(args.path, destination)
        if not os.path.isdir(destination):
            os.makedirs(destination)
        os.chdir(destination)
        src_path = os.path.join(SCRIPT_DIR, directory)
        for root, dirs, files in os.walk(src_path):
            for dirname in dirs:
                if (dirname.startswith('!')):
                    dirs.remove(dirname)
            for filename in files:
                if not (filename.startswith('!')):
                    shutil.copy(os.path.join(root, filename), filename)
                    if not (filename.startswith('~')):
                        routes.append(os.path.normpath(os.path.join(os.path.relpath(root, src_path), filename)))
        return routes
    except Exception as e:
        fatal_exception(e)



try:
    args.path = os.path.abspath(args.path)
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

try:
    # generate app.py
    main_routes_string = ""
    for route in get_routes_for_directory("dev/views", "www/views"):
        delimiter = '\\' if os.name == 'nt' else '/'
        path_array = route.split(delimiter)
        path_array[-1] = path_array[-1][:-4]
        main_routes_string += MAIN_ROUTE_TEMPLATE.safe_substitute(
            path='/'.join(path_array), 
            method_name="load_{}".format(path_array[-1].split(".")[0].replace("-","_")), 
            template=path_array[-1] )

    static_routes_string = ""
    for route in get_routes_for_directory("res/static", "www/static/static"):
        static_routes_string += STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=route,
            method_name=route.split(".")[0],
            file=route,
            root='static' )

    img_routes = get_routes_for_directory("res/img", "www/static/img")
    font_routes = get_routes_for_directory("res/font", "www/static/font")
    #TODO: generate favicon folder with an api call
    #favicon_routes = get_routes_for_directory("static/favicon")
    os.chdir(os.path.join(args.path, "www"))
    #TODO: api routes
    APP_PY_TEMPLATE.populate('app.py', 
        doc_string='"""\ndocstring for {}\n"""'.format(PROJECT_NAME),
        ph_commandline="Command Line Interface",
        ph_main_routes="Main Site Routes",
        main_routes=main_routes_string,
        ph_static_routes="Static Routes",
        static_routes=static_routes_string,
        sh_font_routes_header="Font Routes",
        sh_favicon_routes_header="Favicon Routes",
        sh_general_routes_header="General Routes",
        ph_run_server_header="Run Server" )

    # import bottle into the project
    bottle_url = "https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py"
    with urllib.request.urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
        shutil.copyfileobj(response, f)
except Exception as e:
    fatal_exception(e)