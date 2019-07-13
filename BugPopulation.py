
import os
import logging
import neat
from itertools import count

import BugWorld as bw
'''
This is to encapsulate the population interface.

A population will be used to hold a group of bugs for mating, fitness evaluation.  
A population will evolve separately from other populations (e.g., herbivore, carnivore, omnivore will all evolve sep)
Within a population, there is a concept of speciation (from NEAT) that allows for parallel evolution within the same
	population to discourage wiping out interesting (i.e., genetically distant) mutations before they can explore the
	solution space

Reqs:
- Population will be able to assemble to all genomes in it to be used with Neat supplied code.  Each bug has a genome
- Population will be able to identify new bugs that need to be added to the world by supplying genomes
- Population will be able to identify bug that should be removed from the World but won't will actually delete it
- Has the concept of a generation.  Each generation "runs" for a while then there is population-wide mating/mutating
- Loop through a population and control mating and thinning (e.g., use list from reproduction to alter World List)
- Episodic control on the length of a generation
- Control population based on generation/fitness or strongest survive
- Need to rebuild the population if it starts to die off (maybe use the logistic function for this?).  
	Predator/Prey dynamics

- Need to be able to create a bug from a gene (this should be in the constructor of the bug
- Need to store a gene so can start a sim from there (maybe the best one of each population?)
- Need to loop through all of the populations and have each one save itself and then return the file name so can load
	them in

- Save population states based on checkpoints


BugPopulations -- holds all of the populations of bugs that have genomes (to be used to create brains)

BugPopulation -- a single population that has all the same type of bug in it. e.g., OMN

BugPopulationInterface -- a bug must implement this interface to participate in a population

'''

'''
	- reads in the config file and stores the config for this particular population
	- maintains data related to the population
	- needs to have a fitness function associated with it.  Should be different for different populations
		 (i.e., how is a carnivore motivated vs herbivore)
	- needs to assign the reproduction method so can be called each generation if not using DefaultReproduction
	- needs to have the equivalent functionality of the inherited "run" function

'''


# a bug knows what population is belongs to because it is based off its type
# this hides all of the interaction with populations system

class BugPopulationInterface:
	""""A bug must implement this interface to participate in a population. \
		This will control what population the bug is part of and will register, deregister with the appropriate \
		population"""

	def __init__(self, bug_world, owner_bug):
		"""	bug_world: is where bug lives \
			owner_bug: is the bug that owns this interface"""

		self._bug_world = bug_world
		self._owner_bug = owner_bug

		# populations will use the owner_bug.type to try to add it to the correct population
		self._pop = bug_world.populations.register(owner_bug) #save the pop to make it easier later

	def get_population_config(self):  # will be used so NEAT config items can be used to create brains
		return self._pop.get_config()

	# populations will use the owner_bug.type to try to remove it from the population.  it does not delete the bug
	def deregister(self):
		self._pop.deregister(self._owner_bug)

#TODO Maybe use some BugWorldPopulation base class for all objs?  i.e., move plants and meat to a diff pop?

class BugPopulation:
	"""A BugPopulation holds all of the bugs of a given bug type e.g., OMN, CARN, HERB"""

	_pop_objects = []  # list of all of the bugs in the population.

	#TODO utilize the NEAT genomes here eventually
	_genomes = []  # this will be used to genomes if need be

	_bug_number = count(0)  # TODO used to give a unique number to a bug in a population.
	# usage i = next(_bug_number)

	def __init__(self, config, pop_type):
		""" config: is the NEAT config	\
			pop_type: is the type of this population"""
		#TODO add a bug_world for a call back so can instruct to add or delete a bug
		self._config = config
		self._pop_type = pop_type

	def add_to_population(self, bug):
		if bug not in self._pop_objects:  # make sure is only added once
			self._pop_objects.append(bug)

	def del_from_population(self, bug):
		"""search for the bug within the population and remove it without deleting the object. \
			This should be called when the bug is killed"""

		# find object in list and remove it
		# See article: https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating
		# somelist[:] = [x for x in somelist if not determine(x)]
		self._pop_objects = [po for po in self._pop_objects if not po == bug]

	def prune_population(self, new_genomes):  #TODO this will be used to adjust the population after reproduction
		# genomes have GUID within a population so can use as a key
		objs_to_del = []
		objs_to_add = []

		for pop_obj in self._pop_objects:  # loop through the current bug population
			#  if pop_obj.get_genome in new_genomes:  # it will stay in next population so don't need to do anything
				# pass  # this logic is covered in the next for loop section

			if pop_obj.get_genome() not in new_genomes:  # if current bug isn't in the proposed new pop, then its gotta go
				# add to list of bugs go be deleted to pass back to the world
				objs_to_del.append(pop_obj)

		for new_genome in new_genomes:  # loop through all of the genomes proposed for next population
			for pop_obj in self._pop_objects:  # loop through all bugs in current population
				if new_genome == pop_obj.get_genome():  # if it is found, then it will stay in next population
					break # break out of the inner for loop because it is found

			objs_to_add.append((self._pop_type, new_genome ))  	# if it hasn't been found, then
																# add new_genome to the list of bugs to create

		# should pass back a list of bugs need to be removed from the world.
		# should pass back a list of bugs to add to the world [(type, genome)]

		return objs_to_del, objs_to_add

	def calc_fitness(self):  # TODO will need for the reproduction
		# this where we decide what makes a good bug.  Maybe we should have different fitness by bug type
		# this should reside on the bug class
		# fitness is used for NEAT algorithm
		# it is stored on the genome in the NEAT api
		pass

	def gather_genomes(self): # TODO create genomes in the form that the NEAT library expects
		# since NEAT works on a group of genomes, put them in a form that can be passed
		genomes = []
		for pop_obj in self._pop_objects:  # loop through the current bug population
			genomes.append(pop_obj.get_genome())
		return genomes

	def force_mate(self, bug1, bug2): #TODO Phase 2 not sure if this belongs here.
		# allows the world to control mating through collisions or other events (like manually selected)
		pass


class BugPopulations:
	"""This contains all of the different populations in a given BugWorld"""
	# TODO store the config file names for each population, if not supplied use a default
	# read in and store the config params for each population

	# create a dictionary of valid types that can have brains
	populations = {}

	def __init__(self, bug_world, valid_bug_types):
		"""	bug_world: is the owner \
			valid_bug_types: is a list of all of the valid populations that will be created. Assumes is valid BWOType"""

		self._bug_world = bug_world  # call back handle to the BugWorld that holds the populations
		self._valid_types = valid_bug_types  # these are the valid bug types.  a population will be created for each one

		# for each type, create a population and read in the config for it
		# add the group to the dictionary
		for population_type in self._valid_types:
			# open config file and pass to population
			config = self.load_config_file(population_type)

			# create a new population
			pop = BugPopulation(config, population_type)
			#stats = neat.StatisticsReporter()  # TODO once implementing NEAT
			#pop.add_reporter(stats)  # TODO once implementing NEAT
			#pop.add_reporter(neat.StdOutReporter(True))  # TODO once implementing NEAT

			self.populations[population_type] = pop

	def lookup_population(self, population_type):
		"""use to encapsulate error handling for populations that are not found"""
		try:
			return self.populations[population_type]
		except KeyError:
			logging.warning("invalid population type: ", population_type)
			exit()

	def register(self, bug):
		# look up in the dictionary to get correct population
		# invoke add on that population
		pop = self.lookup_population(bug.type)
		pop.add_to_population(bug)  # intentionally crash if there isn't a pop

	def deregister(self, bug):
		pop = self.lookup_population(bug.type)
		pop.remove_from_population(bug)  # intentionally crash if there isn't a pop

	def load_config_file(self, population_type):
		# Load the config file, which is assumed to live in
		# the same directory as this script.

		local_dir = os.path.dirname(__file__)
		pop_name = bw.BWOType.get_name(population_type)
		config_file_name = pop_name + '-config-ff'

		# TODO remove this once it is being used
		config_file_name = 'BUG-config-ff'

		config_path = os.path.join(local_dir, config_file_name)

		#TODO...if file doesn't exist, try using a default config file
		config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
								neat.DefaultSpeciesSet, neat.DefaultStagnation,
								config_path)

		return config


# direct copy from the neat population code for reference...it isn't used ----------------------------------------------
'''
"""Implements the core evolution algorithm."""

from neat.reporting import ReporterSet
from neat.math_util import mean
from neat.six_util import iteritems, itervalues


class CompleteExtinctionException(Exception):
	pass


class NeatPopulation(object):
    """
    This class implements the core evolution algorithm:
        1. Evaluate fitness of all genomes.
        2. Check to see if the termination criterion is satisfied; exit if it is.
        3. Generate the next generation from the current population.
        4. Partition the new generation into species based on genetic similarity.
        5. Go to 1.
    """

    def __init__(self, config, initial_state=None):
        self.reporters = ReporterSet()
        self.config = config
        stagnation = config.stagnation_type(config.stagnation_config, self.reporters)
        self.reproduction = config.reproduction_type(config.reproduction_config,
                                                     self.reporters,
                                                     stagnation)
        if config.fitness_criterion == 'max':
            self.fitness_criterion = max
        elif config.fitness_criterion == 'min':
            self.fitness_criterion = min
        elif config.fitness_criterion == 'mean':
            self.fitness_criterion = mean
        elif not config.no_fitness_termination:
            raise RuntimeError(
                "Unexpected fitness_criterion: {0!r}".format(config.fitness_criterion))

        if initial_state is None:
            # Create a population from scratch, then partition into species.
            self.population = self.reproduction.create_new(config.genome_type,
                                                           config.genome_config,
                                                           config.pop_size)
            self.species = config.species_set_type(config.species_set_config, self.reporters)
            self.generation = 0
            self.species.speciate(config, self.population, self.generation)
        else:
            self.population, self.species, self.generation = initial_state

        self.best_genome = None

    def add_reporter(self, reporter):
        self.reporters.add(reporter)

    def remove_reporter(self, reporter):
        self.reporters.remove(reporter)

	def run(self, fitness_function, n=None):
        """
        Runs NEAT's genetic algorithm for at most n generations.  If n
        is None, run until solution is found or extinction occurs.

        The user-provided fitness_function must take only two arguments:
            1. The population as a list of (genome id, genome) tuples.
            2. The current configuration object.

        The return value of the fitness function is ignored, but it must assign
        a Python float to the `fitness` member of each genome.

        The fitness function is free to maintain external state, perform
        evaluations in parallel, etc.

        It is assumed that fitness_function does not modify the list of genomes,
        the genomes themselves (apart from updating the fitness member),
        or the configuration object.
        """

        if self.config.no_fitness_termination and (n is None):
            raise RuntimeError("Cannot have no generational limit with no fitness termination")

        k = 0
        while n is None or k < n:
            k += 1

            self.reporters.start_generation(self.generation)

            # Evaluate all genomes using the user-provided function.
            fitness_function(list(iteritems(self.population)), self.config)

            # Gather and report statistics.
            best = None
            for g in itervalues(self.population):
                if best is None or g.fitness > best.fitness:
                    best = g
            self.reporters.post_evaluate(self.config, self.population, self.species, best)

            # Track the best genome ever seen.
            if self.best_genome is None or best.fitness > self.best_genome.fitness:
                self.best_genome = best

            if not self.config.no_fitness_termination:
                # End if the fitness threshold is reached.
                fv = self.fitness_criterion(g.fitness for g in itervalues(self.population))
                if fv >= self.config.fitness_threshold:
                    self.reporters.found_solution(self.config, self.generation, best)
                    break

            # Create the next generation from the current generation.
            self.population = self.reproduction.reproduce(self.config, self.species,
                                                          self.config.pop_size, self.generation)

            # Check for complete extinction.
            if not self.species.species:
                self.reporters.complete_extinction()

                # If requested by the user, create a completely new population,
                # otherwise raise an exception.
                if self.config.reset_on_extinction:
                    self.population = self.reproduction.create_new(self.config.genome_type,
                                                                   self.config.genome_config,
                                                                   self.config.pop_size)
                else:
                    raise CompleteExtinctionException()

            # Divide the new population into species.
            self.species.speciate(self.config, self.population, self.generation)

            self.reporters.end_generation(self.config, self.population, self.species)

            self.generation += 1

        if self.config.no_fitness_termination:
            self.reporters.found_solution(self.config, self.generation, self.best_genome)

        return self.best_genome
'''