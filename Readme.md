To do: add initial conditions to boundary conditions calculations

# OpenFOAM CFD Automation

## Overview
This repository contains an automated workflow for running **Computational Fluid Dynamics (CFD) simulations** using **OpenFOAM** in a cloud-based environment via **GitHub Actions**.

## Features
- **Automated CFD Execution** → Runs simulations remotely to reduce local computational load.
- **Cloud-Based Processing** → Offloads complex calculations to GitHub-hosted virtual machines.
- **File Management with Dropbox** → Uses Dropbox for seamless input/output file storage.

## Workflow Summary
1. **Upload input files** to Dropbox (`/simulations/OpenFOAM/input/`).
2. **Trigger GitHub Actions** to run OpenFOAM simulations.
3. **Retrieve output files** from Dropbox (`/simulations/OpenFOAM/output/`).

## Usage
To run a simulation:
1. Prepare case files and upload them to Dropbox.
2. Trigger the GitHub Actions workflow.
3. Download and analyze results from Dropbox.



