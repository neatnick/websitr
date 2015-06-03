


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
    try:
        routes = []
        destination = join(args.path, destination)
        if not isdir(destination): os.makedirs(destination)
        src_path = join(SCRIPT_DIR, directory)
        for root, dirs, files in os.walk(src_path):
            for dirname in dirs:
                if dirname.startswith('!') or dirname in ['.DS_STORE']:
                    dirs.remove(dirname)
            for filename in files:
                if not filename.startswith('!'):
                    if not isfile(filename): #added for the reuse flag
                        copy(join(root, filename), join(destination, filename))
                    if not filename.startswith('~'):
                        routes.append(
                            normpath(
                                join(relpath(root, src_path), filename)
                            ).replace('\\', '/')
                        )
        return routes
    except Exception as exception:
        raise exception


def migrate_views():
    return ([ MAIN_ROUTE("", "load_root", "index") ] + 
            [ MAIN_ROUTE(
                splitext(r)[0],
                "load_" + splitext(r.split("/")[-1])[0].replace("-","_"),
                splitext(r.split("/")[-1])[0] 
            ) for r in migrate_files("dev/views", "www/views") ])


def get_api_routes(): # TODO: multiple file support here?
    file = join(SCRIPT_DIR, "dev/py", "routes.py")
    with open(file, 'r') as f:
        return f.read()


def migrate_static_files(source, destination):
    return [ STATIC_ROUTE(r, r.split("/")[-1], destination)
                for r in migrate_files(source, destination) ]


def generate_favicon_resources():
    fav_path    = lambda p: normpath(join(args.path, "www/static/favicon", p))
    favicon_tpl = normpath(join(SCRIPT_DIR, "res/favicon.svg"))
    fav_tpl     = "favicon-{0}x{0}.png"
    and_tpl     = "touch-icon-{0}x{0}.png"
    app_tpl     = "apple-touch-icon-{0}x{0}.png"
    ico_res     = [ "16", "24", "32", "48", "64", "128", "256" ]
    fav_res     = [ "16", "32", "96", "160", "196", "300" ]
    android_res = [ "192" ]
    apple_res   = [ "57", "76", "120", "152", "180" ] # add to head backwards
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
        os.remove(fav_path(fav_tpl.format(r)))
    
    return ""




rmtree('www')


os.chdir(args.path)
os.makedirs("www")
os.chdir("www")
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
    favicon_routes="",
    image_routes=migrate_static_files("res/img", "static/img"),
    font_routes=migrate_static_files("res/font", "static/font"),
    css_routes="",
    js_routes="" )


exit(0)
# note, everything needs a unique name using this method

print("  --  Generating favicon resources") ####################################
favicon_routes_string = ""
favicon_head_string = ""
try:
    favicon_res_path = os.path.join(args.path, "www/static/favicon")
    favicon_tpl = os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))
    if args.reuse and os.path.isdir(favicon_res_path): # TODO: head string and routes still need to be created
        raise Warning("Reuse flag enabled and previous resources were found, skipping favicon generation")
    if not os.path.isfile(favicon_tpl):
        raise Warning("Favicon template not found, skipping favicon resource generation")
    os.makedirs(favicon_res_path)
    os.chdir(favicon_res_path)
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
    # touch icon for chrome for android
    android_res = "192"
    android_name = "touch-icon-{0}x{0}.png".format(android_res)
    subprocess.call(["inkscape", "-z", "-e", android_name, "-w", android_res, "-h", res, favicon_tpl])
    favicon_head_string = (favicon_head_string +
        "    <link rel=\"icon\" href=\"/{0}\" sizes=\"{1}x{1}\">\n".format(android_name, android_res) )
    favicon_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
        path=android_name, method_name="touch_icon", file=android_name, root='static/favicon' )
    # touch icons for ios
    apple_res = [ "180", "152", "120", "76", "57" ]
    for res in apple_res:
        name = "apple-touch-icon-{0}x{0}.png".format(res)
        precomposed_name = "apple-touch-icon-{0}x{0}-precomposed.png".format(res)
        subprocess.call(["inkscape", "-z", "-e", name, "-w", res, "-h", res, favicon_tpl])
        favicon_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=name, method_name=os.path.splitext(name)[0].replace("-","_"),
            file=name, root='static/favicon' )
        favicon_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=precomposed_name, method_name=os.path.splitext(precomposed_name)[0].replace("-","_"),
            file=name, root='static/favicon' )
        if res == "57":
            favicon_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
                path="apple-touch-icon.png", method_name="apple_touch_icon",
                file=name, root='static/favicon' )
            favicon_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
                path="apple-touch-icon-precomposed.png", method_name="apple_touch_icon_precomposed",
                file=name, root='static/favicon' )
            continue
        favicon_head_string = (favicon_head_string +
            "    <link rel=\"apple-touch-icon\" href=\"{0}\" sizes=\"{1}x{1}\">\n".format(name, res) )
    favicon_head_string = (favicon_head_string +
        "    <link rel=\"apple-touch-icon\" href=\"apple-touch-icon.png\">\n" )
    # TODO: msapplication
    favicon_head_string = favicon_head_string[:-1]
except Warning as warning:
    print(warning)
except Exception as e:
    fatal_exception(e, "Failed to generate favicon resources")