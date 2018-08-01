import hashlib
import logging
import re
import urllib

import ckan.logic as logic
from ckan.common import config
from ckan.controllers.package import PackageController
from ckan.controllers.api import ApiController
from ckan.lib.base import c, request
from paste.util.multidict import MultiDict

import plugin

log = logging.getLogger('ckanext.googleanalytics')


def _post_analytics(category, action, label):
    if config.get('googleanalytics.id'):
        data_dict = {
            "v": 1,
            "tid": config.get('googleanalytics.id'),
            "cid": hashlib.md5(c.user or c.environ.get('X-Forwarded-For') or c.environ.get('X-Real-IP') or c.remote_addr).hexdigest(),
            # customer id should be obfuscated
            "t": "event",
            "dh": c.environ['HTTP_HOST'],
            "dp": c.environ['PATH_INFO'],
            "dr": c.environ.get('HTTP_REFERER', ''),
            "ec": category,
            "ea": action,
            "el": label
        }
        data = urllib.urlencode(data_dict)
        log.debug("Sending event to queue: " + data)
        # send analytics asynchronously
        plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)


class GAPackageController(PackageController):

    def resource_download(self, id, resource_id, filename=None):
        try:
            if config.get('ckan.site_url') not in c.environ.get('HTTP_REFERER', '') \
                    and all(k not in c.environ.get('HTTP_USER_AGENT', '').lower() for k in ['okhttp', 'pingdom', 'bot']):
                        _post_analytics('Resource', 'Download',
                                        urllib.quote(config.get('ckan.site_url', '')+c.environ['PATH_INFO'], ''))
        except Exception, e:
            log.debug(e)
            pass

        return PackageController.resource_download(self, id, resource_id, filename)


class GAApiController(ApiController):
    # intercept API calls to record via google analytics
    def action(self, logic_function, ver=None):
        try:
            function = logic.get_action(logic_function)
            side_effect_free = getattr(function, 'side_effect_free', False)
            request_data = self._get_request_data(
                try_url_params=side_effect_free)
            if isinstance(request_data, dict):
                id = request_data.get('id', '')
                if 'q' in request_data:
                    id = request_data['q']
                if 'query' in request_data:
                    id = request_data['query']
                if 'resource_id' in request_data:
                    id = request_data['resource_id']
                if 'sql' in request_data:
                    uuidregex = re.compile('[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}')
                    for uuid in uuidregex.findall(request_data['sql']):
                        id = uuid
                _post_analytics("CKAN API Request", logic_function, id)
        except Exception, e:
            log.debug(e)
            pass

        return ApiController.action(self, logic_function, ver)


    def list(self, ver=None, register=None,
             subregister=None, id=None):
        _post_analytics("CKAN API Request",
                             register +
                             ("_" + str(subregister) if subregister else "")+
                             "list",
                             id)
        return ApiController.list(self, ver, register, subregister, id)


    def show(self, ver=None, register=None,
             subregister=None, id=None, id2=None):
        _post_analytics("CKAN API Request",,
                             register +
                             ("_" + str(subregister) if subregister else ""),
                             "show",
                             id)
        return ApiController.show(self, ver, register, subregister, id, id2)


    def update(self, ver=None, register=None,
               subregister=None, id=None, id2=None):
        _post_analytics("CKAN API Request",
                             register +
                             ("_" + str(subregister) if subregister else ""),
                             "update",
                             id)
        return ApiController.update(self, ver, register, subregister, id, id2)


    def delete(self, ver=None, register=None,
               subregister=None, id=None, id2=None):
        _post_analytics("CKAN API Request",
                             register +
                             ("_" + str(subregister) if subregister else ""),
                             "delete",
                             id)
        return ApiController.delete(self, ver, register, subregister, id, id2)


    def search(self, ver=None, register=None):
        id = None
        try:
            params = MultiDict(self._get_search_params(request.params))
            if 'q' in params.keys():
                id = params['q']
            if 'query' in params.keys():
                id = params['query']
        except ValueError, e:
            log.debug(str(e))
            pass
        _post_analytics("CKAN API Request", str(register) + "search", id)
        return ApiController.search(self, ver, register)
