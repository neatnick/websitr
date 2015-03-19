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
from string import Template
import re, shutil
import argparse



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

APP_PY_TEMPLATE = Template("""
${doc_string}
from bottle import run, route, request   
from bottle import static_file, template 
import argparse                      

${commandline_header}
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )                                
parser.add_argument('-d', '--deploy',
    action='store_true' 
    help='Run server for deployment' )       
parser.add_argument('-l', '--local', 
    help='Run server for development testing on a local network' ) 
args = parser.parse_args()                                                                     

${main_routes_header}
@route('/')
def load_index():
    return template('index')

${main_routes}

${static_routes_header}
${static_routes}
${font_routes_header}
@get('/fonts/<filepath:path>')
def fonts(filename):
    return static_file(filename, root='static/fonts')

${favicon_routes_header}
@get('/favicon/<filepath:path>')
def favicon(filename):
    return static_file(filename, root='static/favicon')

${general_routes_header}
@get('/<filename:re:.*\.(jpg|png|gif|svg)>')
def images(filename):
    return static_file(filename, root='static/img')

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root='static/css')

@get('/<filename:re:.*\.js>')
def javascript(filename):
    return static_file(filename, root='static/js')

${run_server_header}
if args.deploy:
    run(host=args.ip, port=args.port, server='cherrypy') #deployment
else:
    run(host=args.ip, port=args.port, debug=True, reloader=True) #development """ )


MAIN_ROUTE_TEMPLATE = Template("""
@route('/${path}')
def ${method_name}():
    return template('${template}')""" )


STATIC_ROUTE_TEMPLATE = Template("""
@get('/${path}')
def ${method_name}():
    return static_file('${file}', root='${root}')""" )


########################################################################################################################
##### Script Body ######################################################################################################
########################################################################################################################

SCRIPT_DIR      = os.getcwd()
PROJECT_NAME    = os.path.relpath(SCRIPT_DIR, "..")
RE_NOT_INCLUDED = re.compile(r'^!')
RE_NOT_ADDED    = re.compile(r'^~')


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


def get_routes_for_directory(directory): #TODO: do not include directories like .DS_STORE
    try:
        routes = []
        src_path = os.path.join(SCRIPT_DIR, directory)
        for root, dirs, files in os.walk(src_path):
            for dirname in dirs:
                if (RE_NOT_INCLUDED.match(dirname)):
                    dirs.remove(dirname)
            for filename in files:
                if not (RE_NOT_INCLUDED.match(filename)):
                    shutil.copy(os.path.join(root, filename), filename)
                    if not (RE_NOT_ADDED.match(filename)):
                        routes.append(os.path.normpath(os.path.join(os.path.relpath(root, src_path), filename)))
        return routes
    except Exception as e:
        fatal_exception(e)


def get_main_header(header):
    header = ('#'*5) + ' ' + header.upper() + ' '
    header += ('#'*(121-len(header)))
    return ('#'*121) + '\n' + header + "\n" + ('#'*121)


def get_secondary_header(header):
    header = ('#'*3) + ' ' + header + ' '
    header += ('#'*(121-len(header)))
    return header



try:
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

try:
    os.mkdir("www")
    os.chdir("www")

    os.mkdir("views")
    os.chdir("views")
    main_routes = get_routes_for_directory("dev/views")
    os.chdir("..")

    os.mkdir("static")
    os.chdir("static")
    misc_routes = get_routes_for_directory("res/static")

    os.mkdir("img")
    os.chdir("img")
    img_routes = get_routes_for_directory("res/img")
    os.chdir("..")

    os.mkdir("font")
    os.chdir("font")
    font_routes = get_routes_for_directory("res/font")
    #os.chdir("..")

    #TODO: generate favicon folder with an api call
    #os.mkdir("favicon")
    #os.chdir("favicon")
    #favicon_routes = get_routes_for_directory("static/favicon")
    os.chdir("../..")

    #import bottle into the project
    bottle_url = "https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py"
    with urllib.request.urlopen(bottle_url) as response, open('bottle.py', 'wb') as f:
        shutil.copyfileobj(response, f)

    #generate app.py
    main_routes_string = ""
    for route in main_routes:
        delimiter = '\\' if os.name == 'nt' else '/'
        path_array = route.split(delimiter)
        path_array[-1] = path_array[-1][:-4]
        main_routes_string += MAIN_ROUTE_TEMPLATE.safe_substitute(
            path='/'.join(path_array), 
            method_name="load_{}".format(path_array[-1].split(".")[0].replace("-","_")), 
            template=path_array[-1] )

    static_routes_string = ""
    for route in misc_routes:
        static_routes_string += STATIC_ROUTE_TEMPLATE.safe_substitute(
            path=route,
            method_name=route.split(".")[0],
            file=route,
            root='static' )

    #TODO: api routes
    with open('app.py', 'w') as f:
        content = APP_PY_TEMPLATE.safe_substitute(
            doc_string='"""\ndocstring for {}\n"""'.format(PROJECT_NAME),
            commandline_header=get_main_header("Command Line Interface"),
            main_routes_header=get_main_header("Main Site Routes"),
            main_routes=main_routes_string,
            static_routes_header=get_main_header("Static Routes"),
            static_routes=static_routes_string,
            font_routes_header=get_secondary_header("Font Routes"),
            favicon_routes_header=get_secondary_header("Favicon Routes"),
            general_routes_header=get_secondary_header("General Routes"),
            run_server_header=get_main_header("Run Server") )
        content = content[1:] #to remove leading newline 
        f.write(content) #write data to the new file
except Exception as e:
    fatal_exception(e)