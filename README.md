# SWAB-seq

...

## Getting Started

### Prerequisites

#### Docker

The computational pipeline is contained in a [docker image](https://hub.docker.com/octantbio/swab-seq). We strongly recommend using it for your analyses. Follow the official docs for: [MacOS](https://docs.docker.com/docker-for-mac/install/), [Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/), or [Windows](https://docs.docker.com/docker-for-windows/install/).

Next, choose one of the following:

**A.** Pull from DockerHub

```
docker pull octant/swab-seq
```

**B.** Build it yourself

```
git clone https://github.com/octantbio/swab-seq.git
cd octopus/docker
docker build .
```

It is possible to run the analyses without `docker`, but we would not recommended it. If you insist, see the [dockerfile](docker/Dockerfile) for help.

#### SWAB-seq Code

If you haven't already, clone this repository

```
git clone https://github.com/octantbio/swab-seq.git
```

or unzip the [latest release](https://github.com/octantbio/swab-seq/releases) tarball.

#### Hardware

For optimal performance, we recommend deploying on a machine with at least 32 GB of RAM and 16 cores. We use [GNU Parallel](https://www.gnu.org/software/parallel/) to distribute tasks where possible, and empirically, the RAM requirements seems to scale with the number of cores (e.g. 64 GB of RAM for 64 cores). The compute times (for 384 wells) scale asymptotically, suggesting a potential disk bottleneck.

```
64 cores -> 64 GB RAM -> 13 Mins
32 cores -> 32 GB RAM -> 15 Mins
24 cores -> 24 GB RAM -> 20 Mins
16 cores -> 16 GB RAM -> 25 Mins
8  cores ->  8 GB RAM -> 45 Mins
```

We performed all trials on two Intel(R) Xeon(R) Gold 6130 CPUs @ 2.10GHz, limiting the cores through the docker `--cpuset-cpus=N` flag, and estimated peak RAM usage with `/bin/free`.

### Running the Analysis

#### Directory Structure

The `swab-seq`

#### Spinning up docker

First, spin up a new docker container

```
docker run -d --rm \
  -e PASSWORD=[YOUR_PASSWORD] \
  -p 8787:8787  \
  -v /PATH/TO/SWAB-SEQ_DIR:/home/rstudio/swab-seq \
  -e USERID="$(id -u [USER_NAME])" \
  -e UMASK=0002 \
  swab-seq:latest
```

filling out anything within `[...]` to fit your needs.

#### Copying the raw data

All raw data go in the `data/` directory. Each subdirectory contains the demultiplexed fastq files from each sequencing run and is named with the Illumina Run ID. If you would like to symlink the raw data files instead of copying them, you will need to bind the symlink destination directory to your docker container by adding this argument to the `docker run` command above: `-v /PATH/TO/RAW-DATA/:/PATH/TO/RAW-DATA`.

#### Running the analysis

First, get the name of your docker container

```
docker ps
```

it should be the most recent `swab-seq` one. Next, drop into the docker container on the command line.

```
docker exec -it --user rstudio [docker_container_name] /bin/bash
```

Then navigate to the `swab-seq` folder.

```
cd swab-seq
```

To perform the analysis for one sequencing run, use `make` to generate the specific results target.

```
make results/[ILLUMINA_RUN_ID]/results.tsv.gz
```

To generate all results files, specify the `all` target instead.

```
make all
```

#### Accessing RStudio

You can drop into an RStudio session by pointing your browswer to `localhost:8787`. You should see a login screen that you can access with

```
username: rstudio
password: [YOUR_PASSWORD]
```

If you are running the docker image on a remote instance, you can access RStudio either by pointing your browser to `your.ip.address:8787` or by setting up an `ssh` tunnel from your local machine

```
ssh -N -L 8787:localhost:8787 [USER_NAME]@[your.ip.address]
```

#### Accessing JupyterLab

If you prefer Python to R, we've also included JupyterLab (along with some basic packages - pandas, scikit-learn, etc). Like before, we'll first spin up a docker image:

```
docker run -d --rm \
  -e PASSWORD=[YOUR_PASSWORD] \
  -p 8888:8888  \
  -v /PATH/TO/SWAB-SEQ_DIR:/home/rstudio/swab-seq \
  -e USERID="$(id -u [USER_NAME])" \
  -e UMASK=0002 \
  swab-seq:latest
```


## Contributing

Please feel free to open an issue or pull request.

## Authors

- **Eric Jones** - *Experimental Work*
- **Aaron Cooper** - *Experimental and Initial Computational Work*
- **Joshua Bloom** - *Statistical Modeling*
- **Nathan Lubock** - *Packaging, documentation, etc.*
- **Scott Simpkins** - *Packaging, documentation, etc.*
- **Molly Gasperini** - *Coordination, experimental design*
- **Sri Kosuri** - *External and Internal Coordination*

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details. Additional licensing information:

- [starcode](docker/starcode-license) - GPL-3.0

## Acknowledgments
