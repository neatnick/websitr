


################################################################################
##### Command Line Interface ###################################################
################################################################################

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from tempfile import gettempdir
import os

parser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("-p", "--path", 
    type=str,
    help="the path to the desired location of the generated site")
parser.add_argument("-d", "--deploy",
    action="store_true",
    help="package site for movement to deployment server. Default path is the"
    "current working directory, but the path flag will override that value" )
parser.add_argument("-r", "--reuse",
    action="store_true",
    help="if an already built website exists at the targeted path, attempt to"
    "reuse already present resources (i.e. images, favicon elements and other" 
    "static resources)" )
args = parser.parse_args()

if args.path is None:
    if args.deploy:
        args.path = os.getcwd()
    else:
        args.path = gettempdir()



################################################################################
##### Templates ################################################################
################################################################################

from string import Template
from re import compile

class TemplateWrapper():

    def __init__(self, cls):
        PYTHON_LL = 80
        HTML_LL   = 120

        self.cls = cls
        self.headers = [
            # Primary python file header template
            ( 
                compile(r'\$ph{(.*?)}'),
                lambda x: "\n\n{1}\n##### {0} {2}\n{1}\n".format(
                    x.upper(), '#'*PYTHON_LL, '#'*(PYTHON_LL-len(x)-7) )
            ),

            # Secondary python file header template
            ( 
                compile(r'\$sh{(.*?)}'),
                lambda x: "\n### {0} {1}".format(
                    x, '#'*(PYTHON_LL-len(x)-5) )
            ),

            # HTML file header template
            ( 
                compile(r'\$wh{(.*?)}'),
                lambda x: "<!-- ***** {0} {1} -->".format(
                    x, '*'*(HTML_LL-len(x)-16) )
            )
        ]
        
    def __call__(self, template):
        for header in self.headers:
            ptn, tpl = header
            for match in ptn.finditer(template):
                replacements = ( match.group(0), tpl(match.group(1)) )
                template = template.replace(*replacements)
        template_obj = self.cls(template)
        template_obj.populate = self.populate
        return template_obj


    @staticmethod
    def populate(template, filepath, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                kwargs[key] = "\n".join(
                    [ t[0].safe_substitute(**t[1]) for t in value ]
                )
        try:
            with open(filepath, 'w') as f:
                f.write(template.safe_substitute(**kwargs))
        except Exception as exception:
            raise exception

Template = TemplateWrapper(Template)
    


APP_PY_TEMPLATE = Template("""\
\"""
${doc_string}
\"""
from bottle import run, route, get, post, error
from bottle import static_file, template, request
from bottle import HTTPError
import argparse, os, inspect

$ph{Command Line Interface}
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )                                
parser.add_argument('-d', '--deploy',
    action='store_true',
    help='Run server for deployment' )       
parser.add_argument('-i', '--ip', 
    type=str,
    default="127.0.0.1",
    help='ip to run the server against, default localhost' ) 
parser.add_argument('-p', '--port', 
    type=str,
    default="8080",
    help='port to run server on' ) 
args = parser.parse_args()

# change working directory to script directory
filename = inspect.getframeinfo(inspect.currentframe()).filename
os.chdir(os.path.dirname(os.path.abspath(filename)))

$ph{Main Site Routes}
${main_routes}
$ph{API and Additional Site Routes}
${api_routes}

$ph{Static Routes}
${static_routes}
$sh{Favicon Routes}
${favicon_routes}
$sh{Image Routes}
${image_routes}
$sh{Font Routes}
${font_routes}
$sh{Stylesheet Routes}
${css_routes}
$sh{Javascript Routes}
${js_routes}
$ph{Error Routes}
@error(404)
def error404(error):
    return 'nothing to see here'

$ph{Run Server}
if args.deploy:
    run(host=args.ip, port=args.port, server='cherrypy') #deployment
else:
    run(host=args.ip, port=args.port, debug=True, reloader=True) #development 
""" )


MAIN_ROUTE_TEMPLATE = Template("""\
@route('/${path}')
def ${method_name}():
    return template('${template}', request=request, template='${template}')
""" )


STATIC_ROUTE_TEMPLATE = Template("""\
@get('/${path}')
def load_resource():
    return static_file('${file}', root='${root}')
""" )


WATCH_SASS_SCRIPT = Template("""\
import os
import sys
from subprocess import Popen 
from shutil import rmtree

command = "sass --watch"
for x in range(2, len(sys.argv)):
    command += " {1}.scss:{0}/{1}.css".format(sys.argv[1], sys.argv[x])
p = Popen(command, shell=True)
try:
    while True:
        pass
except KeyboardInterrupt:
    p.kill()
    os.remove("_all.scss")
    if os.path.isdir(".sass-cache"):
        rmtree(".sass-cache")
    os.remove(sys.argv[0])
""" )



################################################################################
##### Script Body ##############################################################
################################################################################

from os.path import relpath, normpath, join, isfile, isdir, splitext
from shutil import copy, copyfileobj, rmtree
from urllib.request import urlopen
from subprocess import call, Popen
from sys import exit

SCRIPT_DIR   = os.getcwd()
PROJECT_NAME = relpath(SCRIPT_DIR, "..")
STATIC_ROUTE = lambda p, f, r: \
    ( STATIC_ROUTE_TEMPLATE, { "path": p, "file": f, "root": r } )
MAIN_ROUTE   = lambda p, m, t: \
    ( MAIN_ROUTE_TEMPLATE, { "path": p, "method_name": m, "template": t } )

def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if message: print(message)
    print("Exception: ", exception)
    if cleanup:
        try:
            os.chdir(args.path)
            rmtree('www')
        except Exception as e:
            print(e)
    exit(1)


def migrate_files(directory, destination):
    src_path = join(SCRIPT_DIR, directory)
    if not isdir(destination): os.makedirs(destination)
    for root, dirs, files in os.walk(src_path):
        for dirname in dirs:
            if dirname.startswith('!') or dirname in ['.DS_STORE']:
                dirs.remove(dirname)
        for filename in files:
            if not filename.startswith('!'):
                if not isfile(filename): #added for the reuse flag
                    copy(join(root, filename), join(destination, filename))
                if not filename.startswith('~'):
                    yield normpath(join(relpath(root, src_path), 
                                        filename) ).replace('\\', '/')


def migrate_views():
    return ([ MAIN_ROUTE("", "load_root", "index") ] + 
            [ MAIN_ROUTE(
                splitext(r)[0],
                "load_" + splitext(r.split("/")[-1])[0].replace("-","_"),
                splitext(r.split("/")[-1])[0] 
            ) for r in migrate_files("dev/views", "views") ])


def get_api_routes(): # TODO: multiple file support here?
    file = join(SCRIPT_DIR, "dev/py", "routes.py")
    with open(file, 'r') as f:
        return f.read()


def migrate_static_files(source, destination):
    return [ STATIC_ROUTE(r, r.split("/")[-1], destination)
                for r in migrate_files(source, destination) ]


def generate_favicon_resources():
    fav_path    = lambda p: normpath(join("static/favicon", p))
    favicon_tpl = normpath(join(SCRIPT_DIR, "res/favicon.svg"))
    fav_tpl     = "favicon-{0}x{0}.png"
    and_tpl     = "touch-icon-{0}x{0}.png"
    app_tpl     = "apple-touch-icon-{0}x{0}.png"
    pra_tpl     = "apple-touch-icon-{0}x{0}-precomposed.png"
    ico_res     = [ "16", "24", "32", "48", "64", "128", "256" ]
    fav_res     = [ "16", "32", "96", "160", "196", "300" ]
    android_res = [ "192" ]
    apple_res   = [ "57", "76", "120", "152", "180" ] # add to head backwards
    if not isdir("static/favicon"): os.makedirs("static/favicon")
    for res in (list(set(ico_res) | set(fav_res)) + android_res + apple_res):
        # TODO: add exception checking
        if res in android_res: name = and_tpl.format(res)
        elif res in apple_res: name = app_tpl.format(res)
        else:                  name = fav_tpl.format(res)
        # TODO: this wont work if there are android and ios duplicates
        call( [ "inkscape", "-z", "-e", fav_path(name), "-w", res, "-h", res, 
              favicon_tpl], shell=True )
    call( ["convert"] + [fav_path(fav_tpl.format(r)) for r in ico_res] + 
          [fav_path("favicon.ico")], shell=True )
    for res in [ r for r in ico_res if r not in fav_res ]:
        os.remove(fav_path(fav_tpl.format(res)))
    
    favicon_route = lambda f:  STATIC_ROUTE(f, f, "static/favicon")
    apple_route   = lambda p,t:STATIC_ROUTE(p, t.format("57"), "static/favicon")
    return ([ favicon_route(fav_tpl.format(r)) for r in fav_res ] +
            [ favicon_route(and_tpl.format(r)) for r in android_res ] +
            [ favicon_route(app_tpl.format(r)) for r in apple_res if r!="57" ] +
            [ favicon_route(pra_tpl.format(r)) for r in apple_res if r!="57" ] +
            [ apple_route("apple-touch-icon.png", app_tpl),
              apple_route("apple-touch-icon-precomposed.png", pra_tpl) ] )



rmtree('www')


os.chdir(args.path)
os.makedirs("www")
os.chdir("www") # all operations will happen relative to www
#os.chdir(join(args.path, "www"))

# import bottle framework
bottle_url = ( "https://raw.githubusercontent.com/"
                "bottlepy/bottle/master/bottle.py" )
with urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
    copyfileobj(response, f)

# generate app.py
# TODO: hide headers if there are no routes for that section?
Template.populate(APP_PY_TEMPLATE, 'app.py', 
    doc_string=900,
    main_routes=migrate_views(),
    api_routes=get_api_routes(),
    static_routes=migrate_static_files("res/static", "static"),
    favicon_routes=generate_favicon_resources(),
    image_routes=migrate_static_files("res/img", "static/img"),
    font_routes=migrate_static_files("res/font", "static/font"),
    css_routes="",
    js_routes="" )


exit(0)
# note, everything needs a unique name using this method