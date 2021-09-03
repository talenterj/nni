# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from .utils import to_json
from .runtime.env_vars import trial_env_vars
from .runtime import platform
# import psutil

__all__ = [
    'get_next_parameter',
    'get_current_parameter',
    'report_intermediate_result',
    'report_final_result',
    'get_experiment_id',
    'get_trial_id',
    'get_sequence_id'
]


_params = None
_experiment_id = platform.get_experiment_id()
_trial_id = platform.get_trial_id()
_sequence_id = platform.get_sequence_id()


def get_next_parameter():
    """
    Get the hyper paremeters generated by tuner. For a multiphase experiment, it returns a new group of hyper
    parameters at each call of get_next_parameter. For a non-multiphase (multiPhase is not configured or set to False)
    experiment, it returns hyper parameters only on the first call for each trial job, it returns None since second call.
    This API should be called only once in each trial job of an experiment which is not specified as multiphase.

    Returns
    -------
    dict
        A dict object contains the hyper parameters generated by tuner, the keys of the dict are defined in
        search space. Returns None if no more hyper parameters can be generated by tuner.
    """
    global _params
    _params = platform.get_next_parameter()
    if _params is None:
        return None
    return _params['parameters']

def get_current_parameter(tag=None):
    """
    Get current hyper parameters generated by tuner. It returns the same group of hyper parameters as the last
    call of get_next_parameter returns.

    Parameters
    ----------
    tag: str
        hyper parameter key
    """
    global _params
    if _params is None:
        return None
    if tag is None:
        return _params['parameters']
    return _params['parameters'][tag]

def get_experiment_id():
    """
    Get experiment ID.

    Returns
    -------
    str
        Identifier of current experiment
    """
    return _experiment_id

def get_trial_id():
    """
    Get trial job ID which is string identifier of a trial job, for example 'MoXrp'. In one experiment, each trial
    job has an unique string ID.

    Returns
    -------
    str
        Identifier of current trial job which is calling this API.
    """
    return _trial_id

def get_sequence_id():
    """
    Get trial job sequence nubmer. A sequence number is an integer value assigned to each trial job base on the
    order they are submitted, incremental starting from 0. In one experiment, both trial job ID and sequence number
    are unique for each trial job, they are of different data types.

    Returns
    -------
    int
        Sequence number of current trial job which is calling this API.
    """
    return _sequence_id

_intermediate_seq = 0


def overwrite_intermediate_seq(value):
    """
    Overwrite intermediate sequence value.

    Parameters
    ----------
    value:
        int
    """
    assert isinstance(value, int)
    global _intermediate_seq
    _intermediate_seq = value


def report_intermediate_result(metric):
    """
    Reports intermediate result to NNI.

    Parameters
    ----------
    metric:
        serializable object.
    """
    global _intermediate_seq
    assert _params or trial_env_vars.NNI_PLATFORM is None, \
        'nni.get_next_parameter() needs to be called before report_intermediate_result'
    metric = to_json({
        'parameter_id': _params['parameter_id'] if _params else None,
        'trial_job_id': trial_env_vars.NNI_TRIAL_JOB_ID,
        'type': 'PERIODICAL',
        'sequence': _intermediate_seq,
        'value': to_json(metric)
    })
    _intermediate_seq += 1
    platform.send_metric(metric)

def report_final_result(metric, cpu_trial , mem_trial):
    """
    Reports final result to NNI.

    Parameters
    ----------
    metric: serializable object
        Usually (for built-in tuners to work), it should be a number, or
        a dict with key "default" (a number), and any other extra keys.
    """
    cpu_usage = str(cpu_trial)
    memory_usage = str(mem_trial)
    assert _params or trial_env_vars.NNI_PLATFORM is None, \
        'nni.get_next_parameter() needs to be called before report_final_result'
    metric = to_json({
        'parameter_id': _params['parameter_id'] if _params else None,
        'trial_job_id': trial_env_vars.NNI_TRIAL_JOB_ID,
        'type': 'FINAL',
        'sequence': 0,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'value': to_json(metric)
    })
    platform.send_metric(metric)
