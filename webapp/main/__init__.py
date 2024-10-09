from flask import Blueprint

main = Blueprint('main',
     __name__,
     url_prefix='',
    template_folder='templates',
    static_folder='static')

from . import routes, events
