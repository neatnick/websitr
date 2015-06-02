"""
files or directories with a ! in front of them will not be copied into the project
files or directories with a ~ in front of them will not have a route added for them

styles.scss will be added to all templates and any .scss file with the same name as an existing
template will be added to that template

use jquery to include js partials, if js file exists with the same name as an existing template
jquery and that js file will be appended to the body of that template

browsehappy code is added to the top of every template

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


################################################################################
##### Command Line Interface ###################################################
################################################################################

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("-p", "--path", 
    type=str,
    help="the path to the desired location of the generated site")
parser.add_argument("-d", "--deploy",
    action="store_true",
    help="package site for movement to deployment server. Default path is the current working "
    "directory, but the path flag will override that value" )
parser.add_argument("-r", "--reuse",
    action="store_true",
    help="if an already build website exists at the targeted path, attempt to reuse already "
    "present resources (i.e. images, favicon elements and other static resources)" )
args = parser.parse_args()

if args.path is None:
    if args.deploy:
        args.path = os.getcwd()
    else:
        args.path = tempfile.gettempdir()

# TODO: move jQuery version, whether or not to include jQuery, whether to autoadd all sass partials and other variables
# up here, eventually make them into arguments for the script? (maybe store in a config file instead)
# (actually why waste the space? this file should be customizable on a per project basis, 
#    like the sass update.py file is <- make note of this in docs)



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
    def populate(template, filename, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                kwargs[key] = "\n".join(
                    [ t[0].safe_substitute(**t[1]) for t in value ]
                )
            elif isinstance(value, str):
                pass
        try:
            with open(filename, 'w') as f:
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
@route('/')
def load_root():
    return template('index', request=request, template='index')
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


MAIN_ROUTE_TEMPLATE = Template("""\
@route('/${path}')
def ${method_name}():
    return template('${template}', request=request, template='${template}')
""" )


STATIC_ROUTE_TEMPLATE = Template("""\
@get('/${path}')
def ${method_name}():
    return static_file('${file}', root='${root}')
""" )


WATCH_SASS_SCRIPT = Template("""\
import subprocess, sys, os, shutil

command = "sass --watch"
for x in range(2, len(sys.argv)):
    command += " {1}.scss:{0}/{1}.css".format(sys.argv[1], sys.argv[x])
p = subprocess.Popen(command, shell=True)
try:
    while True:
        pass
except KeyboardInterrupt:
    p.kill()
    os.remove("_all.scss")
    if os.path.isdir(".sass-cache"):
        shutil.rmtree(".sass-cache")
    os.remove(sys.argv[0])""" )


################################################################################
##### Script Body ##############################################################
################################################################################

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
                    if not os.path.isfile(filename): #added for the reuse flag
                        shutil.copy(os.path.join(root, filename), filename)
                    if not filename.startswith('~'):
                        routes.append(os.path.normpath(os.path.join(os.path.relpath(root, src_path), filename)))
        return routes
    except Exception as exception:
        raise exception


print("""> \
Creating site directory""" )

print("  --  Verifying path") ##################################################
try:
    args.path = os.path.abspath(args.path)
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

print("  --  Searching for already present resources") #########################
try:
    if os.path.isdir('www'):
        if args.reuse:
            os.chdir('www')
            if os.path.isfile('app.py'): os.remove('app.py')
            if os.path.isfile('bottle.py'): os.remove('bottle.py')
            if os.path.isdir('views'): shutil.rmtree('views')
            if os.path.isdir('static'): 
                os.chdir('static')
                if os.path.isdir('css'): shutil.rmtree('css')
                if os.path.isdir('js'): shutil.rmtree('js')
        else:
            shutil.rmtree('www')
    elif args.reuse:
        raise Warning("Reuse flag indicated but no previous site was found at path")
except Warning as warning:
    print(warning)
except Exception as exception: 
    fatal_exception(exception, "Unable to clean previous site", False)



print("""> \
Importing and generating site resources""" )

print("  --  Importing image and font resources") ##############################
try: # TODO: note fact that all image files and font resources have to have unique names
    img_routes = get_routes_for_directory("res/img", "www/static/img")
    font_routes = get_routes_for_directory("res/font", "www/static/font")
except Exception as e:
    fatal_exception(e, "Failed to import image and font resources")

print("  --  Importing miscellaneous static resources") ########################
static_routes_string = ""
try:
    for route in get_routes_for_directory("res/static", "www/static"):
        static_routes_string += "\n" + STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=route, method_name=route.split(".")[0],
            file=route, root='static' )
    static_routes_string = static_routes_string[:-1]
except Exception as e:
    fatal_exception(e)

print("  --  Importing bottle framework") ######################################
try:
    os.chdir(os.path.join(args.path, "www"))
    bottle_url = "https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py"
    with urllib.request.urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
        shutil.copyfileobj(response, f)
except Exception as e:
    fatal_exception(e, "Failed to import bottle.py")

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

print("  --  Generating open graph resources") #################################
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
try: # TODO: route needs to be created
    favicon_tpl = os.path.join(SCRIPT_DIR, os.path.normpath("res/favicon.svg"))
    favicon_res_path = os.path.join(args.path, "www/static/favicon")
    if args.reuse and os.path.isdir(favicon_res_path): # TODO: head string and route still need to be created
        raise Warning("Reuse flag enabled and previous resources were found, skipping open graph resource generation")
    if not os.path.isfile(favicon_tpl):
        raise Warning("Favicon template not found, skipping open graph resource generation")
    if not os.path.isdir(favicon_res_path):
        os.makedirs(favicon_res_path)
    os.chdir(favicon_res_path)
    subprocess.call(["inkscape", "-z", "-e", "favicon-300x300.png", "-w", "300", "-h", "300", favicon_tpl])
    og_head_string = og_head_string.replace('<meta property="open_graph_image">', og_image_string)
except Warning as warning:
    print(warning)
except Exception as e:
    fatal_exception(e, "Failed to generate open graph resources")

print("  --  Generating stylesheets") ##########################################
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
                    if os.path.splitext(file)[-1].lower() in ['.scss', '.sass']:
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

print("  --  Generating javascript resources") #################################
try: # TODO: Implement
    os.chdir(os.path.join(SCRIPT_DIR, "dev/coffee"))
    os.makedirs(os.path.join(args.path, "www/static/js"))
    jquery_version = "2.1.3"
    jquery_file = "jquery-{}.min.js".format(jquery_version)
    jquery_url = "http://code.jquery.com/{}".format(jquery_file)
    jquery_path = os.path.join(args.path, "www/static/js", jquery_file)
    jquery_head = ""
    with urllib.request.urlopen(jquery_url) as response, open(jquery_path, 'wb') as f:
        shutil.copyfileobj(response, f)
        jquery_head = '\n    <script>window.jQuery || document.write(\'<script src="{}"><\\/script>\')</script>'
        jquery_head = jquery_head.format(jquery_file)
    #google_hosted_tag = '\n    <script src="https://ajax.googleapis.com/ajax/libs/{}"></script>'
    #head_string = head_string.replace('<meta name="jquery">', 
    #    '\n$wh{jQuery}' + google_hosted_tag.format('jquery/{}/jquery.min.js'.format(jquery_version)) + jquery_head )
    
    # TODO: add google analytics beneath js
except Exception as e:
    fatal_exception(e, "Could not generate javascript files")

print("  --  Importing views") #################################################
main_routes_string = ""
try: # TODO: if dev mode watch this files for changes and update
    for route in get_routes_for_directory("dev/views", "www/views"):
        delimiter = '\\' if os.name == 'nt' else '/'
        path_array = route.split(delimiter)
        path_array[-1] = path_array[-1][:-4]
        main_routes_string += "\n" + MAIN_ROUTE_TEMPLATE.safe_substitute(
            path='/'.join(path_array), 
            method_name="load_{}".format(path_array[-1].split(".")[0].replace("-","_")), 
            template=path_array[-1] )
    main_routes_string = main_routes_string[:-1]
    # TODO: add browsehappy to the top of every template with regex replace
except Exception as e:
    fatal_exception(e)

print("  --  Generating head template") ########################################
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

print("  --  Generating app.py file") ##########################################
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
    print("  --  Zipping website folder") ######################################
    try:
        os.chdir(args.path)
        if os.path.isfile('www.zip'):
            os.remove('www.zip')
        with zipfile.ZipFile('www.zip', 'w') as zip_file:
            for root, dirs, files in os.walk(os.path.join(os.getcwd(), 'www')):
                rel_path = os.path.relpath(root, os.getcwd())
                for file in files:
                    zip_file.write(os.path.join(rel_path, file))
        shutil.rmtree('www')
    except Exception as e:
        fatal_exception(e, "Could not zip website folder")
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
