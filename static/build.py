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
import subprocess


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
import re

class MyTemplate(Template):
    def __init__(self, template):
        for match in re.finditer(r'\$ph{(.*?)}', template):
            template = template.replace(match.group(0), 
                "\n\n{1}\n##### {0} {2}\n{1}".format(match.group(1).upper(), '#'*121, '#'*(121-len(match.group(1))-7)) )
        for match in re.finditer(r'\$sh{(.*?)}', template):
            template = template.replace(match.group(0), 
                "### {} {}".format(match.group(1), '#'*(121-len(match.group(1))-5)) )
        for match in re.finditer(r'\$wh{(.*?)}', template):
            template = template.replace(match.group(0), 
                "<!-- ***** {} {} -->".format(match.group(1), '*'*(121-len(match.group(1))-16)) )
        super(MyTemplate, self).__init__(template)

    def populate(self, filename, **kwargs):
        try:
            with open(filename, 'w') as f:
                f.write(self.sub(**kwargs))
        except Exception as exception:
            raise exception

    def sub(self, **kwargs):
        return super(MyTemplate, self).safe_substitute(**kwargs)
    


APP_PY_TEMPLATE = MyTemplate("""\
\"""
${doc_string}
\"""
from bottle import run, route, request   
from bottle import static_file, template 
import argparse                      

$ph{Command Line Interface}

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )                                
parser.add_argument('-d', '--deploy',
    action='store_true' 
    help='Run server for deployment' )       
parser.add_argument('-l', '--local', 
    help='Run server for development testing on a local network' ) 
args = parser.parse_args()                                                                     

$ph{Main Site Routes}

@route('/')
def load_index():
    return template('index')

${main_routes}

$ph{API and Additional Site Routes}

${api_routes}

$ph{Static Routes}

${static_routes}

$sh{Favicon Routes}
@get('/<filename:re:.*\.ico>')
def stylesheets(filename):
    return static_file(filename, root='static/favicon')

@get('/favicon/<filepath:path>')
def favicon(filename):
    return static_file(filename, root='static/favicon')

$sh{Font Routes}
@get('/fonts/<filepath:path>')
def fonts(filename):
    return static_file(filename, root='static/fonts')

$sh{General Routes}
@get('/static/<filepath:path>', method='GET')
def static(filepath):
    return static_file(filepath, root='static')

@get('/<filename:re:.*\.(jpg|png|gif|svg)>')
def images(filename):
    return static_file(filename, root='static/img')

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root='static/css')

@get('/<filename:re:.*\.js>')
def javascript(filename):
    return static_file(filename, root='static/js')

$ph{Run Server}

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
    import time
    time.sleep(35)
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
    except Exception as exception:
        raise exception




print("Creating site directory")
try:
    args.path = os.path.abspath(args.path)
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

try:
    # cleanup if project already exists
    # TODO: add ability to use already present resources
    if os.path.isdir("www"):
        shutil.rmtree('www')
except Exception as exception: 
    # TODO: different exceptions to tell if unable to remove or unable to use
    fatal_exception(exception, "Unable to clean previous site", False)



print("Importing resources and generating app.py file")
try:
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

    api_routes_string = ""
    os.chdir(os.path.join(SCRIPT_DIR, "dev/py"))
    with open('routes.py', 'r') as f:
        api_routes_string = f.read()

    os.chdir(os.path.join(args.path, "www"))
    APP_PY_TEMPLATE.populate('app.py', 
        doc_string="docstring for {}".format(PROJECT_NAME),
        main_routes=main_routes_string,
        api_routes=api_routes_string,
        static_routes=static_routes_string )
except Exception as e:
    fatal_exception(e)



print("Importing and generating additional resources")
try:
    img_routes = get_routes_for_directory("res/img", "www/static/img")
    font_routes = get_routes_for_directory("res/font", "www/static/font")
except Exception as e:
    fatal_exception(e, "Failed to import image and font resources")

try:
    if not os.path.isfile(os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))):
        raise Warning("Favicon template not found, skipping favicon resource generation")
    favicon_tpl = os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))
    os.makedirs(os.path.join(args.path, "www/static/favicon"))
    os.chdir(os.path.join(args.path, "www/static/favicon"))
    ico_res = [ "16", "24", "32", "48", "64", "128", "256" ]
    fav_res = [ "16", "32", "96", "160", "196" ]
    remove = []
    ico_command = ["convert"]
    favicon_head_string = "    <link rel=\"shortcut icon\" href=\"favicon.ico\">\n"
    for res in (ico_res + fav_res):
        name = "favicon-{0}x{0}.png".format(res)
        if os.path.isfile(name):
            continue
        subprocess.call(["inkscape", "-z", "-e", name, "-w", res, "-h", res, favicon_tpl])
        if res in ico_res:
            ico_command.append(name)
        if not res in fav_res:
            remove.append(name)
            continue
        favicon_head_string = (favicon_head_string +
            "    <link rel=\"icon\" type=\"image/png\" href=\"/favicon/{0}\" sizes=\"{1}x{1}\">\n".format(name, res) )
    ico_command.append("favicon.ico")
    subprocess.call(ico_command, shell=True)
    for name in remove:
        os.remove(name)
    
    os.chdir(os.path.join(args.path, "www/views"))
    with open('~head.tpl', 'r') as f:
        head_string = f.read()
    head_template = MyTemplate(head_string.replace('<meta name="favicon_elements">', 
        '\n$wh{Favicon Resources}\n${favicon_elements}'))
    head_template.populate('~head.tpl', favicon_elements=favicon_head_string[:-1])

except Warning as warning:
    print(warning)
except Exception as e:
    fatal_exception(e, "Failed to generate favicon resources")

try:
    os.chdir(os.path.join(args.path, "www"))
    bottle_url = "https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py"
    with urllib.request.urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
        shutil.copyfileobj(response, f)
except Exception as e:
    fatal_exception(e, "Failed to import bottle.py")

import time
time.sleep(5)
