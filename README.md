# Artifact for “Execution-Time Opacity Logic: A Logic for Ensuring ET-Opacity in Timed Systems”

## 1. Overview

This artifact contains the implementation of the ETOL model checker described in the accompanying paper, together with the benchmark models, ETOL formulas, scripts, 
and expected outputs used to reproduce the experimental results.

The artifact is designed to support the evaluation of the following claims made in the paper:

- symbolic model checking of ETOL formulas over timed automata;
- reproduction of the ATM case study;
- reproduction of the scalability experiments;
- regeneration of selected output files used to build the tables and figures in the paper.

The artifact is distributed as a self-contained Docker-based package to maximize reproducibility and future-proofness.

## 2. Contents

The artifact archive contains the following main components:

- paper/ETOL.pdf  
  PDF version of the submitted paper.

- src/  
  Source code of the ETOL model checker.

- models/  
  Timed automata models used in the paper, including the ATM benchmark and synthetic benchmark instances.

- formulas/  
  ETOL formulas used in the experiments.

- scripts/  
  Push-button scripts for quick checking and for reproducing the results from the paper.

- results/expected_outputs/ 
  Reference outputs corresponding to the results reported in the paper.

- docker/  
  Docker-related files, including the `Dockerfile`.

- image/etol-ae-docker.tar.gz  
  Pre-built Docker image saved with `docker save` and compressed for distribution.

## 3. Platform and requirements

### Tested platforms
The artifact has been prepared and tested on:

- Linux (amd64)
- macOS with Docker Desktop (amd64/arm64, if applicable)

### Required software
Only the following software is required on the host machine:

- Docker (recommended version 24.x or later)

No additional dependencies need to be installed manually on the host system.

## 4. Quick check

The quick check is intended for Phase I of the artifact evaluation. It runs a minimal example to verify that the environment is correctly set up and that the ETOL model checker can be executed successfully.

### Step 1: Load the Docker image

```bash
docker load < image/etol-ae-docker.tar.gz
