#! /usr/bin/env python3

from nexus import settings,job,run_project,obj
from nexus import generate_physical_system
from nexus import generate_pyscf
from nexus import generate_convert4qmc
from h2o_setup import system, qmc_job

scf = generate_pyscf(
    identifier = 'scf',               # log output goes to scf.out
    path       = 'h2o_hf',         # directory to run in
    job        = job(serial=True),    # pyscf must run serially         
    template   = './scf_template.py', # pyscf template file
    system     = system,
    mole       = obj(                 # used to make Mole() inputs
        basis    = 'ccecp-ccpvtz',
        ecp      = 'ccecp',
        symmetry = True,
        ),
    save_qmc  = True
    )

# convert orbitals to QMCPACK format
c4q = generate_convert4qmc(
    identifier   = 'c4q',
    path         = 'H2O/hf',
    job          = job(cores=1),
    no_jastrow   = True,
    hdf5         = True,              # use hdf5 format
    dependencies = (scf,'orbitals'),
    )

# collect dependencies relating to orbitals
orbdeps = [(c4q,'particles'), # pyscf changes particle positions
           (c4q,'orbitals' )]


run_project()
