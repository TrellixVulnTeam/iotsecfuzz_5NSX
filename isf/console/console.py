import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts.progress_bar import formatters
from prompt_toolkit.styles import Style

from .. import core
from ..core import logger as logger, ModuleExecutionError
from ..parameter import ParameterValidationError
from .logging import ConsoleHandler, ConsoleFormatter
from prompt_toolkit import print_formatted_text, HTML

from .cmd.set import CommandSet
from .cmd.use import CommandUse
from .cmd.run import CommandRun
from .cmd.list import CommandList
from .cmd.back import CommandBack
from .cmd.search import CommandSearch
from .cmd.options import CommandOptions
from .cmd.help import CommandHelp

commands = {}

LOGGING_FORMAT = '%(levelname)s <msg {}>%(message)s</msg>'

logging.addLevelName(logging.DEBUG, '<debug>[*]</debug>')
logging.addLevelName(logging.INFO, '<info>[*]</info>')
logging.addLevelName(logging.WARNING, '<warning>[!]</warning>')
logging.addLevelName(logging.ERROR, '<error>[!]</error>')

LOGGING_DATE_FORMAT = '%H:%M:%S'

handler = ConsoleHandler()
handler.setFormatter(ConsoleFormatter(fmt=LOGGING_FORMAT,
                                      datefmt=LOGGING_DATE_FORMAT))

logger.propagate = False
logger.handlers = [handler]

progress_styles = Style.from_dict({
    'label': '#ffffff',
    'percentage': '#ffffff',
    'current': '#448844',
    'bar': '#00dd00',
    'time': '#ffffff',
    'prefix': '#00dd00'
})

progress_formatters = custom_formatters = [
    formatters.Text('[/] ', style='class:prefix'),
    formatters.Label(),
    formatters.Text(': ', style='class:label'),
    formatters.Percentage(),
    formatters.Text(' '),
    formatters.Bar(sym_a='█', sym_b='█', sym_c='.'),
    formatters.Text('  '),
    formatters.TimeElapsed(),
]


def register_command(cmd):
    if cmd.name in commands:
        raise ValueError('Command \'%s\' already registered' % cmd.name)
    for alias in cmd.aliases:
        if alias in commands:
            raise ValueError('Command \'%s\' already registered' % alias)
    commands[cmd.name] = cmd
    for alias in cmd.aliases:
        commands[alias] = cmd


# Register console commands
register_command(CommandSet())
register_command(CommandUse())
register_command(CommandRun())
register_command(CommandList())
register_command(CommandBack())
register_command(CommandSearch())
register_command(CommandOptions())
register_command(CommandHelp())


# Prints the banner
# TODO print random banner from 'banners.txt'
def print_banner():
    banner = '''   
##################################################    
     
 _____    _____ _____          ______
|_   _|  |_   _/  ___|         |  ___|
  | |  ___ | | \ `--.  ___  ___| |_ _   _ ________
  | | / _ \| |  `--. \/ _ \/ __|  _| | | |_  /_  /
 _| || (_) | | /\__/ /  __/ (__| | | |_| |/ / / /
 \___/\___/\_/ \____/ \___|\___\_|  \__,_/___/___|
 
################################################## 
             ISF framework v1.0 
'''
    for line in banner.split('\n'):
        if line:
            print_formatted_text(HTML('<a fg="#22CC11">%s</a>' % line))


def start():
    session = PromptSession()
    print_banner()
    try:
        core.load_modules()
    except Exception as e:
        logger.error('Unable to load modules:', exc_info=e)
        return
    try:
        while True:
            prompt_text = 'IoTSecFuzz'

            if core.current_module:
                prompt_text += ' (%s)' % core.current_module.qualified_name

            prompt_text += ' > '

            text = session.prompt(HTML('<a fg="#22CC11">%s</a>' % prompt_text))
            if not text.strip():
                continue

            data = text.split()
            if len(data) == 0:
                continue

            cmd_name = data[0]
            args = data[1:] if len(data) > 0 else []
            if cmd_name in commands:
                cmd = commands[cmd_name]
                if len(args) < cmd.min_args_number:
                    logger.warning(
                        'Invalid number of arguments; at least %d required'
                        % cmd.min_args_number)
                    continue
                try:
                    cmd.run(args)
                except ParameterValidationError as e:
                    logger.warning(str(e), exc_info=None)
                except ModuleExecutionError as e:
                    logger.warning(str(e), exc_info=None)
                except KeyboardInterrupt:
                    logger.info('Execution interrupted by user')
                except Exception as e:
                    logger.error('Error occurred during command execution:',
                                 exc_info=e)
            else:
                logger.warn('No command named "%s"' % cmd_name)
    except KeyboardInterrupt:
        logger.info('Bye!')
        return
    except Exception as e:
        logger.error('Unhandled error:', exc_info=e)
        return
