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


import os, tempfile
import argparse

# Command Line Interface
parser = argparse.ArgumentParser(
    prog="WEBSITE_GENERATOR", 
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="Build stuff")
parser.add_argument("-p", "--path", 
    type=str,
    default=tempfile.gettempdir(),
    help="the path to the desired location of the generated site")
args = parser.parse_args()


SCRIPT_DIR = os.getcwd()

def fatal_exception(exception, message=""): #TODO: cleanup after failure?
    print("*******SCRIPT FAILED*******")
    if (message):
        print(message)
    print("Exception: ", exception)
    sys.exit(1)

try:
	os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided")

# add error checking for this stuff
os.makedirs("www/views")
os.makedirs("www/css")
os.makedirs("www/js")
os.makedirs("www/img")

os.chdir("www")





