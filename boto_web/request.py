import webob
from boto_web.resources.user import User
import logging
log = logging.getLogger("vermouth.request")
from boto_web.response import Response

class Request(webob.Request):
    """
    We add in a few special extra functions for us here.
    """
    file_extension = "html"
    ResponseClass = Response

    def __init__(self, environ):
        self._user = None
        charset = webob.NoDefault
        if environ.get('CONTENT_TYPE', '').find('charset') == -1:
            charset = 'utf-8'

        webob.Request.__init__(self, environ, charset=charset,
            unicode_errors= 'ignore', decode_param_names=True)
        if self.headers.has_key("X-Forwarded-Host"):
            self.real_host_url = "%s://%s" % (self.headers.get("X-Forwarded-Proto", "http"), self.headers.get("X-Forwarded-Host"))
        else:
            self.real_host_url = self.host_url

    def get(self, argument_name, default_value='', allow_multiple=False):
        param_value = self.get_all(argument_name)
        if allow_multiple:
            return param_value
        else:
            if len(param_value) > 0:
                return param_value[0]
            else:
                return default_value

    def get_all(self, argument_name):
        if self.charset:
            argument_name = argument_name.encode(self.charset)

        try:
            param_value = self.params.getall(argument_name)
        except KeyError:
            return default_value

        for i in range(len(param_value)):
            if isinstance(param_value[i], cgi.FieldStorage):
                param_value[i] = param_value[i].value

        return param_value

    def formDict(self):
        vals = {}
        if self.GET:
            for k in self.GET:
                vals[k] = self.GET[k]
        if self.POST:
            for k in self.POST:
                vals[k] = self.POST[k]
        return vals

    def getUser(self):
        """
        Get the user from this request object
        @return: User object, or None
        @rtype: User or None
        """
        if not self._user:
            auth_header =  self.environ.get("HTTP_AUTHORIZATION")
            if auth_header:
                auth_type, encoded_info = auth_header.split(None, 1)
                if auth_type.lower() == "basic":
                    unencoded_info = encoded_info.decode('base64')
                    username, password = unencoded_info.split(':', 1)
                    log.info("Looking up user: %s" % username)
                    try:
                        user = User.find(username=username).next()
                    except:
                        user = None
                    if user and user.password == password:
                        self._user = user
        return self._user

    user = property(getUser, None, None)

    def get_base_url(self):
        return self.headers.get("X-Forwarded-URL", self.script_name)
    base_url = property(get_base_url, None, None)
