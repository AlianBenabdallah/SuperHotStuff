from fabric import task
from benchmark.dockerbench import DockerBench

from benchmark.local import LocalBench
from benchmark.logs import ParseError, LogParser
from benchmark.utils import Print
from benchmark.plot import Ploter, PlotError
from benchmark.instance import InstanceManager
from benchmark.remote import Bench, BenchError


@task
def docker(ctx):
    """run a benchmark on docker"""
    bench_params = {
        'faults': 0,
        'nodes': [4],
        'clients' : [1], # Must be the same length as nodes or an integer
        'rate': [10000],
        'tx_size': 512,
        'duration': 20,
        'latency' : 20, # in ms
        'bandwidth' : "", # Has to be str > 0
        'topology' : 'fullmesh',
    }
    node_params = {
        'consensus': {
            'timeout_delay': 1_000,
            'sync_retry_delay': 10_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 15_000,
            'max_batch_delay': 40,
            'fanout' : 4,
        }
    }
    settings = dict({
            "consensus_port": 8000,
            "mempool_port": 7000,
            "front_port": 6000
        })

    try:
        # Create a container, connected to benchNet network, which will supervise the benchmark
        ret = DockerBench(bench_params, node_params, settings).run(debug=True)
    except BenchError as e:
        Print.error(e)

@task
def local(ctx):
    ''' Run benchmarks on localhost '''
    bench_params = {
        'faults': 0,
        'nodes': 10,
        'clients' : 4, # Must be the same length as nodes or an integer
        'rate': 10000,
        'tx_size': 512,
        'duration': 20,
        'topology': 'fullmesh',
    }
    node_params = {
        'consensus': {
            'timeout_delay': 1_000,
            'sync_retry_delay': 10_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 15_000,
            'max_batch_delay': 10,
            'fanout' : 4,
        }
    }
    try:
        ret = LocalBench(bench_params, node_params).run(debug=False).result()
        print(ret)
    except BenchError as e:
        Print.error(e)


@task
def create(ctx, nodes=2):
    ''' Create a testbed'''
    try:
        InstanceManager.make().create_instances(nodes)
    except BenchError as e:
        Print.error(e)


@task
def destroy(ctx):
    ''' Destroy the testbed '''
    try:
        InstanceManager.make().terminate_instances()
    except BenchError as e:
        Print.error(e)


@task
def start(ctx, max=2):
    ''' Start at most `max` machines per data center '''
    try:
        InstanceManager.make().start_instances(max)
    except BenchError as e:
        Print.error(e)


@task
def stop(ctx):
    ''' Stop all machines '''
    try:
        InstanceManager.make().stop_instances()
    except BenchError as e:
        Print.error(e)


@task
def info(ctx):
    ''' Display connect information about all the available machines '''
    try:
        InstanceManager.make().print_info()
    except BenchError as e:
        Print.error(e)


@task
def install(ctx):
    ''' Install the codebase on all machines '''
    try:
        Bench(ctx).install()
    except BenchError as e:
        Print.error(e)


@task
def remote(ctx):
    ''' Run benchmarks on AWS '''
    bench_params = {
        'faults': 0,
        'nodes': [10, 20],
        'clients' : 4, # Must be the same length as nodes or an integer
        'rate': [10_000, 30_000],
        'tx_size': 512,
        'duration': 300,
        'runs': 5,
        'topology': 'kauri',
    }
    node_params = {
        'consensus': {
            'timeout_delay': 5_000,
            'sync_retry_delay': 5_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 500_000,
            'max_batch_delay': 100
        }
    }
    try:
        Bench(ctx).run(bench_params, node_params, debug=False)
    except BenchError as e:
        Print.error(e)


@task
def plot(ctx):
    ''' Plot performance using the logs generated by "fab remote" '''
    plot_params = {
        'faults': [0],
        'nodes': [10, 20, 50],
        'tx_size': 512,
        'max_latency': [2_000, 5_000]
    }
    try:
        Ploter.plot(plot_params)
    except PlotError as e:
        Print.error(BenchError('Failed to plot performance', e))


@task
def kill(ctx):
    ''' Stop any HotStuff execution on all machines '''
    try:
        Bench(ctx).kill()
    except BenchError as e:
        Print.error(e)


@task
def logs(ctx):
    ''' Print a summary of the logs '''
    try:
        print(LogParser.process('./logs', faults='?').result())
    except ParseError as e:
        Print.error(BenchError('Failed to parse logs', e))
