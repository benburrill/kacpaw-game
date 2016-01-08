"""
The idea with this file is that even without installing kacpaw or needing to run the game itself and checking on the KA program, you should be able to see what the front end looks like.  You will need to install jinja2 for this to work.
"""
import jinja2
import base64

env = jinja2.Environment(loader=jinja2.PackageLoader(__name__), undefined=jinja2.StrictUndefined)

# you may need to update some things here to make it work properly
html = env.get_template("program.html").render(
    world_json='{note: "This was loaded from view-front-end.py which may not have access to some important stuff and needs to be modified to keep up with the back end"}',
    title="Title Goes Here!"
)

# make a b64 data uri for the html.  The encode() decode() stuff is because b64encode takes bytes and (for some reason) returns bytes as well.
uri = "data:text/html;base64,{data}".format(data=base64.b64encode(html.encode()).decode())

# Now for actually opening the uri in a web browser
# This was a little more complicated than I expected.  webbrowser.open has problems with data uris on windows.  It opens a windows saying "You'll need a new app to open this data" and doesn't allow you to simply open it with a web browser.  This isn't really webbrowser's fault, it's just asking windows how it wants to open it, and windows doesn't recognise the data: protocol.  I thought maybe I could open it directly in Firefox, but for some reason webbrowser doesn't seem to recognise I have firefox (or any browser besides IE) installed.  I tried IE, but IE doesn't know understand data uris aparently.  At least it opened a web browser window though.  Anyway, at this point I decided I should use selenium and fallback on webbrowser if it isn't installed.  I've used selenium before and it worked perfectly.  Unfortunately, even the most basic documented selenium program failed to work.  It opened a web browser window, but then the program just hung and never got to the point where I could ask it to do things with that window.  I went back and forth between webbrowser and selenium before I finally decided to try upgrading selenium to the latest version.
# Moral of the story: web browsers are complicated, windows is annoying, and always keep selenium up to date.

try:
    from selenium import webdriver
    webdriver.Firefox().get(uri)
except ImportError:
    print("You don't have selenium installed, falling back on webbrowser.  If the page doesn't open, try installing selenium.")
    import webbrowser
    webbrowser.open(uri)