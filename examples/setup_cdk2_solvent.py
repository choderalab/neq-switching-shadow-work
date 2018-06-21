import neq_switching_shadow_work
import datetime

"""

forcefield_files: List[str], 
        project_name: str,
        project_directory: str,
        path_to_setup_script: str,
        forward_functions: Dict[str, str],
        ligand_file: str,
        protein_pdb: str,
        new_ligand_index: int,
        old_ligand_index: int,
        phase: str,
        n_cycles: int,
        n_replicates: int,
        n_equilibration_steps: int,
        n_equilibrium_steps_per_iteration: int,
        solvent_padding: float,
        tmeperature: float,
        cluster_time: datetime.timedelta,
        n_ncmc_report: int,
        n_steps_ncmc_protocols: List[int],
        integrator_splittings: List[Tuple[str, str]],
        timesteps: List[float],        
        atom_selection: str="all"
"""

forward_functions = {
        'lambda_sterics': 'lambda',
        'lambda_electrostatics': 'lambda',
        'lambda_bonds': 'lambda',
        'lambda_angles': 'lambda',
        'lambda_torsions': 'lambda'
    }
if __name__=="__main__":
    neq_shadow_setup = neq_switching_shadow_work.setup_neq_switching.NonequilibriumShadowExperimentSetup(['gaff.xml', 'amber99sbildn.xml', 'tip3p.xml'], 
    "cdk2_expt", 
    "/data/chodera/pgrinaway/automated_solvent_shadow_one",
    "/home/pgrinaway/perses/scripts/setup_relative_calculation.py",
    forward_functions,
    "CDK2_ligands.mol2",
    "CDK2_fixed_nohet.pdb",
    14,
    15,
    "solvent",
    200,
    20,
    100,
    1000,
    9.0,
    300.0,
    datetime.timedelta(hours=5.5),
    5,
    [1000, 5000, 10000, 20000, 50000, 100000],
    [("V R O R V", "V R O H R V"), ("O V R V O", "O V R H V O"), ("R V O V R", "R V O H V R")],
    [0.5, 1.0, 1.5, 2.0, 2.5]
    )
    
    #write the submission files
    neq_shadow_setup.write_setup_files()