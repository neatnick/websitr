from subprocess import call

# watch styles.scss
# - all other sass files flow into this one so this is all we need
call("sass --watch styles.scss:../www/static/css/styles.css", shell=True)