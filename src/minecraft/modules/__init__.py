import os, path, logging, mcpackets
#### Framework for loading and referencing modules ####
__ALL__ = ['Command', 'Hook']

DEFAULT_MESSAGE_PREFIX = "# "
COLOR_PREFIX = '§'

class ModuleBase(object):
    #### Framework ####
    def __init__(self, session):
        self.comms = server.comms
        self.server = server
    
    #local access to chat command
    def chat(self, *messages, **kwargs):
        from mcpackets import encode
        """Use me to give information back to user via in-game chat."""
        prefix = settings.chat_prefix
        for message in messages:
            for line in message.replace("\r\n").split("\n"):
                self.comms.clientqueue.put(encode('s2c',0x03, {'message':prefix+line}))
    
    def help(self):
        """ returns the command's docstring unless overriden """
        return self.__doc__
    
    @property
    def alias(self): return self.__class__.__name__.lower()

class Command(ModuleBase):
    """ Define help syntax in the docstring pls kay thanx! """
    
    # put a list of required hooks here to see to make sure they are activated at startup
    required_hooks = []
    
    def run(self, *args):
        """ You must overide this method to make your command do something """
        raise NotImplementedError(self.__class__.__name__ + " Must define a run() method")
    
    # make command objects callable ;)
    __call__ == run

class Hook(ModuleBase):
    """ Define Hook Behavior in docstring PLSKAYTHANKS """
    packets = []
    
    def activate(self):
        """ does noting on activation """
        pass
    
    #need to make unbound
    def process(self, packet):
        """ This function is called on reciept of every packet it's registered for. """
        raise NotImplemented(self.__class__.__name__+" must implement a process method")
    
    def deactivate(self):
        """ does nothing on de-activation """
        pass
    
    __call__ = process # an alias for the process method

# dynamically loads commands from the /modules subdirectory
commands = []
hooks = []
import inspect
path = path.path(__file__).dirname()
modules = [f.split(".")[0] for f in os.listdir(path) if f.endswith(".py") and f != "__init__.py"]
for module_name in modules:
    try:
        module = __import__(module_name, globals(), locals())
        logging.debug(module)
        for potential_class in [o for n, o in inspect.getmembers(module) 
                                if inspect.isclass(o) and o.__module__ == "modules."+module_name]:
            logging.debug("\t"+str(potential_class))
            try:
                if issubclass(potential_class, Command):
                    commands.append(potential_class)
                if issubclass(potential_class, Hook):
                    hooks.append(potential_class)
            except:
                pass
    except ImportError as e:
        logging.error("Could not load %s: %s", module_name, e)

def activate_modules(session, modules, mode='add'):
    for module in modules:
        if isinstance(module, basestring) and module.startswith("-"):
            mode='remove'
            module=module[1:]
        if module == 'default':
            activate_modules(session, [comm for comm in commands if comm.default==True], mode)
        elif module == 'all':
            activate_modules(session, commands, mode)
        if mode=='remove':
            if isinstance(module, basestring):
                [c for c in session.commands if module=="%s.%s"%(c.__module__,c.__name__)]

def run_command(session, command, *args):
    pass
    
def process_hooks(session, packet):
    for hook in (h for h in session.hooks
                 if packet['id'] in (session.protocol.name_to_id[p] for p in h.packets)):
        hook.process(packet)