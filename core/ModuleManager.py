"""Librairie to manage modules.
"""

from core import CircuitsManager
from core import Log

import os

__active_modules_name = []
__modules_data = {}  # module data


def call_module_method(module_name, method_name, *arg, **kwargs):
    """Call module method.
    """
    if not module_name in __modules_data:
        Log.error('Module "%s" not found' % module_name)
        return False

    if __modules_data[module_name]['instance'] is None:
        Log.error('Module "%s" is not instantiated' % module_name)
        return False

    if not hasattr(__modules_data[module_name]['instance'], method_name):
        Log.error('Module "%s" has not a "%s" method' % (module_name, method_name))
        return False

    return getattr(__modules_data[module_name]['instance'], method_name)(*arg, **kwargs)


def disable_module(module_name, disabled=True):
    """Disable a module.
    """
    if module_name in __modules_data:
        return False

    from core import Daemon

    disable_file = os.path.join(Daemon.MODULES_PATH, module_name, 'disable')

    if disabled:
        stop(module_name)

        with open(disable_file, 'a'):
            os.utime(disable_file, None)

        return True

    else:
        if os.path.isfile(disable_file):
            os.remove(disable_file)

        start(module_name)


def get(module_name):
    """Get module instance.
    """
    return __modules_data[module_name]['instance'] if module_name in __modules_data else None


def get_info(module_name, key, default=None):
    """Get module info by key.
    """
    infos = get_infos(module_name)
    return infos[key] if key in infos else default


def get_infos(module_name):
    """Get module infos.
    """
    return __modules_data[module_name] if module_name in __modules_data else {}


def get_active_modules():
    """Get active module name list.
    """
    return __active_modules_name


def get_all_modules():
    """Get all (with disabled) module name list.
    """
    return __modules_data.keys()


def is_disabled(module_name):
    """Is module disable.
    """
    from core import Daemon

    dir_path = os.path.join(Daemon.MODULES_PATH, module_name)
    if not os.path.isdir(dir_path):
        return True

    return os.path.isfile(os.path.join(dir_path, 'disable'))


def init(module_name):
    """Init module.
    """
    if is_disabled(module_name):
        return False

    if module_name in __modules_data and not __modules_data[module_name]['instance']:
        from core import Daemon

        dir_path = os.path.join(Daemon.MODULES_PATH, module_name)

        module_file = os.path.join(dir_path, 'Module.py')
        if not os.path.isfile(module_file):
            return False

        try:
            __modules_data[module_name]['instance'] = __import__(
                'modules.' + module_name + '.Module',
                globals(),
                locals(),
                ['Module'],
            ).Module()
            Log.debug('init module %s' % module_name)

        except ImportError as e:
            Log.error('Import error, module %s (%s)' % (module_name, e))
            return False

        except AttributeError as e:
            Log.error('Module error, module %s (%s)' % (module_name, e))
            return False

    return True


def init_all():
    """Init all modules.
    """
    __load_module_list()
    loaded = [init(module_name) for module_name in __modules_data]

    Log.info('%d modules initialized' % sum(loaded))


def load(module_name):
    """Load module.
    """
    if is_disabled(module_name):
        return False

    if module_name in __modules_data and __modules_data[module_name]['instance'] is not None:
        Log.debug('load module %s' % module_name)
        return True

    return False


def load_all():
    """Load all modules.
    """
    __load_module_list()
    loaded = [load(module_name) for module_name in __modules_data]

    Log.info('%d modules loaded' % sum(loaded))


def restart(module_name):
    """Restart module.
    """
    Log.info('restart "%s" module' % module_name)
    stop(module_name)
    start(module_name)


def start(module_name):
    """Start module.
    """
    if is_disabled(module_name):
        return False

    if not module_name in __modules_data or __modules_data[module_name]['instance'] is None:
        return False

    # is Circuits module ?
    if hasattr(__modules_data[module_name]['instance'], 'register'):
        CircuitsManager.register(__modules_data[module_name]['instance'])

    __active_modules_name.append(module_name)
    Log.info('start "%s" module' % module_name)
    return True


def start_all():
    """Start all modules.
    """
    __load_module_list()
    started = [not __modules_data[module_name]['disable'] and start(module_name) for module_name in __modules_data]
    Log.info('%d modules started' % sum(started))


def stop(module_name):
    """Stop module.
    """
    __active_modules_name.remove(module_name)
    Log.info('stop "%s" module' % module_name)
    return True


def stop_all():
    """Stop all modules.
    """
    nb = 0

    for module_name in __modules_data:
        if __modules_data[module_name]['instance'] and stop(module_name):
            nb += 1

    Log.info('%d modules stopped' % nb)


def __load_module_list():
    """Add all modules in module_list.
    """
    global __modules_data

    if __modules_data:
        return

    from core import Daemon

    dir_list = sorted(os.listdir(Daemon.MODULES_PATH))
    nb = 0

    for module_name in dir_list:

        if is_disabled(module_name):
            continue

        if '__pycache__' in module_name:
            continue

        __modules_data[module_name] = {
            'instance': None,
            'disable': False,
        }
        Log.debug('index "%s" module' % module_name)
        nb += 1

    Log.info('%d modules indexed' % nb)

