#
# Author: Chris Moyer
#

class ClientConnection(object):
    """
    HTTP Connection wrapper for boto_web clients
    """
    max_tries = 10

    def __init__(self, host, port, enable_ssl):
        """
        @param conn: the httplib connection object
        @type conn: httplib.Connection
        """
        if enable_ssl:
            from httplib import HTTPSConnection as Connection
        else:
            from httplib import HTTPConnection as Connection
        self.conn = Connection(host, port)
        self.host = host
        self.port = port
        self.enable_ssl = enable_ssl
        self.auth_header = None

    def request(self, method, path, post_data=None, body=None, headers={}):
        """
        @param method: the HTTP Method to use
        @type method: str

        @param path: the path to access
        @type path: str

        @param post_data: Optional POST data to send (as form encoded body)
        @type post_data: dict

        @param body: Optional body text to send
        @type body: str
        """
        tries = 0
        while tries < self.max_tries:
            tries += 1
            try:
                self.conn.close()
            except:
                pass
            self.conn.connect()
            if self.auth_header:
                headers['Authorization'] = self.auth_header
            self.conn.request(method, path, body, headers)
            resp = self.conn.getresponse()
            if resp.status == 401:
                self.get_basic_auth()
                continue
            elif resp.status >= 500:
                log.info("Got %s: Retrying in %s seconds" % (resp.status, (tries**2)))
                time.sleep(tries**2)
                continue
            else:
                return resp
        return resp

    def close(self):
        try:
            self.conn.close()
        except:
            pass

    def set_basic_auth(self, username, password):
        import base64
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        self.auth_header =  "Basic %s" % base64string

    def get_basic_auth(self):
        """
        Prompt for basic auth
        """
        import commands
        import re
        output = commands.getstatusoutput("security find-internet-password -gs %s" % self.host)
        if output[0] == 0:
            for l in output[1].split("\n"):
                matches = re.match("password: \"(.+?)\"", str(l))
                if matches:
                    password = matches.group(1)
                matches = re.match("\s+?\"acct\"<blob>=\"(.+?)\"", str(l))
                if matches:
                    username = matches.group(1)
            self.set_basic_auth(username, password)
        else:
            from getpass import getpass
            username = raw_input("Username: ")
            password = getpass("Password: ")
            self.set_basic_auth(username, password)
