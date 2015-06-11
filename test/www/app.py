"""
900
"""
from bottle import run, route, get, post, error
from bottle import static_file, template, request
from bottle import HTTPError



################################################################################
##### COMMAND LINE INTERFACE ###################################################
################################################################################

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from inspect import getframeinfo, currentframe
from os.path import dirname, abspath
import os

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
os.chdir(dirname(abspath(getframeinfo(currentframe()).filename)))



################################################################################
##### MAIN SITE ROUTES #########################################################
################################################################################

@route('/')
def load_root():
    return template('index', request=request, template='index')

@route('/index')
def load_index():
    return template('index', request=request, template='index')

@route('/test/test')
def load_test():
    return template('test', request=request, template='test')

@route('/test/testing/testing')
def load_testing():
    return template('testing', request=request, template='testing')



################################################################################
##### API AND ADDITIONAL SITE ROUTES ###########################################
################################################################################

@route('/', method='POST')
def api():
    if request.POST.get("v") == 'vendetta': 
        return """\
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
       you may call me V.
"""

    return load_root()



################################################################################
##### STATIC ROUTES ############################################################
################################################################################

@get('/ipadiphone.ai')
def load_resource():
    return static_file('ipadiphone.ai', root='static')

@get('/preview.psd')
def load_resource():
    return static_file('preview.psd', root='static')

@get('/robots.txt')
def load_resource():
    return static_file('robots.txt', root='static')


### Favicon Routes #############################################################
@get('/favicon-16x16.png')
def load_resource():
    return static_file('favicon-16x16.png', root='static/favicon')

@get('/favicon-32x32.png')
def load_resource():
    return static_file('favicon-32x32.png', root='static/favicon')

@get('/favicon-96x96.png')
def load_resource():
    return static_file('favicon-96x96.png', root='static/favicon')

@get('/favicon-160x160.png')
def load_resource():
    return static_file('favicon-160x160.png', root='static/favicon')

@get('/favicon-196x196.png')
def load_resource():
    return static_file('favicon-196x196.png', root='static/favicon')

@get('/favicon-300x300.png')
def load_resource():
    return static_file('favicon-300x300.png', root='static/favicon')

@get('/touch-icon-192x192.png')
def load_resource():
    return static_file('touch-icon-192x192.png', root='static/favicon')

@get('/apple-touch-icon-76x76.png')
def load_resource():
    return static_file('apple-touch-icon-76x76.png', root='static/favicon')

@get('/apple-touch-icon-120x120.png')
def load_resource():
    return static_file('apple-touch-icon-120x120.png', root='static/favicon')

@get('/apple-touch-icon-152x152.png')
def load_resource():
    return static_file('apple-touch-icon-152x152.png', root='static/favicon')

@get('/apple-touch-icon-180x180.png')
def load_resource():
    return static_file('apple-touch-icon-180x180.png', root='static/favicon')

@get('/apple-touch-icon-76x76-precomposed.png')
def load_resource():
    return static_file('apple-touch-icon-76x76-precomposed.png', root='static/favicon')

@get('/apple-touch-icon-120x120-precomposed.png')
def load_resource():
    return static_file('apple-touch-icon-120x120-precomposed.png', root='static/favicon')

@get('/apple-touch-icon-152x152-precomposed.png')
def load_resource():
    return static_file('apple-touch-icon-152x152-precomposed.png', root='static/favicon')

@get('/apple-touch-icon-180x180-precomposed.png')
def load_resource():
    return static_file('apple-touch-icon-180x180-precomposed.png', root='static/favicon')

@get('/apple-touch-icon.png')
def load_resource():
    return static_file('apple-touch-icon-57x57.png', root='static/favicon')

@get('/apple-touch-icon-precomposed.png')
def load_resource():
    return static_file('apple-touch-icon-57x57-precomposed.png', root='static/favicon')


### Image Routes ###############################################################
@get('/appicon-mines.svg')
def load_resource():
    return static_file('appicon-mines.svg', root='static/img')

@get('/appicon-passkey.svg')
def load_resource():
    return static_file('appicon-passkey.svg', root='static/img')

@get('/binding_dark.png')
def load_resource():
    return static_file('binding_dark.png', root='static/img')

@get('/binding_dark_@2X.png')
def load_resource():
    return static_file('binding_dark_@2X.png', root='static/img')

@get('/computer.svg')
def load_resource():
    return static_file('computer.svg', root='static/img')

@get('/crossword.png')
def load_resource():
    return static_file('crossword.png', root='static/img')

@get('/grey_wash_wall.png')
def load_resource():
    return static_file('grey_wash_wall.png', root='static/img')

@get('/grey_wash_wall_@2X.png')
def load_resource():
    return static_file('grey_wash_wall_@2X.png', root='static/img')

@get('/ipad-hand.png')
def load_resource():
    return static_file('ipad-hand.png', root='static/img')

@get('/ipadiphone.svg')
def load_resource():
    return static_file('ipadiphone.svg', root='static/img')

@get('/logo-small.svg')
def load_resource():
    return static_file('logo-small.svg', root='static/img')

@get('/logo-small_300x300.png')
def load_resource():
    return static_file('logo-small_300x300.png', root='static/img')

@get('/logo.png')
def load_resource():
    return static_file('logo.png', root='static/img')

@get('/logo.svg')
def load_resource():
    return static_file('logo.svg', root='static/img')

@get('/logo_15000x3808.png')
def load_resource():
    return static_file('logo_15000x3808.png', root='static/img')

@get('/preview-mines.png')
def load_resource():
    return static_file('preview-mines.png', root='static/img')

@get('/preview-passkey.png')
def load_resource():
    return static_file('preview-passkey.png', root='static/img')

@get('/preview.jpg')
def load_resource():
    return static_file('preview.jpg', root='static/img')

@get('/stardust.png')
def load_resource():
    return static_file('stardust.png', root='static/img')

@get('/stardust_@2X.png')
def load_resource():
    return static_file('stardust_@2X.png', root='static/img')

@get('/tweed.png')
def load_resource():
    return static_file('tweed.png', root='static/img')

@get('/tweed_@2X.png')
def load_resource():
    return static_file('tweed_@2X.png', root='static/img')

@get('/zwartevilt.png')
def load_resource():
    return static_file('zwartevilt.png', root='static/img')

@get('/zwartevilt_@2X.jpg')
def load_resource():
    return static_file('zwartevilt_@2X.jpg', root='static/img')

@get('/test_folder/ser01.png')
def load_resource():
    return static_file('ser01.png', root='static/img')

@get('/test_folder/ser02.png')
def load_resource():
    return static_file('ser02.png', root='static/img')

@get('/test_folder/ser03.png')
def load_resource():
    return static_file('ser03.png', root='static/img')


### Font Routes ################################################################
@get('/icomoon-social-media.eot')
def load_resource():
    return static_file('icomoon-social-media.eot', root='static/font')

@get('/icomoon-social-media.svg')
def load_resource():
    return static_file('icomoon-social-media.svg', root='static/font')

@get('/icomoon-social-media.ttf')
def load_resource():
    return static_file('icomoon-social-media.ttf', root='static/font')

@get('/icomoon-social-media.woff')
def load_resource():
    return static_file('icomoon-social-media.woff', root='static/font')


### Stylesheet Routes ##########################################################
@get('/styles.css')
def load_resource():
    return static_file('styles.css', root='static/css')

@get('/styles.css.map')
def load_resource():
    return static_file('styles.css.map', root='static/css')


### Javascript Routes ##########################################################



################################################################################
##### ERROR ROUTES #############################################################
################################################################################

@error(404)
def error404(error):
    return 'nothing to see here'



################################################################################
##### RUN SERVER ###############################################################
################################################################################

if args.deploy:
    run(host=args.ip, port=args.port, server='cherrypy') #deployment
else:
    run(host=args.ip, port=args.port, debug=True, reloader=True) #development 
