
"""
Build Nick's prefered default project starting point for new websites. The 
project will precompile sass files for css, and use bottle as the web 
framework. It will be geared towards deployment on a cherrypy server using a 
nginx reverse proxy.

Copyright (c) 2015, Nick Balboni.
License: BSD (see LICENSE for details)
"""

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
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("name", 
    type=str,
    metavar="NAME",
    nargs="?",
    default="untitled",
    help="the name of the project for the new website." )
parser.add_argument("-p", "--path", 
    type=str,
    default=os.getcwd(),
    help="the path to the desired location of the new project." )
parser.add_argument("-f", "--favicon", 
    type=str,
    help="location of image file to be used as the favicon for the project. If an absolute path is "
    "not given, location will be assumed to be relative to the location of this script. It is "
    "recommended to provide a 300px by 300px png file for use here." )
parser.add_argument("-r", "--resources", 
    type=str,
    nargs='+',
    help="locations of any additional resources to be added to the project. If an absolute path is "
    "not given, location will be assumed to be relative to the location of this script." )
args = parser.parse_args()


SCRIPT_DIR     = os.getcwd()
PROJECT_DIR    = os.path.join(args.path, args.name)
RE_USER_ACCEPT = re.compile(r'y(?:es|up|eah)?$', re.IGNORECASE)
RE_USER_DENY   = re.compile(r'n(?:o|ope|ada)?$', re.IGNORECASE)


def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if (message): print(message)
    print("Exception: ", exception)
    if (cleanup):
        try:
            os.chdir(args.path)
            shutil.rmtree(args.name)
        except Exception as e:
            print(e)
    sys.exit(1)


def non_fatal_exception(exception, message, *args):
    while (1):
        response = input(message)
        if (RE_USER_ACCEPT.match(response)):
            return
        if (RE_USER_DENY.match(response)):
            fatal_exception(exception, "Script canceled by user", *args)


def populate_static_resource(*args):
    for resource_name in args:
        src_path = os.path.join(SCRIPT_DIR, "static/{}".format(resource_name))
        try:
            shutil.copy(src_path, resource_name)
        except Exception as exception:
            fatal_exception(exception, 
                "Could not populate resource: {}".format(resource_name))



print("Creating folder for new project")
try:
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

try:
    os.makedirs(args.name)
except OSError as exception:
    if (exception.errno == errno.EEXIST): #TODO: add ability to update an already existing project
        non_fatal_exception(exception,
            "Folder already exists at \'{}\' with the desired project name.".format(os.getcwd()) +
            " Do you wish to proceed (script will use this folder for the project)? [yes/no]", False)
    else:
        fatal_exception(exception, "Could not create project folder", False)


print("Building out directory structure for the project")
os.chdir(PROJECT_DIR)
try:
    populate_static_resource('build.py') #probably move this to where you call it
    os.makedirs("dev/coffee")
    os.makedirs("dev/sass/resources")
    os.makedirs("dev/views")
    os.makedirs("res/font")
    os.makedirs("res/img")
    os.makedirs("res/static")
except OSError as exception:
    fatal_exception(exception, "Could not build project directory structure")


print("Creating sass scripts and pulling in resources")
os.chdir(PROJECT_DIR)
try:
    os.chdir('dev/sass')
    populate_static_resource('base.scss', 'watch.py')
    with open('styles.scss', 'w') as f:
        f.write('@import \"base\";\n\n')
except Exception as exception:
    fatal_exception(exception, "Could not build sass project")

try:
    os.chdir('resources')
    populate_static_resource('resources.json', 'resources.py')

    # exec(open("resources.py", 'r').read())
    subprocess.Popen([sys.executable, 'resources.py'], creationflags = subprocess.CREATE_NEW_CONSOLE)
except Exception as exception:
    fatal_exception(exception, "Could not pull in sass resources")


print("Creating default views for bottle project")
os.chdir(PROJECT_DIR)
try:
    os.chdir('dev/views')
    with open('~head.tpl', 'w') as f:
        f.write('<head>\n</head>')
    with open('index.tpl', 'w') as f: #TODO: templating
        f.write('<!DOCTYPE html>\n<html lang="en">\n% include(\'~head.tpl\', title=\'{}\', description=\'{}\')\n\t<body></body>\n</html>')
except Exception as exception:
    fatal_exception(exception, "Could not build default views")


print("Populating project resources")
os.chdir(PROJECT_DIR)
try:
    os.chdir('res')
except Exception as exception:
    fatal_exception(exception, "Could not populate project resources")

try:
    os.chdir('static')
    with open('robots.txt', 'w') as f:
        f.write('User-agent: *\nDisallow:')
except Exception as exception:
    fatal_exception(exception, "Could not create default robots.txt")

