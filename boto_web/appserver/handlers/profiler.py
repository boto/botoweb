# Author: Chris Moyer
from boto_web.appserver.handlers import RequestHandler
from paste.debug.watchthreads import WatchThreads
class ProfilerHandler(RequestHandler):
    """
    Wrapper around the paste.debug.watchthreads.WatchThreads class
    """
    def __init__(self, config):
        RequestHandler.__init__(self, config)
        self.thread_watcher = WatchThreads(allow_kill=config.get('allow_kill', False))

    def _any(self, request, response, id=None):
        return request.get_response(self.thread_watcher)
