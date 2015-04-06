
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
    - Inkscape

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
    "required to provide a square svg file for use here." )
parser.add_argument("-r", "--resources", 
    type=str,
    nargs='+',
    help="locations of any additional resources to be added to the project. If an absolute path is "
    "not given, location will be assumed to be relative to the location of this script." )
args = parser.parse_args()



########################################################################################################################
##### Templates ########################################################################################################
########################################################################################################################

# template setup
MYTEMPLATE = """\
from string import Template

class MyTemplate(Template):
    def populate(self, filename, **kwargs):
        try:
            with open(filename, 'w') as f:
                f.write(self.sub(**kwargs))
        except Exception as exception:
            raise exception

    def sub(self, **kwargs):
        for key, value in kwargs.items():
            if key.startswith("ph_"):
                kwargs[key] = self.get_primary_header(value)
            if key.startswith("sh_"):
                kwargs[key] = self.get_secondary_header(value)
        return super(MyTemplate, self).safe_substitute(**kwargs)

    def get_primary_header(header):
        header = ('#'*5) + ' ' + header.upper() + ' '
        header += ('#'*(121-len(header)))
        return '\\n\\n' + ('#'*121) + '\\n' + header + "\\n" + ('#'*121)

    def get_secondary_header(header):
        header = ('#'*3) + ' ' + header + ' '
        header += ('#'*(121-len(header)))
        return header"""

with open('templates.py', 'w') as f:
    f.write(MYTEMPLATE)


from templates import MyTemplate

BASE_SASS_TEMPLATE = MyTemplate("""\
@import "./resources/resources";

$main-font-stack: 'Lato', sans-serif;

body.main {
    @include fixpos(0);
    margin: 0;
    padding: 0;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    font-family: $main-font-stack; }""" )


STYLES_SASS_TEMPLATE = MyTemplate("""\
@import "base";

""" )


WATCH_SASS_TEMPLATE = MyTemplate("""\
from subprocess import call

# watch styles.scss
# - all other sass files flow into this one so this is all we need
call("sass --watch styles.scss:../www/static/css/styles.css", shell=True)""" )


RESOURCES_SASS_TEMPLATE = MyTemplate("""\
import urllib.request
import shutil, os


RESOURCES = [ { "name": "_flex-box_mixins.scss",
                "url": "https://raw.githubusercontent.com/mastastealth/sass-flex-mixin/master/_flex.scss" },

              { "name": "_media-query_mixins.scss",
                "url": "https://raw.githubusercontent.com/paranoida/sass-mediaqueries/master/_media-queries.scss" },

              { "name": "_general_mixins.scss",
                "url": "https://raw.githubusercontent.com/SwankSwashbucklers/some-sassy-mixins/master/mixins.scss" } ]


def populate_resource(resource_name, resource_url):
    try:
        with urllib.request.urlopen(resource_url) as response, open(resource_name, 'wb') as f:
            shutil.copyfileobj(response, f)
    except Exception as e:
        message = "Could not populate resource" if not (os.path.isfile(resource_name)) else "Unable to update resource"
        print("{}: {}\\n  from url: {}\\nException: {}".format(message, resource_name, resource_url, e))
    return os.path.isfile(resource_name)


with open('resources.scss', 'w') as f:
    for resource in RESOURCES:
        if not (populate_resource(resource['name'], resource['url'])):
            f.write("//")
        f.write("@import \\"{}\\";\\n".format(resource['name']))""" )



HEAD_TEMPLATE = MyTemplate("""\
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


INDEX_TEMPLATE = MyTemplate("""\
<!DOCTYPE html>
<html lang="en">
% include('~head.tpl', title='$title', description='$description')
    <body>
    </body>
</html>""" )


ROUTES_TEMPLATE = MyTemplate("""\
import textwrap

@route('/', method='POST')
def api():
    if request.POST.get("v") == 'vendetta': 
        return_val = \"""\\
            Evey:  Who are you?
               V:  Who? Who is but the form following the function of what, and what 
                   I am is a man in a mask.
            Evey:  Well I can see that.
               V:  Of course you can. I'm not questioning your powers of observation; 
                   I'm merely remarking upon the paradox of asking a masked man who 
                   he is.
            Evey:  Oh. Right.
               V:  But on this most auspicious of nights, permit me then, in lieu of 
                   the more commonplace sobriquet, to suggest the character of this 
                   dramatis persona.
               V:  Voila! In view, a humble vaudevillian veteran cast vicariously as 
                   both victim and villain by the vicissitudes of Fate. This visage, 
                   no mere veneer of vanity, is a vestige of the vox populi, now 
                   vacant, vanished. However, this valourous visitation of a bygone 
                   vexation stands vivified and has vowed to vanquish these venal and 
                   virulent vermin vanguarding vice and vouchsafing the violently 
                   vicious and voracious violation of volition! The only verdict is 
                   vengeance; a vendetta held as a votive, not in vain, for the value 
                   and veracity of such shall one day vindicate the vigilant and the 
                   virtuous. Verily, this vichyssoise of verbiage veers most verbose, 
                   so let me simply add that it's my very good honour to meet you and 
                   you may call me V.\"""
        return textwrap.dedent(return_val)
    return load_home()""" )


ROBOTS_TEMPLATE = MyTemplate("""\
User-agent: *
Disallow:""" )



########################################################################################################################
##### Script Body ######################################################################################################
########################################################################################################################

SCRIPT_DIR     = os.getcwd()
PROJECT_DIR    = os.path.join(os.path.abspath(args.path), args.name)
RE_USER_ACCEPT = re.compile(r'y(?:es|up|eah)?$', re.IGNORECASE)
RE_USER_DENY   = re.compile(r'n(?:o|ope|ada)?$', re.IGNORECASE)


def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if (message): print(message)
    print("Exception: ", exception)
    os.chdir(args.path)
    os.remove("templates.py")
    if (cleanup):
        try:
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
    args.path = os.path.abspath(args.path)
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
try:
    os.chdir(PROJECT_DIR)
    os.makedirs("dev/coffee")
    os.makedirs("dev/py")
    os.makedirs("dev/sass/resources")
    os.makedirs("dev/views")
    os.makedirs("res/font")
    os.makedirs("res/img")
    os.makedirs("res/static")
except OSError as exception:
    fatal_exception(exception, "Could not build project directory structure")



print("Setting up python resources")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/py'))
    ROUTES_TEMPLATE.populate('routes.py')
except Exception as exception:
    fatal_exception(exception, "Could not create routes file")



print("Creating sass scripts and pulling in resources")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/sass'))
    BASE_SASS_TEMPLATE.populate('base.scss')
    STYLES_SASS_TEMPLATE.populate('styles.scss')
    WATCH_SASS_TEMPLATE.populate('watch.py')
except Exception as exception:
    fatal_exception(exception, "Could not build sass project")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/sass/resources'))
    RESOURCES_SASS_TEMPLATE.populate('resources.py')
    if (os.name == 'nt'):
        # exec(open("resources.py", 'r').read())
        subprocess.Popen([sys.executable, 'resources.py'], creationflags = subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen([sys.executable, 'resources.py'])
except Exception as exception:
    fatal_exception(exception, "Could not pull in sass resources")



print("Creating default views for bottle project")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/views'))
    HEAD_TEMPLATE.populate('~head.tpl', 
        title=args.name, 
        description="Welcome to {}!".format(args.name) )
    INDEX_TEMPLATE.populate('index.tpl')
except Exception as exception:
    fatal_exception(exception, "Could not build default views")



print("Populating project resources")
try: #TODO: add checking if image doesn't meet requirements
    os.chdir(os.path.join(PROJECT_DIR, 'res'))
    if not args.favicon is None:
        if not os.path.isabs(args.favicon):
            args.favicon = os.path.join(SCRIPT_DIR, args.favicon)
        if os.path.isdir(args.favicon):
            args.favicon = os.path.join(args.favicon, "favicon.svg")
        if os.path.splitext(args.favicon)[-1].lower() != '.svg':
            raise Exception("Given image file does not meet requirements")
        shutil.copy(args.favicon, "favicon.svg")
except Exception as exception:
    non_fatal_exception(exception, "Unable to import favicon image. Do you wish to proceed? [yes/no]")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'res'))
    if not args.resources is None:
        resources = []
        for resource_path in args.resources:
            if not os.path.isabs(resource_path):
                resource_path = os.path.join(SCRIPT_DIR, resource_path)
            if os.path.isfile(resource_path):
                resource.append(resource_path)
            elif os.path.isdir(resource_path):
                for root, dirs, files in os.walk(resource_path):
                    for filename in files:
                        resources.append(os.path.join(root, filename))
        for resource in resources: #TODO: could use some improvement
            name = os.path.split(resource)[-1]
            ext = os.path.splitext(resource)[-1].lower()
            if ext == '.svg':
                if any(res in resources for res in [name[:-4] + '.eot', name[:-4] + '.ttf', name[:-4] + '.woff']): 
                    # if there is a font file of the same name this one is probably a font too
                    shutil.copy(resource, os.path.join('font', name))
                else:
                    shutil.copy(resource, os.path.join('img', name))
            elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
                shutil.copy(resource, os.path.join('img', name))
            elif ext in ['.eot', '.ttf', '.woff']:
                shutil.copy(resource, os.path.join('font', name))
            else:
                shutil.copy(resource, os.path.join('static', name))
except Exception as exception:
    fatal_exception(exception, "Could not import project resources")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'res/static'))
    if not os.path.isfile('robots.txt'): #user may have imported their own robots.txt
        ROBOTS_TEMPLATE.populate('robots.txt')
except Exception as exception:
    fatal_exception(exception, "Could not create default robots.txt")



print("Generating website in temporary directory")
try:
    os.chdir(PROJECT_DIR)
    populate_static_resource('build.py')
    if (os.name == 'nt'):
        subprocess.Popen([sys.executable, 'build.py', '-p', '.'], creationflags = subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen([sys.executable, 'build.py', '-p', '.'])
except Exception as exception:
    fatal_exception(exception, "Unable to generate website")


os.chdir(args.path)
os.remove("templates.py")
