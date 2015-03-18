
"""
Build Nick's prefered default project starting point for new websites. The 
project will precompile sass files for css, and use bottle as the web 
framework. It will be geared towards deployment on a cherrypy server using a 
nginx reverse proxy.

Requirements:
    - Python 3.x
    - CoffeeScript
    - Sass
    - Git

Copyright (c) 2015, Nick Balboni.
License: BSD (see LICENSE for details)
"""

import os, sys 
import time, subprocess
import urllib.request, shutil
from string import Template
import errno, re
import argparse



########################################################################################################################
##### Command Line Interface ###########################################################################################
########################################################################################################################

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



########################################################################################################################
##### Templates ########################################################################################################
########################################################################################################################

BASE_SASS_TEMPLATE = Template(""""
@import "./resources/resources";

$main-font-stack: 'Lato', sans-serif;

body.main {
    @include fixpos(0);
    margin: 0;
    padding: 0;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    font-family: $main-font-stack; }""" )


STYLES_SASS_TEMPLATE = Template("""
@import "base";

""" )


WATCH_SASS_TEMPLATE = Template("""
from subprocess import call

# watch styles.scss
# - all other sass files flow into this one so this is all we need
call("sass --watch styles.scss:../www/static/css/styles.css", shell=True)""" )


RESOURCES_SASS_TEMPLATE = Template("""
import urllib.request
import json, shutil, os


def populate_resource(resource_name, resource_url):
    try:
        with urllib.request.urlopen(resource_url) as response, open(resource_name, 'wb') as f:
            shutil.copyfileobj(response, f)
    except Exception as e:
        message = "Could not populate resource" if not (os.path.isfile(resource_name)) else "Unable to update resource"
        print("{}: {}\n  from url: {}\nException: {}".format(message, resource_name, resource_url, e))
    return os.path.isfile(resource_name)


with open('resources.json', 'r') as f_data, open('resources.scss', 'w') as f_out:
    resources = json.loads(f_data.read())
    for resource in resources:
        if not (populate_resource(resource['name'], resource['url'])):
            f_out.write("//")
        f_out.write("@import \"{}\";\n".format(resource['name']))""" )


RESOURCES_JSON_TEMPLATE = Template("""
[
    {
        "name": "flex-box_mixins.scss",
        "url": "https://raw.githubusercontent.com/mastastealth/sass-flex-mixin/master/flex.scss"
    },
    {
        "name": "media-query_mixins.scss",
        "url": "https://raw.githubusercontent.com/paranoida/sass-mediaqueries/master/_media-queries.scss"
    },
    {
        "name": "general_mixins.scss",
        "url": "https://raw.githubusercontent.com/SwankSwashbucklers/some-sassy-mixins/master/mixins.scss"
    }
]""" )



HEAD_TEMPLATE = Template("""
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>{{title}}</title>

    <meta name="keywords" content="appswithstyle, apps with style, iOS development, developers, awesome things">
    <meta name="description" content="{{description}}">
    <meta name="author" content="Nick Balboni">

<!-- ***** Favicon Stuff ******************************************************************************************* -->
    <link rel="shortcut icon" href="favicon.ico">
    <link rel="apple-touch-icon" sizes="57x57" href="/static/favicon/apple-touch-icon-57x57.png?v=2">
    <link rel="apple-touch-icon" sizes="114x114" href="/static/favicon/apple-touch-icon-114x114.png?v=2">
    <link rel="apple-touch-icon" sizes="72x72" href="/static/favicon/apple-touch-icon-72x72.png?v=2">
    <link rel="apple-touch-icon" sizes="144x144" href="/static/favicon/apple-touch-icon-144x144.png?v=2">
    <link rel="apple-touch-icon" sizes="60x60" href="/static/favicon/apple-touch-icon-60x60.png?v=2">
    <link rel="apple-touch-icon" sizes="120x120" href="/static/favicon/apple-touch-icon-120x120.png?v=2">
    <link rel="apple-touch-icon" sizes="76x76" href="/static/favicon/apple-touch-icon-76x76.png?v=2">
    <link rel="apple-touch-icon" sizes="152x152" href="/static/favicon/apple-touch-icon-152x152.png?v=2">
    <link rel="icon" type="image/png" href="/static/favicon/favicon-196x196.png?v=2" sizes="196x196">
    <link rel="icon" type="image/png" href="/static/favicon/favicon-160x160.png?v=2" sizes="160x160">
    <link rel="icon" type="image/png" href="/static/favicon/favicon-96x96.png?v=2" sizes="96x96">
    <link rel="icon" type="image/png" href="/static/favicon/favicon-16x16.png?v=2" sizes="16x16">
    <link rel="icon" type="image/png" href="/static/favicon/favicon-32x32.png?v=2" sizes="32x32">
    <meta name="msapplication-TileColor" content="#2d89ef">
    <meta name="msapplication-TileImage" content="/static/favicon/mstile-144x144.png?v=2">
    <meta name="msapplication-config" content="/static/favicon/browserconfig.xml">

<!-- ***** Social Media ******************************************************************************************** -->
    <meta property="og:url" content="http://appswithstyle.net/">
    <meta property="og:type" content="website">
    <meta property="og:title" content="appsWithStyle | iOS App Developer Team">
    <meta property="og:image:type" content="image/png">
    <meta property="og:image:width" content="300">
    <meta property="og:image:height" content="300">
    <meta property="og:image" content="http://appswithstyle.net/logo-small_300x300.png">
    <meta property="og:image:url" content="http://appswithstyle.net/logo-small_300x300.png">
    <meta property="og:description" content="{{description}}">
    <!-- Here you go facebook -->
    <meta property="fb:admins" content="nick.balboni.92">

<!-- ****** jQuery ************************************************************************************************* -->
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>

<!-- ****** Style Sheets ******************************************************************************************* -->
    <link href="styles.css" rel="stylesheet" type="text/css">
    <!-- Fonts -->
    <link href="http://fonts.googleapis.com/css?family=Lato:300,400,900" rel="stylesheet" type="text/css">
    <link href="fonts.css" rel="stylesheet" type="text/css">
</head>""" )


INDEX_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
% include('~head.tpl', title='$title', description='$description')
    <body>
    </body>
</html>""" )


ROBOTS_TEMPLATE = Template("""
User-agent: *
Disallow:""" )



########################################################################################################################
##### Script Body ######################################################################################################
########################################################################################################################

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


def populate_template(filename, template, **kargs):
    try:
        with open(filename, 'w') as f:
            content = template.safe_substitute(kargs) #populate template
            content = content[1:] #to remove leading newline 
            f.write(content) #write data to the new file
    except Exception as exception:
        raise exception #test this



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
    populate_template('base.scss', BASE_SASS_TEMPLATE)
    populate_template('styles.scss', STYLES_SASS_TEMPLATE)
    populate_template('watch.py', WATCH_SASS_TEMPLATE)
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
    populate_template('~head.tpl', HEAD_TEMPLATE, title=args.name, description="Welcome to {}!".format(args.name))
    populate_template('index.tpl', INDEX_TEMPLATE)
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
    populate_template('robots.txt', ROBOTS_TEMPLATE)
except Exception as exception:
    fatal_exception(exception, "Could not create default robots.txt")


print("Generating website in temporary directory")
os.chdir(PROJECT_DIR)
try:
    pass
    #populate_static_resource('build.py')
except Exception as exception:
    fatal_exception(exception, "Unable to generate website")