Some Automated KA Game
======================

To test the front end, run ``view-front-end.py``

To test the back end, you will want to use venv.
After cloning this repo (make sure to get the submodules), install virtualenv and run
::
    virtualenv venv

to create virtualenv in the folder venv
Now activate the virtualenv.  See `the virtualenv documentation page <http://virtualenv.readthedocs.org/en/latest/userguide.html>`_ for details.  Now you can pip install kacpaw, which will be in the submodule folder like so::
    pip install ./external/kacpaw

You may also need to install some other dependencies, such as jinja2
Now, you can run the program
::
    python __init__.py



Assuming I'm not the only person who will work on this game, communication will be done with issues.  Open an issue if you have a topic you want to discuss (or if there is an actual issue)

You need Python 3 (Probably 3.3+, I have 3.4) to run anything here, and you may need to ``pip install`` some stuff like jinja2.