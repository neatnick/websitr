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
import re, shutil
import argparse

# Command Line Interface
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="Build stuff")
parser.add_argument("-p", "--path", 
    type=str,
    default=tempfile.gettempdir(),
    help="the path to the desired location of the generated site")
args = parser.parse_args()


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
            shutil.rmtree(os.path.join(args.path, 'wwww'))
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


def get_route(path, method_name, return_stmt, method="route", arg=""):
    return "@{}('{}')\ndef {}({}):\n\treturn {}\n\n".format(method, path, method_name, arg, return_stmt)


def get_template_route(path, template):
    return get_route(path, 
        "load_{}".format(template.split(".")[0].replace("-","_")), #might need more to be safe
        "template('{}')".format(template) )


def get_static_route(pattern, method, file, root, arg=""):
    return get_route("/{}".format(pattern),
        method, "static_file({}, root='{}')".format(file, root),
        'get', arg)


def get_general_static_route(pattern, method, root):
    return get_static_route(pattern, method,
        'filename', root, 'filename')


def get_misc_static_route(file, root):
    return get_static_route(file, file.split(".")[0],
        "'{}'".format(file), root)


def get_main_route(route):
    delimiter = '\\' if os.name == 'nt' else '/'
    path_array = route.split(delimiter)
    path_array[-1] = path_array[-1][:-4]
    return get_template_route("/{}".format('/'.join(path_array)), path_array[-1])



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
    with open("app.py", 'w') as f:
        f.write("from bottle import run, route, request   \n"
              + "from bottle import static_file, template \n"
              + "import argparse                      \n\n\n" )
        
        description = "Run server for {}".format(PROJECT_NAME) # change for custom description
        f.write("##### Command Line Interface ######################################################################\n"
              + "parser = argparse.ArgumentParser(                                                                  \n"
              +   "\tformatter_class=argparse.ArgumentDefaultsHelpFormatter,                                        \n"
              +   "\tdescription='" + description + "' )                                                            \n"
              + "parser.add_argument('ip',                                                                          \n"
              +   "\ttype=str,                                                                                      \n" 
              +   "\tmetavar='IP',                                                                                  \n"
              +   "\tnargs='?',                                                                                     \n" 
              +   "\tdefault='127.0.0.1',                                                                           \n"
              +   "\thelp='the ip the server will run on' )                                                         \n"     
              + "parser.add_argument('port',                                                                        \n"
              +   "\ttype=int,                                                                                      \n" 
              +   "\tmetavar='PORT',                                                                                \n"
              +   "\tnargs='?',                                                                                     \n" 
              +   "\tdefault='8081',                                                                                \n"
              +   "\thelp='the port the server will run on' )                                                       \n" 
              + "parser.add_argument('-d', '--deploy',                                                              \n"
              +   "\taction='store_true',                                                                           \n" 
              +   "\thelp='run server for deployment' )                                                             \n"
              + "args = parser.parse_args()                                                                     \n\n\n" )
        f.write("##### Main Site Routes ############################################################################\n"
              + get_template_route('/', 'index')                                                                        )
        for route in main_routes:
            f.write(get_main_route(route))
        f.write("\n")
        f.write("##### Static Routes ###############################################################################\n")
        for route in misc_routes:
            f.write(get_misc_static_route(route, "static"))
        f.write("# Font Routes                                                                                      \n"
              + get_general_static_route('fonts/<filepath:path>', 'fonts', 'static/fonts') )
        f.write("# Favicon Routes                                                                                   \n"
              + get_general_static_route('favicon/<filepath:path>', 'favicon', 'static/favicon') )
        f.write("# General Routes                                                                                   \n"
              + get_general_static_route('<filename:re:.*\.(jpg|png|gif|svg)>', 'images', 'static/img')
              + get_general_static_route('<filename:re:.*\.css>', 'stylesheets', 'static/css')
              + get_general_static_route('<filename:re:.*\.js>', 'javascript', 'static/js') )
        #TODO: api routes
        f.write("if args.deploy:                                                                                    \n"
              +   "\trun(host=args.ip, port=args.port, server='cherrypy') #deployment                               \n"
              + "else:                                                                                              \n"
              +   "\trun(host=args.ip, port=args.port, debug=True, reloader=True) #development                      \n" )
except Exception as e:
        fatal_exception(e)
