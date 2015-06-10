


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

$ph{Command Line Interface}
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from inspect import getframeinfo, currentframe
from os.path import dirname, abspath
import os

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
os.chdir(dirname(abspath(getframeinfo(currentframe()).filename)))

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
from re import match
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
    with open( join(SCRIPT_DIR, "dev/py", "routes.py"), 'r') as f: 
        return f.read()


def migrate_static_files(source, destination):
    return [ STATIC_ROUTE(r, r.split("/")[-1], destination)
                for r in migrate_files(source, destination) ]


def generate_favicon_resources():
    fav_tpl     = lambda r: "favicon-{0}x{0}.png".format(r)
    and_tpl     = lambda r: "touch-icon-{0}x{0}.png".format(r)
    app_tpl     = lambda r: "apple-touch-icon-{0}x{0}.png".format(r)
    pra_tpl     = lambda r: "apple-touch-icon-{0}x{0}-precomposed.png".format(r)
    fav_path    = lambda p: normpath(join("static/favicon", p))
    favicon_tpl = normpath(join(SCRIPT_DIR, "res/favicon.svg"))
    ico_res     = [ "16", "24", "32", "48", "64", "128", "256" ]
    fav_res     = [ "16", "32", "96", "160", "196", "300" ]
    android_res = [ "192" ]
    apple_res   = [ "57", "76", "120", "152", "180" ] # add to head backwards
    if not isdir("static/favicon"): os.makedirs("static/favicon")

    # generate favicon resources
    for res in (list(set(ico_res) | set(fav_res)) + android_res + apple_res):
        # TODO: add exception checking
        if res in android_res: name = and_tpl(res)
        elif res in apple_res: name = app_tpl(res)
        else:                  name = fav_tpl(res)
        # TODO: this wont work if there are android and ios duplicates
        call( [ "inkscape", "-z", "-e", fav_path(name), "-w", res, "-h", res, 
              favicon_tpl], shell=True )
        print([ "inkscape", "-z", "-e", fav_path(name), "-w", res, "-h", res, 
              favicon_tpl])
    call( ["convert"] + [fav_path(fav_tpl(r)) for r in ico_res] + 
          [fav_path("favicon.ico")], shell=True )
    for res in [ r for r in ico_res if r not in fav_res ]:
        os.remove(fav_path(fav_tpl(res)))
    
    # return routes for generated favicon resources
    fav_route = lambda f:   STATIC_ROUTE(f, f, "static/favicon")
    app_route = lambda p,t: STATIC_ROUTE(p, t("57"), "static/favicon")
    return ([ fav_route(fav_tpl(r)) for r in fav_res ] +
            [ fav_route(and_tpl(r)) for r in android_res ] +
            [ fav_route(app_tpl(r)) for r in apple_res if r!="57" ] +
            [ fav_route(pra_tpl(r)) for r in apple_res if r!="57" ] +
            [ app_route("apple-touch-icon.png", app_tpl),
              app_route("apple-touch-icon-precomposed.png", pra_tpl) ])


def generate_stylesheets():
    sass_path  = join( SCRIPT_DIR, "dev/sass" )
    is_sass    = lambda f: splitext(f)[-1].lower() in ['.scss', '.sass']
    is_mixin   = lambda f: match(r'.*mixins?$', splitext(f)[0].lower())
    get_import = lambda p: [ join(root, file) for root, d, files in os.walk(p)
                             for file in files if is_sass(file) ]
    if not isdir("static/css"): os.makedirs("static/css")

    # generate _all.scss file from existing sass resources
    # TODO: this will only work for the de4fault sass directory setup
    with open( join( sass_path, '_all.scss' ), 'w') as f:
        f.write('\n'.join( # probably not the most effecient way
            [ '@import "{}";'.format(path.replace('\\', '/')) for path in 
                ( # mixins and global variables must be imported first
                    # modules
                    [ f for f in get_import('modules') ]
                    # vendor mixins 
                  + [ f for f in get_import('vendor') if is_mixin(f) ]
                    # all other vendor files
                  + [ f for f in get_import('vendor') if not is_mixin(f) ]
                    # partials (comment out this line for manually selection)
                  + [ f for f in get_import('partials') ]
                ) 
            ] ) 
        )

    # use sass command line tool to generate stylesheets


    # return css routes from generated stylesheets
    return ""



#rmtree('www')


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
# head is generated by inspecting www and seeing what files are there
Template.populate(APP_PY_TEMPLATE, 'app.py', 
    doc_string=900,
    main_routes=migrate_views(),
    api_routes=get_api_routes(),
    static_routes=migrate_static_files("res/static", "static"),
    favicon_routes=generate_favicon_resources(),
    image_routes=migrate_static_files("res/img", "static/img"),
    font_routes=migrate_static_files("res/font", "static/font"),
    css_routes=generate_stylesheets(),
    js_routes="" )


exit(0)
# note, everything needs a unique name using this method


print("  --  Generating stylesheets") ##########################################
css_head_string = ""
try:
    os.chdir(os.path.join(SCRIPT_DIR, "dev/sass"))
    os.makedirs(os.path.join(args.path, "www/static/css"))
    stylesheets = []
    with open('_all.scss', 'w') as f:
        import_array = []
        for root, dirs, files in os.walk(os.getcwd()):
            # uncomment if you want to pick and choose which 
            # partials to include 
            #if 'partials' in dirs: dirs.remove('partials')
            for file in files:
                directory = os.path.relpath(root, os.getcwd())
                if directory == '.':
                    if os.path.splitext(file)[-1].lower() in ['.scss', '.sass']:
                        stylesheets.append(file)
                    continue
                if not file.startswith('~') \
                and os.path.splitext(file)[-1].lower() in ['.scss', '.sass']:
                    import_string = '@import "{}";\n'.format(
                        os.path.join(directory, file).replace('\\', '/'))
                    if re.match(r'.*mixins?$', 
                        os.path.splitext(file)[0].lower()) \
                    or directory == 'modules':
                        import_array.insert(0, import_string) 
                        #mixins and variables are imported first
                    else:
                        import_array.append(import_string)
        for string in import_array:
            f.write(string)
    sass_path = os.path.join(os.path.relpath(args.path, os.getcwd()), "www/static/css").replace('\\', '/')
    stylesheet_tpl = "    <link href=\"{}.css\" rel=\"stylesheet\" type=\"text/css\">\n"
    stylesheets = [ os.path.splitext(x)[0] for x in stylesheets ]
    if '_all' in stylesheets: stylesheets.remove('_all')
    if 'styles' in stylesheets: css_head_string += stylesheet_tpl.format('styles.min' if args.deploy else 'styles')
    if args.deploy:
        for name in stylesheets:
            subprocess.call(
                "sass {0}.scss {1}/{0}.min.css -t compressed --sourcemap=none -C".format(name, sass_path), shell=True)
        os.remove("_all.scss")
    else: # TODO: if dev mode add sass maps to routes
        WATCH_SASS_SCRIPT.populate('watch.py')
        if (os.name == 'nt'):
            subprocess.Popen([sys.executable, 'watch.py', sass_path] + stylesheets, 
                creationflags = subprocess.CREATE_NEW_CONSOLE )
        else:
            subprocess.Popen([sys.executable, 'watch.py', sass_path] + stylesheets)
    if 'styles' in stylesheets: stylesheets.remove('styles')
    css_head_string += "    % if template in {}:\n".format(stylesheets)
    css_head_string += stylesheet_tpl.format('{{template}}.min' if args.deploy else '{{template}}')
    css_head_string += "    % end"
except Exception as e:
    fatal_exception(e, "Could not generate stylesheets")