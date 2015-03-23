
import os
import cmd
import readline

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
            response = self.socket.recv(self.configs.get('read_buffer', 1024))
            return response
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
        print key

    def do_SET(self, key, value, expiry):
        """SET cache item value from the Reservoir cache
           FORMAT: GET <key> <value> <expiry>
        """
        print key

    def do_DEL(self, key):
        """REMOVE cache item value from the Reservoir cache
           FORMAT: DEL <key>
        """
        print key

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

if __name__ == '__main__':
        console = ReservoirConsole()
        console . cmdloop() 
