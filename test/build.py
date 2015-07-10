


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
##### Overrides ################################################################
################################################################################

from string import Template
from re import compile

class TemplateWrapper():

    def __init__(self, cls):
        PYTHON_LL = 80
        HTML_LL   = 120

        self.cls = cls
        self.headers = [
            (   # Primary python file header template
                compile(r'\$ph{(.*?)}'),
                lambda x: "\n\n{1}\n##### {0} {2}\n{1}\n".format(
                    x.upper(), '#'*PYTHON_LL, '#'*(PYTHON_LL-len(x)-7) )
            ),
            (   # Secondary python file header template
                compile(r'\$sh{(.*?)}'),
                lambda x: "\n### {0} {1}".format(
                    x, '#'*(PYTHON_LL-len(x)-5) )
            ),
            (   # HTML file header template
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
                # TODO: rather than having all of these template objects I could
                #       just convert from a string to a template here
                #       i.e. : template = Template(template)
                #       youd have to move header generation to populate
                f.write(template.safe_substitute(**kwargs))
        except Exception as exception:
            raise exception

Template = TemplateWrapper(Template)

    
from subprocess import Popen, call, DEVNULL, STDOUT, PIPE
from sys import executable

def sPopen(*args):
    command, shell = list(args), True
    if command[0] == 'python': 
        command[0] = executable
        shell = False
    if os.name == 'nt':
        from subprocess import CREATE_NEW_CONSOLE
        Popen( command, shell=shell, creationflags=CREATE_NEW_CONSOLE )
    else:
        Popen( command, shell=shell )

def sCall(*args):
    command, shell = list(args), True
    if command[0] == 'python': 
        command[0] = executable
        shell = False
    if os.name != 'nt':
        shell = False # TODO: not sure why i need this
    call( command, shell=shell, stdout=DEVNULL, stderr=STDOUT )



################################################################################
##### Templates ################################################################
################################################################################

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
from sys import argv
from shutil import rmtree
from subprocess import Popen
from inspect import getframeinfo, currentframe
from os.path import dirname, abspath, isdir, isfile
import os

# change working directory to script directory
os.chdir(dirname(abspath(getframeinfo(currentframe()).filename)))

command = "sass --watch"
for x in range(1, len(argv)):
    command += " {0}.scss:../../www/static/css/{0}.css".format(argv[x])
p = Popen(command, shell=True)
try:
    while True:
        pass
except KeyboardInterrupt:
    p.kill()
    if isfile("_all.scss"): os.remove("_all.scss")
    if isdir(".sass-cache"): rmtree(".sass-cache")
    os.remove("watch.py") # argv[0] contains full path
""" )



################################################################################
##### Script Body ##############################################################
################################################################################

from os.path import relpath, abspath, normpath, join, isfile, isdir, splitext
from shutil import copy, copyfileobj, rmtree
from urllib.request import urlopen
from time import sleep
from re import match
from sys import exit

SCRIPT_DIR   = os.getcwd()
PROJECT_NAME = relpath(SCRIPT_DIR, "..")
STATIC_ROUTE = lambda p, f, r: \
    ( STATIC_ROUTE_TEMPLATE, { "path": p, "file": f, "root": r } )
MAIN_ROUTE   = lambda p, m, t: \
    ( MAIN_ROUTE_TEMPLATE, { "path": p, "method_name": m, "template": t } )


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



def generate_favicon_resources(): # TODO: adhere to ! ~ rules?
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
        if res in android_res: path = abspath( fav_path(and_tpl(res)) )
        elif res in apple_res: path = abspath( fav_path(app_tpl(res)) )
        else:                  path = abspath( fav_path(fav_tpl(res)) )
        # TODO: this wont work if there are android and ios duplicates
        sCall("inkscape", "-z", "-e", path, "-w", res, "-h", res, favicon_tpl)
    # TODO: theres gotta be a cleaner way than this (bet i can get it on 1 line)
    sCall( *(["convert"] + [fav_path(fav_tpl(r)) for r in ico_res] + 
             [fav_path("favicon.ico")]) )
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



def generate_stylesheets(): # TODO: adhere to ! ~ rules?
    dev_path   = join( SCRIPT_DIR, "dev/sass" )
    is_sass    = lambda f: splitext(f)[-1].lower() in ['.scss', '.sass']
    is_mixin   = lambda f: match(r'.*mixins?$', splitext(f)[0].lower())
    get_import = lambda p: [ join( relpath(r, dev_path), f ) 
                             for r, d, fs in os.walk( join(dev_path, p) ) 
                             for f in fs if is_sass(f) ]
    if not isdir("static/css"): os.makedirs("static/css")

    # generate _all.scss file from existing sass resources
    # TODO: this will only work for the default sass directory setup
    with open( join( dev_path, '_all.scss' ), 'w') as f:
        f.write('\n'.join( # probably not the most efficient way
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
    stylesheets = [ splitext(f)[0] for f in os.listdir(dev_path) 
                    if is_sass(f) and not f.startswith('_') ]
    sass_path = relpath(dev_path, os.getcwd()).replace('\\', '/')
    if args.deploy:
        for s in stylesheets:
            sCall("sass", sass_path+"/"+s+".scss", "static/css/"+s+".min.css", 
                  "-t", "compressed", "--sourcemap=none", "-C")
        os.remove( join(dev_path, "_all.scss") )
    else: # TODO: if dev mode add sass maps to routes (i think it will)
        Template.populate(WATCH_SASS_SCRIPT, '../dev/sass/watch.py')
        sPopen( 'python', '../dev/sass/watch.py', *stylesheets )
        sleep(3) # delay so the stylesheets have time to be created

    # return css routes from generated stylesheets
    return [ STATIC_ROUTE(f, f, "static/css") for f in os.listdir("static/css")]



def generate_javascript():
    if not isdir("static/js"): os.makedirs("static/js")
    return [ STATIC_ROUTE(f, f, "static/js") for f in os.listdir("static/js")]



def get_favicon_head():
    # TODO: revisit this at some point
    link_tpl   = lambda c: ('    <link', c, '>\n')
    all_favs   = os.listdir('static/favicon')
    favicons   = [ x for x in all_favs if x.startswith('favicon') ]
    apple_favs = [ x for x in all_favs if x.startswith('apple')   ]
    print( "\n".join(favicons) )
    print( "\n" )
    return ""



def get_opengraph_head():
    og_head_string = """\
    % url = request.environ['HTTP_HOST']
    <meta property="og:url" content="http://{{url}}/">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{{title}}">
    <meta property="open_graph_image">
    <meta property="og:description" content="{{description}}">"""
    og_image_string = """<meta property="og:image:type" content="image/png">
    <meta property="og:image:width" content="300">
    <meta property="og:image:height" content="300">
    <meta property="og:image" content="http://{{url}}/favicon-300x300.png">
    <meta property="og:image:url" content="http://{{url}}/favicon-300x300.png">""" 
    if isfile("static/favicon/favicon-300x300.png"):
        og_head_string = og_head_string.replace(
            '<meta property="open_graph_image">', 
            og_image_string
        )
    return og_head_string



def get_stylesheet_head():
    return ""



rmtree('www')


os.chdir(args.path)
os.makedirs("www")
os.chdir("www") # all operations will happen relative to www
#os.chdir(join(args.path, "www"))

# import bottle framework 
# TODO: something here to account for offline use?
# bottle_url = ( "https://raw.githubusercontent.com/"
#                 "bottlepy/bottle/master/bottle.py" )
# with urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
#     copyfileobj(response, f)

# generate app.py
# TODO: hide headers if there are no routes for that section?
Template.populate(APP_PY_TEMPLATE, 'app.py', 
    doc_string="",
    main_routes=migrate_views(),
    api_routes=get_api_routes(),
    static_routes=migrate_static_files("res/static", "static"),
    favicon_routes=generate_favicon_resources(),
    image_routes=migrate_static_files("res/img", "static/img"),
    font_routes=migrate_static_files("res/font", "static/font"),
    css_routes=generate_stylesheets(),
    js_routes=generate_javascript() )

# generate head template
# TODO: have default if ~head.tpl not present?
# TODO: don't bothering copying head over in migrate views?
if isfile('views/~head.tpl'): os.remove('views/~head.tpl')
head_tpl = ""
with open(join(SCRIPT_DIR, "dev/views/~head.tpl"), 'r') as head:
    head_tpl = head.read()
# TODO: decide when not to convert these meta tags
metas = [ "Favicon_Resources", "Open_Graph", "Style_Sheets" ]
for meta in metas:
    head_tpl = head_tpl.replace(
        '<meta name="'+meta.lower()+'">',
        '\n$wh{'+meta.replace('_', ' ')+'}\n${'+meta.lower()+'}'
    )
Template.populate(Template(head_tpl), 'views/~head.tpl',
    favicon_resources=get_favicon_head(),
    open_graph=get_opengraph_head(),
    style_sheets=get_stylesheet_head() )


exit(0)
# note, everything needs a unique name using this method
# head is generated by inspecting www and seeing what files are there





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
    sass_path = os.path.join(os.path.relpath(args.path, os.getcwd()), 
        "www/static/css").replace('\\', '/')
    stylesheet_tpl = (
        "    <link href=\"{}.css\" rel=\"stylesheet\" type=\"text/css\">\n")
    stylesheets = [ os.path.splitext(x)[0] for x in stylesheets ]
    if '_all' in stylesheets: stylesheets.remove('_all')
    if 'styles' in stylesheets: 
        css_head_string += stylesheet_tpl.format(
            'styles.min' if args.deploy else 'styles'
        )
    if args.deploy:
        for name in stylesheets:
            subprocess.call(
"sass {0}.scss {1}/{0}.min.css -t compressed --sourcemap=none -C".format(
                name, sass_path), shell=True)
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
    css_head_string += stylesheet_tpl.format('{{template}}.min' if args.deploy \
        else '{{template}}')
    css_head_string += "    % end"
except Exception as e:
    fatal_exception(e, "Could not generate stylesheets")