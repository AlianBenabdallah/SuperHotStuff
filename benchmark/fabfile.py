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
        'faults': 0,                     # Number of faults
        'nodes': 10,                     # Number of nodes
        'clients': 1,                    # Number of clients
        'rate': [1000],                 # Total rate of transactions per second
        'tx_size': 512,                  # Transaction size in bytes
        'duration': 30,                  # Duration in s
        'latency': 0,                    # Latency in ms
        'bandwidth': "",                 # Bandwidth in Mbps
        'topology': 'fullmesh',          # 'kauri', 'fullmesh', 'binomial'
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
            'max_batch_delay': 50,
            'max_hop_delay': 10000,
            'fanout': 3,
        }
    }
    settings = dict({
        "branch" : "script_with_failure",
        "repo_name" : "SuperHotStuff",
        "consensus_port": 8000,
        "mempool_port": 7000,
        "front_port": 6000
    })

    try:
        # Create containers and run the benchmark
        DockerBench(bench_params, node_params, settings).run(debug=True)
    except BenchError as e:
        Print.error(e)


@task
def local(ctx):
    ''' Run benchmarks on localhost '''
    bench_params = {
        'faults': 0,
        'nodes': 10,
        'clients': 1,  # Must be the same length as nodes or an integer
        'rate': 1000,
        'tx_size': 512,
        'duration': 30,
        'topology': 'fullmesh',
    }
    node_params = {
        'consensus': {
            'timeout_delay': 5_000,
            'sync_retry_delay': 10_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 500_000,
            'max_batch_delay': 50,
            'max_hop_delay': 10000,
            'fanout': 3,
        }
    }
    try:
        ret = LocalBench(bench_params, node_params).run(debug=True).result()
        print(ret)
    except BenchError as e:
        Print.error(e)


@task
def create(ctx, nodes=6):
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
def start(ctx, max=30):
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
        'nodes': 30,
        'clients': 1,  # Must be the same length as nodes or an integer
        'rate': [30_000],
        'tx_size': 512,
        'duration': 60,
        'runs': 1,
        'topology': 'fullmesh',
        'latency': 0,
        'bandwidth': "",
    }
    node_params = {
        'consensus': {
            'timeout_delay': 10_000,
            'sync_retry_delay': 10_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 10_000,
            'sync_retry_nodes': 3,
            'batch_size': 500_000,
            'max_batch_delay': 200,
            'max_hop_delay': 10000,
            'fanout' : 3,
        }
    }
    try:
        Bench(ctx).run(bench_params, node_params, debug=True)
    except BenchError as e:
        Print.error(e)


@task
def plot(ctx):
    ''' Plot performance using the logs generated by "fab remote" '''
    plot_params = {
        'faults': [0],
        'nodes': [29],
        'tx_size': 512,
        'max_latency': [5_000],
        'topology' : ['binomial'],
        'tc_latency' : [0],
        'tc_bandwidth' : ['max'],
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
        print(LogParser.process('./logs').result())
    except ParseError as e:
        Print.error(BenchError('Failed to parse logs', e))
