
from flask import Flask
app = Flask(__name__)

from . import slack_commands
from . import slack_events
from . import userauth
from . import purchasing
from . import easy_inventory
from . import stats

app = Flask(__name__)

app.register_blueprint(slack_commands.blueprint, url_prefix='/slack_commands')
app.register_blueprint(userauth.blueprint, url_prefix='/userauth')
app.register_blueprint(purchasing.blueprint, url_prefix='/buy')
app.register_blueprint(easy_inventory.blueprint, url_prefix='/easy_inventory')
app.register_blueprint(stats.blueprint, url_prefix='/stats')
app.register_blueprint(slack_events.blueprint, url_prefix='/slack_events')


