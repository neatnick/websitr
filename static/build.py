"""
files or directories with a ! in front of them will not be copied into the project
files or directories with a ~ in front of them will not have a route added for them

if the deploy flag is not given the site will be build as if for local development and testing
"""

# arguments:
# - path to put the generated site
# - whether to update non-local site files (i.e. bottle)
# - whether to update static local site files (i.e. img/fonts/misc.)
#
# - development flag: (set up site for local dev/testing)
#    + put generated site in tmp
#    + attempt to update non-local files (non-fatal exception if unable to)
#    + start webserver with development flag
#
# - deployment flag: (package site for scp to deployment server)
#    + put generated site in path (required argument for the flag)
#    + update non-local (?)
#    + start webserver with deploy flag


import os, sys, tempfile
import urllib.request
import shutil, argparse
import subprocess, zipfile


#########################################################################################################################
##### Command Line Interface ############################################################################################
#########################################################################################################################

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("-d", "--deploy",
    action="store_true",
    help="package site for movement to deployment server. Default path is the current working "
    "directory, but the path flag will override that value." )
parser.add_argument("-p", "--path", 
    type=str,
    help="the path to the desired location of the generated site")
args = parser.parse_args()

if args.path is None:
    if args.deploy:
        args.path = os.getcwd()
    else:
        args.path = tempfile.gettempdir()



#########################################################################################################################
##### Templates #########################################################################################################
#########################################################################################################################

from string import Template
import re

class MyTemplate(Template):
    def __init__(self, template):
        for match in re.finditer(r'\$ph{(.*?)}', template):
            template = template.replace(match.group(0), 
                "\n\n{1}\n##### {0} {2}\n{1}\n".format(match.group(1).upper(),
                    '#'*121, '#'*(121-len(match.group(1))-7)) )
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
@route('/')
def load_root():
    return template('index', request=request)
${main_routes}

$ph{API and Additional Site Routes}${api_routes}

$ph{Static Routes}${static_routes}

$sh{Favicon Routes}${favicon_routes}
@get('/<filename:re:.*\.ico>')
def stylesheets(filename):
    if (filename.startswith('~')):
        raise HTTPError(404, "File does not exist.")
    return static_file(filename, root='static/favicon')

@get('/favicon/<filepath:path>')
def favicon(filepath):
    for item in filepath.split('/'):
        if (item.startswith('~')):
            raise HTTPError(404, "File does not exist.")
    return static_file(filepath, root='static/favicon')

$sh{Font Routes}
@get('/fonts/<filepath:path>')
def fonts(filepath):
    for item in filepath.split('/'):
        if (item.startswith('~')):
            raise HTTPError(404, "File does not exist.")
    return static_file(filepath, root='static/fonts')

$sh{General Routes}
@get('/static/<filepath:path>', method='GET')
def static(filepath):
    for item in filepath.split('/'):
        if (item.startswith('~')):
            raise HTTPError(404, "File does not exist.")
    return static_file(filepath, root='static')

@get('/<filename:re:.*\.(jpg|png|gif|svg)>')
def images(filename):
    if (filename.startswith('~')):
        raise HTTPError(404, "File does not exist.")
    return static_file(filename, root='static/img')

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    if (filename.startswith('~')):
        raise HTTPError(404, "File does not exist.")
    return static_file(filename, root='static/css')

@get('/<filename:re:.*\.js>')
def javascript(filename):
    if (filename.startswith('~')):
        raise HTTPError(404, "File does not exist.")
    return static_file(filename, root='static/js')

$ph{Error Routes}
@error(404)
def error404(error):
    return 'nothing to see here'

$ph{Run Server}
if args.deploy:
    run(host=args.ip, port=args.port, server='cherrypy') #deployment
else:
    run(host=args.ip, port=args.port, debug=True, reloader=True) #development """ )


MAIN_ROUTE_TEMPLATE = MyTemplate("""\
@route('/${path}')
def ${method_name}():
    return template('${template}', request=request)
""" )


STATIC_ROUTE_TEMPLATE = MyTemplate("""\
@get('/${path}')
def ${method_name}():
    return static_file('${file}', root='${root}')
""" )


WATCH_SASS_SCRIPT = MyTemplate("""\
import subprocess, sys, os, shutil

p = subprocess.Popen("sass --watch {0}.scss:{1}/{0}".format(sys.argv[1], sys.argv[2]), shell=True)
try:
    while True:
        pass
except KeyboardInterrupt:
    p.kill()
    os.remove("_all.scss")
    if os.path.isdir(".sass-cache"):
        shutil.rmtree(".sass-cache")
    os.remove(sys.argv[0])""" )


#########################################################################################################################
##### Script Body #######################################################################################################
#########################################################################################################################

SCRIPT_DIR      = os.getcwd()
PROJECT_NAME    = os.path.relpath(SCRIPT_DIR, "..")


def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if (message): print(message)
    print("Exception: ", exception)
    if (cleanup):
        try:
            os.chdir(args.path)
            shutil.rmtree('www')
        except Exception as e:
            print(e)
    import time
    time.sleep(10)
    sys.exit(1)


def get_routes_for_directory(directory, destination):
    try:
        routes = []
        destination = os.path.join(args.path, destination)
        if not os.path.isdir(destination):
            os.makedirs(destination)
        os.chdir(destination)
        src_path = os.path.join(SCRIPT_DIR, directory)
        for root, dirs, files in os.walk(src_path):
            for dirname in dirs:
                if dirname.startswith('!') or dirname in ['.DS_STORE']:
                    dirs.remove(dirname)
            for filename in files:
                if not filename.startswith('!'):
                    shutil.copy(os.path.join(root, filename), filename)
                    if not filename.startswith('~'):
                        routes.append(os.path.normpath(os.path.join(os.path.relpath(root, src_path), filename)))
        return routes
    except Exception as exception:
        raise exception




print("""> \
Creating site directory""" )

print("  --  Verifying path") ###########################################################################################
try:
    args.path = os.path.abspath(args.path)
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

print("  --  Searching for already present resources") ##################################################################
try:
    # cleanup if project already exists
    # TODO: add ability to use already present resources
    if os.path.isdir("www"):
        shutil.rmtree('www')
except Exception as exception: 
    # TODO: different exceptions to tell if unable to remove or unable to use
    fatal_exception(exception, "Unable to clean previous site", False)



print("""> \
Importing and generating site resources""" )

print("  --  Importing views") ##########################################################################################
main_routes_string = ""
try:
    for route in get_routes_for_directory("dev/views", "www/views"):
        delimiter = '\\' if os.name == 'nt' else '/'
        path_array = route.split(delimiter)
        path_array[-1] = path_array[-1][:-4]
        main_routes_string += "\n" + MAIN_ROUTE_TEMPLATE.safe_substitute(
            path='/'.join(path_array), 
            method_name="load_{}".format(path_array[-1].split(".")[0].replace("-","_")), 
            template=path_array[-1] )
        main_routes_string = main_routes_string[:-1]
except Exception as e:
    fatal_exception(e)

print("  --  Importing image and font resources") #######################################################################
try:
    img_routes = get_routes_for_directory("res/img", "www/static/img")
    font_routes = get_routes_for_directory("res/font", "www/static/font")
except Exception as e:
    fatal_exception(e, "Failed to import image and font resources")

print("  --  Importing miscellaneous static resources") #################################################################
static_routes_string = ""
try:
    for route in get_routes_for_directory("res/static", "www/static"):
        static_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=route, method_name=route.split(".")[0],
            file=route, root='static' )
except Exception as e:
    fatal_exception(e)

print("  --  Importing bottle framework") ###############################################################################
try:
    os.chdir(os.path.join(args.path, "www"))
    bottle_url = "https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py"
    with urllib.request.urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
        shutil.copyfileobj(response, f)
except Exception as e:
    fatal_exception(e, "Failed to import bottle.py")

print("  --  Generating favicon resources") #############################################################################
favicon_routes_string = ""
favicon_head_string = ""
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

print("  --  Generating open graph resources") ##########################################################################
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
try:
    if not os.path.isfile(os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))):
        raise Warning("Favicon template not found, skipping open graph resource generation")
    favicon_tpl = os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))
    favicon_path = os.path.join(args.path, "www/static/favicon")
    if not os.path.isdir(favicon_path):
        os.makedirs(favicon_path)
    os.chdir(favicon_path)
    subprocess.call(["inkscape", "-z", "-e", "favicon-300x300.png", "-w", "300", "-h", "300", favicon_tpl])
    og_head_string = og_head_string.replace('<meta property="open_graph_image">', og_image_string)
except Warning as warning:
    print(warning)
except Exception as e:
    fatal_exception(e, "Failed to generate open graph resources")

print("  --  Generating stylesheets") ###################################################################################
css_head_string = ""
try:
    os.chdir(os.path.join(SCRIPT_DIR, "dev/sass"))
    os.makedirs(os.path.join(args.path, "www/static/css"))
    stylesheets = []
    with open('_all.scss', 'w') as f:
        import_array = []
        for root, dirs, files in os.walk(os.getcwd()):
            # uncomment if you want to pick and choose which partials to include 
            #if 'partials' in dirs: dirs.remove('partials')
            for file in files:
                directory = os.path.relpath(root, os.getcwd())
                if directory == '.':
                    stylesheets.append(file)
                    continue
                if not file.startswith('~') and os.path.splitext(file)[-1].lower() in ['.scss', '.sass']:
                    import_string = '@import "{}";\n'.format(os.path.join(directory, file).replace('\\', '/'))
                    if re.match(r'.*mixins?$', os.path.splitext(file)[0].lower()) or directory == 'modules':
                        import_array.insert(0, import_string) #mixins and variables are imported first
                    else:
                        import_array.append(import_string)
        for string in import_array:
            f.write(string)
    #TODO: add support for page specific stylesheets
    stylesheets = [ os.path.splitext(x)[0] for x in stylesheets ]
    if '_all' in stylesheets: stylesheets.remove('_all')
    sass_path = os.path.join(os.path.relpath(args.path, os.getcwd()), "www/static/css").replace('\\', '/')
    if args.deploy:
        for name in stylesheets:
            subprocess.call("sass {0}.scss {1}/{0}.min.css --style compressed".format(name, sass_path), shell=True)
            css_head_string += "    <link href=\"{}.min.css\" rel=\"stylesheet\" type=\"text/css\">\n".format(name)
        os.remove("_all.scss")
        if os.path.isdir(".sass-cache"):
            shutil.rmtree(".sass-cache")
    else:
        WATCH_SASS_SCRIPT.populate('watch.py')
        for name in stylesheets:
            if (os.name == 'nt'):
                subprocess.Popen([sys.executable, 'watch.py', name, sass_path], 
                    creationflags = subprocess.CREATE_NEW_CONSOLE )
            else:
                subprocess.Popen([sys.executable, 'watch.py', name, sass_path])
            css_head_string += "    <link href=\"{}.css\" rel=\"stylesheet\" type=\"text/css\">\n".format(name)
except Exception as e:
    fatal_exception(e, "Could not generate stylesheets")

print("  --  Generating javascript resources") ##########################################################################
try: #TODO: Implement
    pass
except Exception as e:
    fatal_exception(e, "Could not generate javascript files")

print("  --  Generating head template") #################################################################################
try:
    os.chdir(os.path.join(args.path, "www/views"))
    with open('~head.tpl', 'r') as f:
        head_string = f.read()
    if favicon_head_string:
        head_string = head_string.replace('<meta name="favicon_elements">', 
            '\n$wh{Favicon Resources}\n${favicon_elements}')
    if og_head_string:
        head_string = head_string.replace('<meta name="open_graph">', 
            '\n$wh{Open Graph}\n${open_graph}')
    if css_head_string:
        head_string = head_string.replace('<meta name="stylesheets">', 
            '\n$wh{Style Sheets}\n${stylesheets}')
    MyTemplate(head_string).populate('~head.tpl', 
        favicon_elements=favicon_head_string,
        open_graph=og_head_string,
        stylesheets=css_head_string )
except Exception as e:
    fatal_exception(e, "Could not generate head template")

print("  --  Generating app.py file") ###################################################################################
try:
    api_routes_string = ""
    os.chdir(os.path.join(SCRIPT_DIR, "dev/py"))
    with open('routes.py', 'r') as f:
        api_routes_string = "\n" + f.read()

    os.chdir(os.path.join(args.path, "www"))
    APP_PY_TEMPLATE.populate('app.py', 
        doc_string="docstring for {}".format(PROJECT_NAME),
        main_routes=main_routes_string,
        api_routes=api_routes_string,
        favicon_routes=favicon_routes_string,
        static_routes=static_routes_string )
except Exception as e:
    fatal_exception(e)



print("""> \
Executing development scripts""" )

if args.deploy:
    print("  --  Zipping website folder") ###############################################################################
    try:
        os.chdir(args.path)
        with zipfile.ZipFile('www.zip', 'w') as zip_file:
            for root, dirs, files in os.walk(os.path.join(os.getcwd(), 'www')):
                rel_path = os.path.relpath(root, os.getcwd())
                for file in files:
                    zip_file.write(os.path.join(rel_path, file))
        shutil.rmtree('www')
    except Exception as e:
        fatal_exception(e, "Could not zip website folder")
    import time
    time.sleep(10)
    print("Script complete")
    sys.exit(0)

print("  --  Launching server") #########################################################################################
try:
    os.chdir(os.path.join(args.path, "www"))
    if (os.name == 'nt'):
        subprocess.Popen([sys.executable, 'app.py'], creationflags = subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen([sys.executable, 'app.py'])
except Exception as e:
    fatal_exception(e, "Could not launch server")
