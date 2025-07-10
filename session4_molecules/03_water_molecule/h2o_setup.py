from nexus import settings,job,run_project,obj
from nexus import generate_physical_system

settings(
    results = '',
    sleep   = 3,
    machine = 'ws4',
    )

system = generate_physical_system(
    structure = 'H2O.xyz',
    O         = 6,                    # Zeff=6 for ccECP oxygen
    H         = 1,                    # Zeff=1 for ccECP hydrogen
    )

cores = 4
qmc_job = job(cores=cores,processes=4,threads=1)
