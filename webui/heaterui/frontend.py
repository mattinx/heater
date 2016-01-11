"""Frontend blueprint for Heater WebUI"""

import json

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from markupsafe import escape
from wtforms import Form
from wtforms.fields import RadioField, DecimalField
from wtforms.fields.html5 import DecimalRangeField


# from .forms import SignupForm
from .nav import nav

frontend = Blueprint('frontend', __name__)

# Setup navigation bar using flask-navbar
nav.register_element('frontend_top', Navbar(
    View('Heater Control', '.index'),
    View('Home', '.index'),
    Text('Using Flask-Bootstrap {}'.format(FLASK_BOOTSTRAP_VERSION)),
))


def getheatersettings():
    CONTROL_FILE = "/dev/shm/heater-control"
    default = {"highlowthresh": 1.5, "temphyst": 0.5, "elements": "auto", "run": "auto", "setpoint": 21.0, "minduration": 15}
    try:
        fd = open(CONTROL_FILE, "r")
        settings = json.load(fd)
        fd.close()
    except IOError:
        print "Error reading control file"
        return default
    except ValueError:
        print "Error parsing json from control file"
        return default
    return settings


def saveheatersettings(settings):
    CONTROL_FILE = "/dev/shm/heater-control"
    try:
        fd = open(CONTROL_FILE, "w")
        json.dump(settings, fd)
        fd.close()
    except IOError:
        print "Error writing control file"
        return False
    return True


def getheaterstate():
    STATUS_FILE = "/dev/shm/heater-status"
    default = {"heater": "off", "setpoint": 21.0, "run": "auto", "temperature": -999}
    try:
        fd = open(STATUS_FILE, "r")
        state = json.load(fd)
        fd.close()
    except IOError:
        print "Error reading state file"
        return default
    except ValueError:
        print "Error parsing json from state file"
        return default
    return state


class HeaterForm(Form):
    state = getheaterstate()
    settings = getheatersettings()
    run = RadioField(u'Heater', choices=[('off', 'Off'), ('cont', 'Continuous'), ('auto', 'Automatic')])
    # setpoint = DecimalRangeField('Setpoint', default=settings['setpoint'])
    setpoint = DecimalField('Setpoint', default=settings['setpoint'])
    elements = RadioField(u'Heat', choices=[('low', 'Low'), ('high', 'High'), ('auto', 'Automatic')])


@frontend.route('/', methods=['GET', 'POST'])
def index():
    state = getheaterstate()
    settings = getheatersettings()
    tempC = "%.2fC" % state['temperature']
    form = HeaterForm(request.form)

    if request.method == "POST" and form.validate():
        settings['run'] = request.form.get('run')
        setpoint = float(request.form.get('setpoint'))
        setpoint = round(setpoint * 2) / 2
        settings['setpoint'] = setpoint
        settings['elements'] = request.form.get('elements')
        saveheatersettings(settings)

    if settings['run'] == "cont":
        flash(u'Heater is in continuous mode and will not turn off automatically', 'error')
    elif settings['run'] == "off":
        flash(u'Heater is turned off', 'warning')

    return render_template('index.html', tempC=tempC, state=state, settings=settings, form=form)

"""
# Shows a long signup form, demonstrating form rendering.
@frontend.route('/example-form/', methods=('GET', 'POST'))
def example_form():
    form = SignupForm()

    if form.validate_on_submit():
        # We don't have anything fancy in our application, so we are just
        # flashing a message when a user completes the form successfully.
        #
        # Note that the default flashed messages rendering allows HTML, so
        # we need to escape things if we input user values:
        flash('Hello, {}. You have successfully signed up'
              .format(escape(form.name.data)))

        # In a real application, you may wish to avoid this tedious redirect.
        return redirect(url_for('.index'))

    return render_template('signup.html', form=form)
"""
