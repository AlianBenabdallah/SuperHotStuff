from os.path import join

from benchmark.utils import PathMaker


class CommandMaker:

    @staticmethod
    def cleanup():
        return (
            f'rm -rf .db-* ; rm .*.json ; mkdir -p {PathMaker.results_path()}'
        )

    @staticmethod
    def clean_logs():
        return f'rm -rf {PathMaker.logs_path()} ; mkdir -p {PathMaker.logs_path()}'

    @staticmethod
    def compile():
        return 'cargo build --quiet --release --features benchmark'

    @staticmethod
    def generate_key(filename):
        assert isinstance(filename, str)
        return f'./node keys --filename {filename}'

    @staticmethod
    def remove_tc(interface='eth0'):
        return f'tc qdisc del dev {interface} root netem'

    @staticmethod
    def tc(latency, bandwidth, interface='eth0'):
        assert isinstance(latency, int)
        assert isinstance(bandwidth, str)
        cmd = [f'tc qdisc add dev {interface} root netem']
        if latency > 0:
            cmd.append(f'delay {latency}ms')
        if bandwidth:
            cmd.append(f'limit 4000000 rate {bandwidth}mbit')
        cmd = ' '.join(cmd)
        return cmd

    @staticmethod
    def run_node(keys, committee, store, parameters, topology, debug=False):
        assert isinstance(keys, str)
        assert isinstance(committee, str)
        assert isinstance(parameters, str)
        assert isinstance(topology, str)
        assert isinstance(debug, bool)
        v = '-vvv' if debug else '-vv'
        return (f'./node {v} run --keys {keys} --committee {committee} '
                f'--store {store} --topology-builder {topology} --parameters {parameters}')

    @staticmethod
    def run_client(address, size, rate, timeout, nodes=[]):
        assert isinstance(address, str)
        assert isinstance(size, int) and size > 0
        assert isinstance(rate, int) and rate >= 0
        assert isinstance(nodes, list)
        assert all(isinstance(x, str) for x in nodes)
        nodes = f'--nodes {" ".join(nodes)}' if nodes else f'--nodes {address}'
        cmd = (f'./client {address} --size {size} '
               f'--rate {rate} --timeout {timeout} {nodes}')
        return cmd

    @staticmethod
    def kill():
        return 'tmux kill-server'

    @staticmethod
    def alias_binaries(origin):
        assert isinstance(origin, str)
        node, client = join(origin, 'node'), join(origin, 'client')
        return f'rm node ; rm client ; ln -s {node} . ; ln -s {client} .'
