from urllib.request import urlopen
from shutil import copyfileobj
import os


RESOURCES = (
[ 
    { 
        "name": "_flex-box_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "mastastealth/sass-flex-mixin/master/_flexbox.scss" ) 
    },

    { 
        "name": "_media-query_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "paranoida/sass-mediaqueries/master/_media-queries.scss" )
    },

    { 
        "name": "_general_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "SwankSwashbucklers/some-sassy-mixins/master/mixins.scss" ) 
    } 
]
)

def populate_resource(resource_name, resource_url):
    try:
        with urlopen(resource_url) as response, \
                open(resource_name, 'wb') as f:
            copyfileobj(response, f)
        print("Successfully populated '{}'".format(resource_name))
    except Exception as e:
        message = "Could not populate resource" \
            if not (os.path.isfile(resource_name)) \
            else "Unable to update resource"
        print("{}: {}\n  from url: {}\nException: {}".format(
            message, resource_name, resource_url, e ) )


print("Updating external sass resources")
for resource in RESOURCES:
    populate_resource(resource['name'], resource['url'])