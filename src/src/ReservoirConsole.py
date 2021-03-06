
import os
import cmd
import readline
import json
import socket

class ReservoirConsole(cmd.Cmd):

    def __init__(self, **configs):
        self.configs = configs
        self.host = configs.get('server_host', 'localhost') # defaults to localhost
        self.port = configs.get('server_port', 3142)

        cmd.Cmd.__init__(self)
        self.prompt = "Reservoir > "
        self.intro  = "Welcome to Reservoir console!"  ## defaults to None

        # set the protocol to follow
        self.protocol = configs.get('protocol', 'TCP')
        if self.protocol not in ['TCP', 'UDP']:
            self.protocol = 'TCP' 

        self.socket = socket.socket() # default socket
        self.create_socket()
        self.connect()

    def create_socket(self):
        if self.protocol == 'TCP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.protocol == 'UDP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.socket = socket.socket()

    def connect(self):
        if self.protocol == 'TCP':
            print 'connecting to the server %s' % (self.host)
            self.socket.connect((self.host, self.port))

        if self.protocol == 'UDP':
            print 'No connection required for UDP'

    def send(self, data, expect_return=True):
        self.socket.send(data)
        if expect_return:
            response = self.socket.recv(1024)
            if response:
                response_json = json.loads(response)
                return response_json.get('data', None)
            else:
                return {}
        else:
            return True

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    def do_GET(self, key):
        """GET cache item value from the Reservoir cache
           FORMAT: GET <key>
        """
        batch = [{
            'key': key
        }]
        data_string = json.dumps(batch)
        data = "GET %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_SET(self, args):
        """SET cache item value from the Reservoir cache
           FORMAT: SET {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}
        """
        try:
            arguments = json.loads(args)
        except ValueError as e:
            print 'Invalid JSON Format. \n\tFORMAT: SET {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return

        if(len(arguments.values()) != 3):
            print 'Invalid arguments. \n\tFORMAT: SET {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return 

        batch = [{
            'key': arguments.get("key"),
            'data': arguments.get("value"),
            'expiry': str(arguments.get("expiry"))
        }]
        data_string = json.dumps(batch)
        data = "SET %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_DEL(self, key):
        """REMOVE cache item value from the Reservoir cache
           FORMAT: DEL <key>
        """
        batch = [{
            'key': key
        }]
        data_string = json.dumps(batch)
        data = "DEL %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_ICR(self, args):
        """INCREMENT a cache item value from the Reservoir cache. If the key does not exist it will initialize the key. 
           During initializing you can set expiry of the item as well
           FORMAT: ICR <key> [<expiry>]
        """
        arguments = args.split()
        key = arguments[0]
        if len(arguments > 1):
            expiry = arguments[1]
        else:
            expiry = 0

        batch = [{
            'key': key,
            'expiry': str(expiry)
        }]
        data_string = json.dumps(batch)
        data = "ICR %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_DCR(self, args):
        """DECREMENT a cache item value from the Reservoir cache.
           FORMAT: DCR <key> [<expiry>]
        """
        arguments = args.split()
        key = arguments[0]
        if len(arguments > 1):
            expiry = arguments[1]
        else:
            expiry = 0

        batch = [{
            'key': key,
            'expiry': str(expiry)
        }]
        data_string = json.dumps(batch)
        data = "DCR %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_OTA(self, args):
        """Set cache item value from the Reservoir cache with ONE-TIME-ACCESS
           FORMAT: OTA {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}
        """
        try:
            arguments = json.loads(args)
        except ValueError as e:
            print 'Invalid JSON Format. \n\tFORMAT: OTA {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return

        if(len(arguments.values()) != 3):
            print 'Invalid arguments. \n\tFORMAT: OTA {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return 

        batch = [{
            'key': arguments.get("key"),
            'data': arguments.get("value"),
            'expiry': str(arguments.get("expiry"))
        }]
        data_string = json.dumps(batch)
        data = "OTA %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_TPL(self, args):
        """Set cache item value from the Reservoir cache with READ-ONLY
           FORMAT: TPL {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}
        """
        try:
            arguments = json.loads(args)
        except ValueError as e:
            print 'Invalid JSON Format. \n\tFORMAT: TPL {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return

        if(len(arguments.values()) != 3):
            print 'Invalid arguments. \n\tFORMAT: TPL {"key":"<key>", "value":"<value>", "expiry":"<expiry>"}'
            return 

        batch = [{
            'key': arguments.get("key"),
            'data': arguments.get("value"),
            'expiry': str(arguments.get("expiry"))
        }]
        data_string = json.dumps(batch)
        data = "TPL %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    def do_TMR(self, key):
        """ Get the timer of a cache item; how long the item has been cached for
        """
        batch = [{
            'key': key,
        }]
        data_string = json.dumps(batch)
        data = "TMR %s" % (data_string,)
        result = self.send(data)
        result_json = json.loads(result)
        print result_json[0].get("data", None)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        print "" # new line after every command
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e

    def parse(arg):
        'Convert a series of zero or more numbers to an argument tuple'
        return tuple(map(int, arg.split()))

if __name__ == '__main__':
        console = ReservoirConsole()
        console . cmdloop() 
