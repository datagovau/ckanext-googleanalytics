import logging
import urllib
import commands
import dbutil
import paste.deploy.converters as converters
import pylons
import ckan.lib.helpers as h
import ckan.plugins as p
import gasnippet
from routes.mapper import SubMapper

import urllib2

import threading
import Queue

log = logging.getLogger('ckanext.googleanalytics')

class GoogleAnalyticsException(Exception):
    pass

class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grabs host from queue
            data_dict = self.queue.get()

            data = urllib.urlencode(data_dict)
            log.debug("Sending event to Google Analytics: " + data)
            # send analytics
            urllib2.urlopen(
                "http://www.google-analytics.com/collect",
                data,
                # timeout in seconds
                # https://docs.python.org/2/library/urllib2.html#urllib2.urlopen
                10)

            # signals to queue job is done
            self.queue.task_done()


class GoogleAnalyticsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers)

    analytics_queue = Queue.Queue()

    def configure(self, config):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        if 'googleanalytics.id' not in config:
            msg = "Missing googleanalytics.id in config"
            raise GoogleAnalyticsException(msg)
        self.googleanalytics_id = config['googleanalytics.id']
        self.googletagmanager_id = config['googletagmanager.id']
        self.googleanalytics_domain = config.get(
                'googleanalytics.domain', 'auto')
        self.googleanalytics_javascript_url = h.url_for_static(
                '/scripts/ckanext-googleanalytics.js')

        # If resource_prefix is not in config file then write the default value
        # to the config dict, otherwise templates seem to get 'true' when they
        # try to read resource_prefix from config.
        if 'googleanalytics_resource_prefix' not in config:
            config['googleanalytics_resource_prefix'] = (
                    commands.DEFAULT_RESOURCE_URL_TAG)
        self.googleanalytics_resource_prefix = config[
            'googleanalytics_resource_prefix']

        self.show_downloads = converters.asbool(
            config.get('googleanalytics.show_downloads', True))
        self.track_events = converters.asbool(
            config.get('googleanalytics.track_events', False))

        if not converters.asbool(config.get('ckan.legacy_templates', 'false')):
            p.toolkit.add_resource('fanstatic_library', 'ckanext-googleanalytics')

            # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()


    def update_config(self, config):
        '''Change the CKAN (Pylons) environment configuration.

        See IConfigurer.

        '''
        if converters.asbool(config.get('ckan.legacy_templates', 'false')):
            p.toolkit.add_template_directory(config, 'legacy_templates')
            p.toolkit.add_public_directory(config, 'legacy_public')
        else:
            p.toolkit.add_template_directory(config, 'templates')

    def before_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        # Helpers to reduce code clutter
        GET = dict(method=['GET'])
        PUT = dict(method=['PUT'])
        POST = dict(method=['POST'])
        DELETE = dict(method=['DELETE'])
        GET_POST = dict(method=['GET', 'POST'])
        # intercept downloads
        map.connect('/dataset/{id}/resource/{resource_id}/download',
                  controller='ckanext.googleanalytics.controller:GAPackageController',
                  action='resource_download')
        map.connect('/dataset/{id}/resource/{resource_id}/download/{filename}',
                  controller='ckanext.googleanalytics.controller:GAPackageController',
                  action='resource_download')
        # intercept API calls that we want to capture analytics on
        register_list = [
            'package',
            'dataset',
            'resource',
            'tag',
            'group',
            'related',
            'revision',
            'licenses',
            'rating',
            'user',
            'activity'
        ]
        register_list_str = '|'.join(register_list)
        # /api ver 3 or none
        with SubMapper(map, controller='ckanext.googleanalytics.controller:GAApiController', path_prefix='/api{ver:/3|}',
                    ver='/3') as m:
            m.connect('/action/{logic_function}', action='action',
                      conditions=GET_POST)

        # /api ver 1, 2, 3 or none
        with SubMapper(map, controller='ckanext.googleanalytics.controller:GAApiController', path_prefix='/api{ver:/1|/2|/3|}',
                       ver='/1') as m:
            m.connect('/search/{register}', action='search')

        # /api/rest ver 1, 2 or none
        with SubMapper(map, controller='ckanext.googleanalytics.controller:GAApiController', path_prefix='/api{ver:/1|/2|}',
                       ver='/1', requirements=dict(register=register_list_str)
                       ) as m:

            m.connect('/rest/{register}', action='list', conditions=GET)
            m.connect('/rest/{register}', action='create', conditions=POST)
            m.connect('/rest/{register}/{id}', action='show', conditions=GET)
            m.connect('/rest/{register}/{id}', action='update', conditions=PUT)
            m.connect('/rest/{register}/{id}', action='update', conditions=POST)
            m.connect('/rest/{register}/{id}', action='delete', conditions=DELETE)

        return map

    def after_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        map.redirect("/analytics/package/top", "/analytics/dataset/top")
        map.connect(
            'analytics', '/analytics/dataset/top',
            controller='ckanext.googleanalytics.controller:GAController',
            action='view'
        )
        return map

    def get_helpers(self):
        '''Return the CKAN 2.0 template helper functions this plugin provides.

        See ITemplateHelpers.

        '''
        return {'googleanalytics_header': self.googleanalytics_header}

    def googleanalytics_header(self):
        '''Render the googleanalytics_header snippet for CKAN 2.0 templates.

        This is a template helper function that renders the
        googleanalytics_header jinja snippet. To be called from the jinja
        templates in this extension, see ITemplateHelpers.

        '''
        data = {'googleanalytics_id': self.googleanalytics_id,
                'googletagmanager_id': self.googletagmanager_id,
                'googleanalytics_domain': self.googleanalytics_domain}
        return p.toolkit.render_snippet(
            'googleanalytics/snippets/googleanalytics_header.html', data)
