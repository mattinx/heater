#!/usr/bin/python
"""Startup script for heaterui"""

from heaterui import create_app

app = create_app()

app.run(debug=True, host='0.0.0.0')
#app.run(debug=True)
