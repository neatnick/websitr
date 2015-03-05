import os, sys
import errno, re
import argparse

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
    f = open('resources.scss', 'w')
    f.write('@import \"./resources/mixins\";\n'
          + '@import \"./resources/flex\";\n'
          + '@import \"./resources/_media-queries\";' )
    f = open('base.scss', 'w')
    f.write('@import \"resources\";\n\n'
          + '$main-font-stack: \'Lato\', sans-serif;\n\n'
          + 'body.main {\n'
          +   '\t@include fixpos(0);\n'
          +   '\tmargin: 0;\n'
          +   '\tpadding: 0;\n'
          +   '\tfont-size: 16px;\n'
          +   '\t-webkit-font-smoothing: antialiased;\n'
          +   '\tfont-family: $main-font-stack; }\n' )
    f = open('styles.scss', 'w')
    f.write('@import \"base\";\n\n')
    f = open('watch.py', 'w')
    f.write('from subprocess import call\n\n'
          + '# watch styles.scss\n'
          + '# - all other sass files flow into this one so this is all we need\n'
          + 'call(\"sass --watch styles.scss:../www/static/css/styles.css\", shell=True)')
except Exception as exception:
    fatal_exception(exception, "Could not build sass project")

try:
    pass
except Exception as exception:
    fatal_exception(exception, "Could not pull in sass resources")

print(args.name)

