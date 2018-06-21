__author__ = "Patrick B. Grinaway"
import copy
import datetime
import itertools
import os
import pkg_resources
import subprocess
from typing import List, Dict, Tuple
import yaml

#This is a simple code to automate setting up nonequilibrium switching calculations that collect shadow work

class NonequilibriumShadowExperimentSetup(object):
    """
    """

    def __init__(self, forcefield_files: List[str], 
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
        atom_selection: str="all"):
        """
        Instantiate a setup object that coordinates the construction of 
        """
        #global options that are used to decide where to put the directory structure, how to name it, etc.
        self._time_on_cluster = cluster_time
        self._n_replicates  = n_replicates
        self._project_directory = project_directory
        self._path_to_setup_script = path_to_setup_script
        
        #set up the format we will use for directory naming
        self._directory_format = "{project_name}_{timestep}fs_{switching_length}steps_{phase}_{integrator}_{replicate}"

        #load in our template LSF script, depending on how much time was requested.
        #If we need more than six hours, we'll need to use a restricted set of nodes
        if self._time_on_cluster > datetime.timedelta(hours=6):
            self._lsf_script_filename = pkg_resources.resource_filename(__name__, "data/template_long_script.sh")
        else:
            self._lsf_script_filename = pkg_resources.resource_filename(__name__, "data/template_long_script.sh")

        self._timesteps = timesteps
        self._integrator_splittings = integrator_splittings
        self._n_steps_ncmc_protocols = n_steps_ncmc_protocols
        self._project_name = project_name
        self._phase = phase
        self._n_ncmc_report = n_ncmc_report

        #this will be used to template the dictionaries that will become yaml input files
        #we're setting global settings that will not change over the combinatorial scan
        self._reference_dictionary = {
            'forcefield_files' : forcefield_files,
            'trajectory_prefix' : project_name,
            'forward_functions': forward_functions,
            'ligand_file' : os.path.abspath(ligand_file),
            'protein_pdb' : os.path.abspath(protein_pdb),
            'new_ligand_index' : new_ligand_index,
            'old_ligand_index' : old_ligand_index,
            'phases' : [phase],
            'n_cycles' : n_cycles,
            'n_equilibration_iterations' : n_equilibration_steps,
            'trajectory_directory' : 'shadow_work_test',
            'temperature' : tmeperature,
            'n_equilibrium_steps_per_iteration' : n_equilibrium_steps_per_iteration,
            'save_setup_pickle_as' : 'shadow_work.pkl',
            'atom_selection' : atom_selection,
            'pressure' : 1.0,
            'solvent_padding' : solvent_padding,
            'measure_shadow_work' : True
        }

        self._yaml_dictionaries = self._construct_combinatorial_yaml_files()



    def _construct_combinatorial_yaml_files(self) -> Dict[str, Dict]:
        """
        Given the requested input options, construct a dictionary of setup options that can be used to set up simulations.
        """
        yaml_dictionaries = {}
        #go through the entire combinatorial set of options
        for timestep in self._timesteps:
            for switching_length in self._n_steps_ncmc_protocols:
                for integrator_pair in self._integrator_splittings:
                    equilibrium_integrator = integrator_pair[0]
                    nonequilibrium_integrator = integrator_pair[1]

                    if equilibrium_integrator.find("H") > -1:
                        raise ValueError("In the integrator pairs, the integrators should be supplied as (equilibrium_integrator, nonequilibrium_integrator")
                    


                    for replicate in range(self._n_replicates):

                        #build the name of the directory, which we'll also use as a key
                        directory_name = self._directory_format.format(project_name=self._project_name, timestep=timestep, switching_length=switching_length, integrator=equilibrium_integrator.replace(" ", ""),phase=self._phase, replicate=replicate)
                        yaml_options = copy.deepcopy(self._reference_dictionary)

                        yaml_options['timestep'] = timestep
                        yaml_options['n_steps_ncmc_protocol'] = switching_length
                        yaml_options['eq_splitting'] = equilibrium_integrator
                        yaml_options['neq_splitting'] = nonequilibrium_integrator
                        
                        #this option controls how often we will write out the work values
                        yaml_options['n_steps_per_move_application'] = switching_length // self._n_ncmc_report

                        yaml_dictionaries[directory_name] = yaml_options
        
        return yaml_dictionaries

    def _build_lsf_script(self, directory_name: str) -> str:
        """
        Build the LSF submission script. If the time requested is less than 6 hours, then more nodes can be used
        
        Arguments
        ---------
        directory_name : str
            The name of the destination directory

        Returns
        -------
        lsf_script : str
            The completed LSF script
        """
        with open(self._lsf_script_filename, 'r') as templatefile:
            template_script = templatefile.read()
        
        yaml_filename = self._project_name + ".yaml"
        return template_script.format(calculation_name=directory_name, memory=8, wallclock_time=self._time_on_cluster, yaml_filename=yaml_filename, estimated_time=self._time_on_cluster, path_to_setup_script=self._path_to_setup_script)

    def write_setup_files(self):
        """
        Write all the prepared setup files to the appropriate location and prepare for job submission
        """
        #check if the intended destination path exists. If it does not, create it and move into it.
        if not os.path.exists(self._project_directory):
            os.mkdir(self._project_directory)
        
        #move into the project directory:
        os.chdir(self._project_directory)

        #for each calculation, we'll set up a folder with protein, ligand, yaml file, and submission script.
        for directory_name, yaml_dictionary in self._yaml_dictionaries.items():
            #create the directory and move into it:
            os.mkdir(directory_name)
            os.chdir(directory_name)

            #we'll build the LSF script
            lsf_script_string = self._build_lsf_script(directory_name)

            #now write it out:
            with open('submit_script.sh', 'w') as script_file:
                script_file.write(lsf_script_string)
            
            #write out the yaml file:
            yaml_filename = self._project_name + "_run.yaml"
            with open(yaml_filename, 'w') as yaml_file:
                yaml.dump(yaml_dictionary, stream=yaml_file)

            #go back to the project directory
            os.chdir(self._project_directory)

           
    def submit_all(self):
        """
        Submit all of the prepared calculations to the cluster.
        """
        #go to the project directory
        os.chdir(self._project_directory)

        for directory in os.listdir(self._project_directory):

            #move into that directory:
            os.chdir(directory)

            #read in the script file
            with open("submit_script.sh" ,"r") as submit_scriptfile:
                submit_script = submit_scriptfile.read()
            
            #submit by running bsub:
            result = subprocess.run(['bsub'], input=submit_script, check=True, stdout=subprocess.PIPE)

            print(result.stdout)

            #go back up to the project directory:
            os.chdir(self._project_directory)
            


