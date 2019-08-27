import json
import threading
import logging
import os
from flask import Flask, render_template
from chomps.chomps import initialize
from chomps.sheetsdecorator import SheetsDecorator


logger = logging.getLogger(__name__)


class WebChomps(object):
    def __init__(self):
        self.credentials_path = os.path.join('.', 'data', 'client_secret_debug.json')
        self.config_file = os.path.join('.', 'data', 'config.json')
        assert os.path.exists(self.credentials_path)
        assert os.path.exists(self.config_file)
        with open(self.config_file) as data_file:
            self.config = json.load(data_file)

        self.app = Flask(__name__)
        self.spreadsheet = self.init_spreadsheet(self.config['email_address'])
        self.chomps_instance = initialize(
            bot_id=self.config['bot_id'],
            debug=self.config['debug'],
            use_spreadsheet=self.config['use_spreadsheet'],
            service_credentials=self.config['service_credentials'])

        threading.Thread(target=self.start_server)

    def start_server(self):
        self.chomps_instance.listen(port=self.config['listening_port'])  # blocking call

    def init_spreadsheet(self, email_address):
        logger.info('Preparing to initialize stats spreadsheet')
        spread = None
        if os.path.exists(self.credentials_path):
            spread = SheetsDecorator(load_spreadsheet=False, credentials=self.credentials_path)
            spread.init_spreadsheet(email=email_address)
            logger.info('Successfully created spreadsheet!')
        else:
            logger.error('Credentials file not found in path {}'.format(self.credentials_path))
        return spread


web_chomps = WebChomps()


@web_chomps.app.route('/')
def hello_world():
    context = web_chomps.chomps_instance.nickname_map  # GET STATS HERE AS DICT
    return render_template(template_name_or_list='views/stats.html', context=context)


@web_chomps.app.route('/partners')
def partners_view():
    context = web_chomps.chomps_instance.nickname_map
    return render_template(template_name_or_list='views/partners.html', context=context)


@web_chomps.app.route('/about')
def about_view():
    context = web_chomps.chomps_instance.nickname_map
    return render_template(template_name_or_list='views/about.html', context=context)


if __name__ == '__main__':
    logging_format = '%(asctime)s %(name)s [%(filename)s:%(lineno)d][%(process)d] [%(levelname)s] %(message)s'
    debug = bool(web_chomps.config['debug'])
    port = int(web_chomps.config['web_port'])
    host = '0.0.0.0'
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format=logging_format)
    logger.info('Starting server on {host}:{port}. Debug: {debug}.'.format(host=host, port=port, debug=debug))
    web_chomps.app.run(host=host, port=port, debug=debug, threaded=True)
