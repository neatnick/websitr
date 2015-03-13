import os, sys 
import time, subprocess
import urllib.request, shutil
import errno, re
import argparse

# Requirements:
#  Python3, Sass, Git
#

# Command Line Interface
parser = argparse.ArgumentParser(
    prog="SITE_BUILDER", 
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="Build Nick\'s prefered default project starting point for new websites."   +
    " The project will precompile sass files for css, and use bottle as the web framework." +
    " It will be geared towards deployment on a cherrypy server using a nginx reverse proxy.")
parser.add_argument("name", 
    type=str,
    metavar="NAME",
    nargs="?",
    default="untitled",
    help="the name of the project for the new website")
parser.add_argument("-p", "--path", 
    type=str,
    help="the path to the desired location of the new project")
args = parser.parse_args()


SCRIPT_DIR     = os.getcwd()
RE_USER_ACCEPT = re.compile(r'y(?:es|up|eah)?$', re.IGNORECASE)
RE_USER_DENY   = re.compile(r'n(?:o|ope|ada)?$', re.IGNORECASE)


def fatal_exception(exception, message=""): #TODO: cleanup after failure?
    print("*******SCRIPT FAILED*******")
    if (message):
        print(message)
    print("Exception: ", exception)
    sys.exit(1)


def non_fatal_exception(exception, message):
    while (1):
        response = input(message)
        if (RE_USER_ACCEPT.match(response)):
            return
        if (RE_USER_DENY.match(response)):
            fatal_exception(exception, "Script canceled by user")


def populate_static_resource(resources):
    for resource_name in resources:
        src_path = os.path.join(SCRIPT_DIR, "static/{}".format(resource_name))
        try:
            shutil.copy(src_path, resource_name)
        except Exception as exception:
            fatal_exception(exception, 
                "Could not populate resource: {}".format(resource_name))



print("Create folder for new project")
if not (args.path) is None:
    try:
        os.chdir(args.path)
    except OSError as exception:
        fatal_exception(exception, "Invalid path provided")

try:
    os.makedirs(args.name)
except OSError as exception:
    if (exception.errno == errno.EEXIST):
        non_fatal_exception(exception,
            "Folder already exists at \'{}\' with the desired project name.".format(os.getcwd()) +
            " Do you wish to proceed (script will use this folder for the project)? [yes/no]")
    else:
        fatal_exception(exception, "Could not create project folder")
os.chdir(args.name)


print("Building out directory structure for the project")
try:
    os.makedirs("sass/resources")
    os.makedirs("www/static/css")
    os.makedirs("www/static/favicon")
    os.makedirs("www/static/fonts")
    os.makedirs("www/static/img")
    os.makedirs("www/static/js")
    os.makedirs("www/views")
except OSError as exception:
    fatal_exception(exception, "Could not build project directory structure")


print("Creating sass scripts and pulling in resources")
try:
    os.chdir('sass')
    populate_static_resource(['base.scss', 'watch.py'])
    with open('styles.scss', 'w') as f:
        f.write('@import \"base\";\n\n')
except Exception as exception:
    fatal_exception(exception, "Could not build sass project")

try:
    os.chdir('resources')
    populate_static_resource(['resources.json', 'resources.py'])

    # exec(open("resources.py", 'r').read())
    subprocess.Popen([sys.executable, 'resources.py'], creationflags = subprocess.CREATE_NEW_CONSOLE)
except Exception as exception:
    fatal_exception(exception, "Could not pull in sass resources")


print("Creating bottle project")
try:
    os.chdir('../../www')
    with open('app.py', 'w') as f:
        f.write('test')
except Exception as exception:
    fatal_exception(exception, "Could not build bottle project")

print(args.name)

