from nexus import settings,job
from nexus import generate_physical_system


settings(
    results    = '',
    sleep      = 3,
    machine    = 'ws4',
    status_only  = 0,
    )


system = generate_physical_system(
    structure = 'Be2.xyz',  
    )

cores = 4
qmc_job = job(cores=cores,processes=4,threads=1)
