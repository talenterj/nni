# Copyright (c) Microsoft Corporation
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import nni
import subprocess
import logging
import psutil
import numpy as np
import shutil

from pathlib import Path
from numpy import *

LOG = logging.getLogger('rocksdb-workloada')

cpu_trial_avg = 0
memory_trial = 0
list_cpu_result = []


def generate_args(parameters):
    args = []
    # Set low priority parameters based on high priority parameters
    # if parameters['memtablerep'] != "skip_list":
    #     parameters['allow_concurrent_memtable_write'] = False
    # Combine conflict parameters with same priority
    for k, v in parameters.items():
        # if k == "io_method":
        #     if v == 0:
        #         args.append("--mmap_read=0")
        #         args.append("--use_direct_reads=0")
        #         args.append("--mmap_write=0")
        #         args.append("--use_direct_io_for_flush_and_compaction=0")
        #     elif v == 1:
        #         args.append("--mmap_read=0")
        #         args.append("--use_direct_reads=0")
        #         args.append("--mmap_write=0")
        #         args.append("--use_direct_io_for_flush_and_compaction=1")
        #     elif v == 2:
        #         args.append("--mmap_read=0")
        #         args.append("--use_direct_reads=0")
        #         args.append("--mmap_write=1")
        #         args.append("--use_direct_io_for_flush_and_compaction=0")
        #     elif v == 4:
        #         args.append("--mmap_read=0")
        #         args.append("--use_direct_reads=1")
        #         args.append("--mmap_write=0")
        #         args.append("--use_direct_io_for_flush_and_compaction=0")
        #     elif v == 5:
        #         args.append("--mmap_read=0")
        #         args.append("--use_direct_reads=1")
        #         args.append("--mmap_write=0")
        #         args.append("--use_direct_io_for_flush_and_compaction=1")
        #     elif v == 8:
        #         args.append("--mmap_read=1")
        #         args.append("--use_direct_reads=0")
        #         args.append("--mmap_write=0")
        #         args.append("--use_direct_io_for_flush_and_compaction=0")
        #     elif v == 10:
        #         args.append("--mmap_read=1")
        #         args.append("--use_direct_reads=0")
        #         args.append("--mmap_write=1")
        #         args.append("--use_direct_io_for_flush_and_compaction=0")
        # else:
        args.append("{}={}".format(k, v))
    return args


def run(**parameters):
    '''Run rocksdb benchmark and return throughput'''
    # bench_type = parameters['benchmarks']
    # recover args
    args = generate_args(parameters)
    # print(args)
    list_cpu_avg = []
    list_mem = []
    # create a subprocess to run go-ycsb
    process = subprocess.Popen(['go-ycsb', 'run', 'rocksdb', '-P', '/root/zcj/go-ycsb/workloads/writeheavy', '-p',
                                'operationcount=1000000', '-p', 'recordcount=10000000', '-p'] + args, stdout=subprocess.PIPE)
    # process.poll() detect subprocess finished
    while process.poll() is None:
        list_mem.append(psutil.virtual_memory().used)
        # statistic cpu_percent per 0.1s
        tmp = psutil.cpu_percent(0.1)
        list_cpu_avg.append(tmp)
    
    # in python global var need to state in local func first
    global cpu_trial_avg
    cpu_trial_avg = int(mean(list_cpu_avg) * 10) / 10
    global memory_trial
    memory_trial_int = int(mean(list_mem) / 1024 / 1024 / 1024 * 100) / 100
    memory_trial = "%s" % (memory_trial_int)

    cpu_90 = int(np.percentile(list_cpu_avg, 90) * 10) / 10
    cpu_95 = int(np.percentile(list_cpu_avg, 95) * 10) / 10
    cpu_99 = int(np.percentile(list_cpu_avg, 99) * 10) / 10
    list_cpu_result.append("%s%s" % ("avg: ", str(cpu_trial_avg)))
    list_cpu_result.append("%s%s" % ("90: ", str(cpu_90)))
    list_cpu_result.append("%s%s" % ("95: ", str(cpu_95)))
    list_cpu_result.append("%s%s" % ("99: ", str(cpu_99)))

    # get db_bench result after process finished
    out, err = process.communicate()
    # split into lines
    lines = out.decode("utf8").splitlines()

    oper_count_lines = []
    time_lines = []
    for line in lines:
        # find the line with matched str
        if 'operationcount' in line:
            oper_count_lines.append(line)
        elif 'finish' in line:
            time_lines.append(line)
            break
        else:
            continue

    oper_count = 1.0
    time = 1.0
    # db_bench result select throughout ops/s
    for line in oper_count_lines:
        _, _, value = line.partition("=")
        value = value.strip('"')
        oper_count = float(value)

    for line in time_lines:
        _, _, value = line.partition(",")
        value = value.strip('takes ')
        if "ms" in line:
            value = value.strip('ms')
            time = float(value) / 1000
        else:
            value = value.strip('s')
            time = float(value)

    ops = int((oper_count / time) * 10) / 10
    return ops


def generate_params(received_params):
    '''generate parameters based on received parameters'''
    params = {
        "rocksdb.dir": "/mnt/vdc/rocksdb",
        "rocksdb.write_buffer_size": 2097152,
        "rocksdb.block_size": 4096
    }

    for k, v in received_params.items():
        if isinstance(v, str):
            params[k] = str(v)
        elif isinstance(v, float) and 1 > v > 0:
            params[k] = float(v)
        else:
            params[k] = int(v)

    return params


if __name__ == "__main__":
    try:
        # get parameters from tuner
        RECEIVED_PARAMS = nni.get_next_parameter()
        LOG.debug(RECEIVED_PARAMS)
        # print(RECEIVED_PARAMS)
        PARAMS = generate_params(RECEIVED_PARAMS)
        LOG.debug(PARAMS)
        # delete db before trial
        if Path('/mnt/vdc/rocksdb'):
            shutil.rmtree('/mnt/vdc/rocksdb')
        # os.mkdir('/mnt/vdc/rocksdb')
        # reload data
        process_load = subprocess.Popen(['go-ycsb', 'load', 'rocksdb', '-P', '/root/zcj/go-ycsb/workloads/writeheavy',
                                         '-p', 'recordcount=10000000', '-p', 'rocks.db=/mnt/vdc/rocksdb'],
                                        stdout=subprocess.PIPE)
        out_load, err_load = process_load.communicate()
        # run benchmark
        throughput = run(**PARAMS)
        LOG.debug(throughput)
        # report throughput to nni
        nni.report_final_result(throughput, list_cpu_result, memory_trial)
    except Exception as exception:
        LOG.exception(exception)
        raise
