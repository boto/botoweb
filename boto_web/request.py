import webob

class Request(webob.Request):
    """
    We like to add in session support here. Due to how the system must be distributable,
    all session information must be stored in the database.
    """
    file_extension = "html"

    def __init__(self, environ):
        charset = webob.NoDefault
        if environ.get('CONTENT_TYPE', '').find('charset') == -1:
            charset = 'utf-8'

        webob.Request.__init__(self, environ, charset=charset,
            unicode_errors= 'ignore', decode_param_names=True)

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
