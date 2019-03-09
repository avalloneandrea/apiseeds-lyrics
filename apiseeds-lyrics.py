PLUGIN_NAME = 'Apiseeds Lyrics'
PLUGIN_AUTHOR = 'Andrea Avallone'
PLUGIN_DESCRIPTION = 'Fetch lyrics from Apiseeds Lyrics, which provides millions of lyrics from artist all around the world. ' \
                     'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed. ' \
                     'In order to use Apiseeds you need to get a free API key at <em>https://apiseeds.com</em>. ' \
                     'Want to contribute? Check out the project page at <em>https://github.com/avalloneandrea/apiseeds-lyrics</em>!'
PLUGIN_VERSION = '1.0.0'
PLUGIN_API_VERSIONS = ['2.0.0']
PLUGIN_LICENSE = 'MIT'
PLUGIN_LICENSE_URL = 'https://opensource.org/licenses/MIT'

from functools import partial

from PyQt5 import QtWidgets
from picard import config, log
from picard.config import TextOption
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.util import load_json
from picard.webservice import ratecontrol
from urllib.parse import quote, urlencode

APISEEDS_HOST = 'orion.apiseeds.com'
APISEEDS_PORT = 443
APISEEDS_DELAY = 60 * 1000 / 200
ratecontrol.set_minimum_delay((APISEEDS_HOST, APISEEDS_PORT), APISEEDS_DELAY)  # 200 requests per minute


def process_result(album, metadata, response, reply, error):

    try:
        data = load_json(response)
        lyrics = data['result']['track']['text']
        metadata['lyrics'] = lyrics
        log.info('{}: lyrics found for track {}'.format(PLUGIN_NAME, metadata['title']))

    except:
        log.info('{}: lyrics NOT found for track {}'.format(PLUGIN_NAME, metadata['title']))

    finally:
        album._requests -= 1
        album._finalize_loading(None)


def process_track(album, metadata, track, release):

    apikey = config.setting['apiseeds_apikey']
    if (apikey is None):
        log.error('{}: API key is missing, please provide a valid value'.format(PLUGIN_NAME))
        return

    artist = metadata['artist']
    if (artist is None):
        log.error('{}: artist is missing, please provide a valid value'.format(PLUGIN_NAME))
        return

    title = metadata['title']
    if (title is None):
        log.error('{}: title is missing, please provide a valid value'.format(PLUGIN_NAME))
        return

    apiseeds_path = '/api/music/lyric/{}/{}'.format(artist, title)
    apiseeds_params = {'apikey': apikey}
    album._requests += 1
    log.info('{}: GET {}?{}'.format(PLUGIN_NAME, quote(apiseeds_path), urlencode(apiseeds_params)))

    album.tagger.webservice.get(
        APISEEDS_HOST,
        APISEEDS_PORT,
        apiseeds_path,
        partial(process_result, album, metadata),
        parse_response_type=None,
        priority=True,
        queryargs=apiseeds_params)


class ApiseedsLyricsOptionsPage(OptionsPage):

    NAME = 'apiseeds_lyrics'
    TITLE = 'Apiseeds Lyrics'
    PARENT = 'plugins'

    options = [TextOption('setting', 'apiseeds_apikey', None)]

    def __init__(self, parent=None):

        super(ApiseedsLyricsOptionsPage, self).__init__(parent)
        self.box = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.label.setText('Apiseeds API key')
        self.box.addWidget(self.label)

        self.description = QtWidgets.QLabel(self)
        self.description.setText('Apiseeds Lyrics provides millions of lyrics from artist all around the world. '
                                 'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed. '
                                 'In order to use Apiseeds Lyrics you need to get a free API key <a href="https://apiseeds.com">here</a>.')
        self.description.setOpenExternalLinks(True)
        self.box.addWidget(self.description)

        self.input = QtWidgets.QLineEdit(self)
        self.box.addWidget(self.input)

        self.contribute = QtWidgets.QLabel(self)
        self.contribute.setText('Want to contribute? Check out the <a href="https://github.com/avalloneandrea/apiseeds-lyrics">project page</a>!')
        self.contribute.setOpenExternalLinks(True)
        self.box.addWidget(self.contribute)

        self.spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.box.addItem(self.spacer)

    def load(self):
        self.input.setText(config.setting['apiseeds_apikey'])

    def save(self):
        config.setting['apiseeds_apikey'] = self.input.text()


register_track_metadata_processor(process_track)
register_options_page(ApiseedsLyricsOptionsPage)
