import os
import uuid
import requests
import functools

from .logger import log
from .utils import default_config_path, read_from_config, save_in_config, \
                   is_uuid, get_local_time, silent_fail, get_runtime_env, \
                   get_credentials, get_parameter_from_decorator
from .. import __version__

EVENT_VERSION = '1'
EVENT_SOURCE = 'cartoframes'

UUID_KEY = 'uuid'
ENABLED_KEY = 'enabled'
METRICS_FILENAME = 'metrics.json'

_metrics_config = None


def setup_metrics(enabled):
    '''Update the metrics configuration.

    Args:
        enabled (bool): flag to enable/disable metrics.

    '''
    global _metrics_config

    _metrics_config[ENABLED_KEY] = enabled

    save_in_config(_metrics_config, filename=METRICS_FILENAME)


@silent_fail
def init_metrics_config():
    global _metrics_config

    filepath = default_config_path(METRICS_FILENAME)

    if _metrics_config is None:
        if os.path.exists(filepath):
            _metrics_config = read_from_config(filepath=filepath)

        if not check_valid_metrics_uuid(_metrics_config):
            _metrics_config = create_metrics_config()
            save_in_config(_metrics_config, filename=METRICS_FILENAME)


def create_metrics_config():
    return {
        UUID_KEY: str(uuid.uuid4()),
        ENABLED_KEY: True
    }


def get_metrics_uuid():
    if _metrics_config is not None:
        return _metrics_config.get(UUID_KEY)


def get_metrics_enabled():
    if _metrics_config is not None:
        return _metrics_config.get(ENABLED_KEY)


def check_valid_metrics_uuid(metrics_config):
    return metrics_config is not None and is_uuid(metrics_config.get(UUID_KEY))


def build_metrics_data(event_name, extra_metrics_data):
    metrics_data = {
        'event_version': EVENT_VERSION,
        'event_time': get_local_time(),
        'event_source': EVENT_SOURCE,
        'event_name': event_name,
        'source_version': __version__,
        'installation_id': get_metrics_uuid(),
        'runtime_env': get_runtime_env()
    }

    if isinstance(extra_metrics_data, dict):
        metrics_data.update(extra_metrics_data)  # Compatible with old Python versions

    elif extra_metrics_data is not None:
        extra_metrics_data = {'extra': str(extra_metrics_data)}

    return metrics_data


@silent_fail
def post_metrics(event_name, extra_metrics_data):
    if get_metrics_enabled():
        json_data = build_metrics_data(event_name, extra_metrics_data)
        result = requests.post('https://carto.com/api/metrics', json=json_data, timeout=2)
        log.debug('Metrics sent! {0} {1}'.format(result.status_code, json_data))


def send_metrics(event_name):
    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            result = func(*args, **kwargs)

            extra_metrics_data = build_extra_metrics_data(func, *args, **kwargs)
            post_metrics(event_name, extra_metrics_data)

            return result
        return wrapper_func
    return decorator_func


def build_extra_metrics_data(decorated_function, *args, **kwargs):
    credentials = get_parameter_from_decorator(
        'credentials', decorated_function, *args, **kwargs)
    credentials = get_credentials(credentials)
    return {'user_id': credentials.user_id} if credentials and credentials.user_id else {}


# Run this once
init_metrics_config()
