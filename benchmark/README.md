# Benchmarks

This repo uses Fabric to run benchmarks locally, on docker and remotely.

## Docker benchmark
In order to run a benchmark on [docker](https://www.docker.com/), please follow the steps below: 
- Install docker on every physical machine. 
- Build the docker image on every physical machine with :
    ```
    docker build -t superhotstuff .
    ```
- On your main machine, initialize a docker swarm with `docker swarm init`. This command will output a token that you will need in the next step.
- On the other machines, join the swarm with `docker swarm join --token <token> <ip>`.
- Create an overlay network with `docker network create --driver=overlay --subnet=10.1.0.0/16 benchNet`.
- Run `fab docker` on your main machine.

The results will be in the `results` repository following this format : 
`bench-{topology}-{faults}-{nodes}-{clients}-{rate}-{tx_size}-{latency}-{bandwidth}.txt`

## Remote benchmark

- Set your SSH keys in settings.json. 
- Modify _get_ami in instance.py to get an AWS AMI that you own.
- Run fab create to create EC2 instances. We advise using 8XL instances as their bandwidth is stable.
- Run fab update to clone the repository and compile the binary.
- Optional: create a new AMI and transfer it to each AWS region in order to avoid repeating the previous tasks for every benchmark. Don't forget to update _get_ami or improve the script.
- Run fab remote to run a benchmark.
