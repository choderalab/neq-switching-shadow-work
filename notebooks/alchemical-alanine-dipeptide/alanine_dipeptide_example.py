import numpy as np
import openmmtools
from openmmtools.constants import kB
from simtk import openmm as mm
from simtk.openmm import app
from tqdm import tqdm

# Versions helpful for debugging
print('openmmtools version: {}'.format(openmmtools.version.full_version))
print('openmm version: {}'.format(mm.version.full_version))

# Set some global variables
from simtk import unit
temperature = 298 * unit.kelvin
beta = 1.0 / (kB * temperature)
n_samples = 1000

# Use pre-generated samples from the 298K ensemble of alaninedipeptide with HBonds constrained
import mdtraj as md
alanine_constrained_samples = md.load('alanine_dipeptide_constrained_samples.h5')
sample_cache = alanine_constrained_samples.xyz * unit.nanometer
testsystem = openmmtools.testsystems.AlchemicalAlanineDipeptide()


# Define what will be variable during the experiments
splittings = {'VVVR (OVR-H-RVO)': 'O V R H R V O',
              'BAOAB-mid (VRO-H-RV)': 'V R O H R V',
              'BAOAB-end (VRORV-H)': 'V R O R V H',
              # 'velocity-verlet-mid (VR-H-RV)': 'V R H R V', # requires to disable LangevinIntegrator splitting checks
              # 'velocity-verlet-end (VRV-H)': 'V R V H', # requires to disable LangevinIntegrator splitting checks
              }

switching_times = np.array([0.1, 0.5, 1.0]) * unit.picoseconds
timesteps = np.array([1.0, 2.0, 3.0, 4.0, 5.0]) * unit.femtosecond


# Enumerate all the experiment conditions in a certain order
conditions = []
from collections import namedtuple
Condition = namedtuple('Condition', ['timestep', 'switching_time', 'n_switching_steps', 'splitting'])

for timestep in timesteps[::-1]:
    for switching_time in switching_times:
        for splitting in splittings:
            n_switching_steps = int(switching_time / timestep)
            conditions.append(Condition(
                timestep=timestep,
                switching_time=switching_time,
                n_switching_steps=n_switching_steps,
                splitting=splitting)
            )
print('# of conditions in this experiment: {}'.format(len(conditions)))


def collect_samples_at_condition(condition):
    print(condition)

    timestep = condition.timestep
    n_switching_steps = condition.n_switching_steps
    splitting = splittings[condition.splitting]

    integrator = openmmtools.integrators.AlchemicalNonequilibriumLangevinIntegrator(
        alchemical_functions={'lambda_electrostatics': '1-lambda'},
        splitting=splitting,
        measure_heat=True,
        measure_shadow_work=False,
        nsteps_neq=n_switching_steps,
        collision_rate=1.0 / unit.picoseconds,
        timestep=timestep,
        temperature=temperature,
    )

    sim = app.Simulation(testsystem.topology, testsystem.system, integrator,
                         platform=mm.Platform.getPlatformByName("Reference"))

    # store in reduced units...
    w_shads = np.zeros(n_samples)
    w_prots = np.zeros(n_samples)
    w_tots = np.zeros(n_samples)
    reduced_DeltaEs = np.zeros(n_samples)

    for i in tqdm(range(n_samples + 1)):
        if i > 1: i -= 1 # discard first sample

        # set initial (x,v) from equilibrium
        x0 = sample_cache[np.random.randint(len(sample_cache))]
        sim.context.setPositions(x0)
        sim.context.setVelocitiesToTemperature(temperature)

        # reset the relevant integrator state
        sim.integrator.reset()
        sim.integrator.setGlobalVariableByName('lambda', 0)
        sim.integrator.setGlobalVariableByName('lambda_step', 0)

        # get the total energy before switching
        state_0 = sim.context.getState(getEnergy=True)
        E_0 = state_0.getPotentialEnergy() + state_0.getKineticEnergy()

        # perform switching
        sim.step(n_switching_steps)

        # get the total energy change
        state_1 = sim.context.getState(getEnergy=True)
        E_1 = state_1.getPotentialEnergy() + state_1.getKineticEnergy()
        DeltaE = (E_1 - E_0)
        reduced_DeltaEs[i] = beta * DeltaE

        # get the heat and protocol work, derive total work, shadow work
        W_prot = integrator.get_protocol_work()
        w_prots[i] = beta * W_prot

        Q = integrator.get_heat()

        w_tots[i] = beta * (DeltaE - Q + W_prot)
        w_shads[i] = w_tots[i] - w_prots[i]

    result = {'w_shads': w_shads,
              'w_tots': w_tots,
              'w_prots': w_prots,
              'reduced_DeltaEs': reduced_DeltaEs
              }
    return result


def save_result(experiment_id, condition, result):
    from pickle import dump
    fname = str(experiment_id) + '.pkl'
    with open(fname, 'wb') as f:
        dump({'condition': condition, 'result': result}, f)


if __name__ == '__main__':

    import sys

    try:
        job_id = int(sys.argv[1])
        experiment_id = job_id - 1

    except:
        print("No valid job_id supplied! Selecting one at random")
        experiment_id = np.random.randint(len(conditions))

    condition = conditions[experiment_id]
    result = collect_samples_at_condition(condition)
    print(result)
    save_result(experiment_id=experiment_id, condition=condition, result=result)
