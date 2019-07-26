
import logging
import numpy as np
import random

import BugWorld as bw
import Collisions as coll
import BugPopulation as pop
import BugBrain as bb

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class BugEyeHitbox(bw.BWObject):
	"""This object is mounted on an eye so it can be offset and larger than the physical eye"""

	def __init__(self, bug_world, owner, pos_transform, size=15,name="EHB"):
		self.name = name
		# position should be center of eye + radius of hitbox
		super().__init__(bug_world, pos_transform, self.name)
		self.size = size
		self.color = bw.Color.GREY
		self.default_color = self.color
		self.type = bw.BWOType.EHB
		self.owner = owner
		self.ci = coll.CollisionInterface(bug_world.collisions, owner)
		self.ci.register_as_detector(self, coll.Collisions.VISUAL)

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base)  # update it based on the passed in ref frame

	def draw(self, surface):
		super().draw(surface, 1)  # the 1 says to draw the outline only
		self.color = self.default_color


class BugEye(bw.BWObject):

	def __init__(self, bug_world, owner, pos_transform, size=1, name="E"):
		self.name = name
		super().__init__(bug_world, pos_transform, name)
		self.size = size
		self.color = bw.Color.BLACK
		self.default_color = self.color
		self.type = bw.BWOType.EYE
		self.owner = owner
		self.HITBOX_SIZE = self.size * 5

		# add the eye hitbox for the current eye
		# put hitbox so tangent with eye center...actually add 1 so avoid collision with bug just for efficiency
		self.HITBOX_LOC = bw.BugWorld.get_pos_transform((self.HITBOX_SIZE + 1), 0, 0, 0)
		self.add_subcomponent(BugEyeHitbox(bug_world, owner, self.HITBOX_LOC, self.HITBOX_SIZE, name))

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base) #update it based on the passed in ref frame
		self.update_subcomponents(self.abs_position)


class Bug(bw.BWObject):
	"""Abstract base class.  All bugs in the BugWorld must be of this type
		Bug is made up of different parts:
		body, left eye, right eye,

		Phase 2
			left ear, right ear, antenna, nose, gland (to emit odor), speaker (to emit sound)
		Phase 3
			display text

		most of these are Subcomponents because they have hitboxes"""

	DEFAULT_TURN_AMT = np.deg2rad(30)  	# turns are in radians, used for random moving
	DEFAULT_MOVE_AMT = 5				# used for random moving

	def __init__(self, bug_world, initial_pos, name="Bug", genome=None, bug_type=None):
		super().__init__(bug_world, initial_pos, name)
		self.size = 10  # override default and set the intial radius of bug
		self.color = bw.Color.PINK  # override default and set the initial color of a default bug
		self.default_color = self.color
		self.default_energy = 100
		self.default_health = 100
		self.default_score = 0
		self.energy = self.default_energy  # default...needs to be overridden
		self.health = self.default_health
		self.score = self.default_score  # used to reinforce behaviour.  Add to the score when does a "good" thing
		self.owner = self
		self.vel_r = 0  # to store state
		self.vel_l = 0  # to store state

		if not bug_type:  # if none passed it, set it to default
			bug_type = bw.BWOType.BUG
		self.type = bug_type

		# participate in the collision system
		self.ci = coll.CollisionInterface(bug_world.collisions, self.owner)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)  	# can be hit
		self.ci.register_as_detector(self, coll.Collisions.PHYSICAL) 	# can detect hitting something
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)		# can be seen

		# participate in the population system.
		self.pi = pop.BugPopulationInterface(bug_world, self, genome)  # uses bug_type

		# interface to the brain...requires config if using NEAT
		# population interface must be instantiated first
		config = self.pi.get_population_config()
		genome = self.pi.get_genome()
		self.bi = bb.BugBrainInterface(self, config, genome)

		# add the eyes for a default bug
		# put eye center on circumference of bug body, rotate then translate.
		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(-30))
		tT = bw.BugWorld.get_pos_transform(self.size, 0, 0, 0)
		self.RIGHT_EYE_LOC = np.matmul(rT, tT)

		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(30))
		self.LEFT_EYE_LOC = np.matmul(rT, tT)

		self.EYE_SIZE = int(self.size * 0.50)  # set a percentage the size of the bug

		# instantiate the eyes
		self.add_subcomponent(BugEye(bug_world, self.owner, self.RIGHT_EYE_LOC, self.EYE_SIZE,"R"))
		self.add_subcomponent(BugEye(bug_world, self.owner, self.LEFT_EYE_LOC, self.EYE_SIZE,"L"))

	def calc_fitness(self):
		logging.warning("must override fitness method to calculate appropriate fitness for a given bug")
		# default_fitness = self.energy*self.health*self.score
		default_fitness = self.energy*self.score
		return default_fitness

	def reset_fitness(self):
		self.energy = self.default_energy
		self.score = self.default_score
		self.health = self.default_health

	def update(self, base):
		# uncomment this to not use the brain
		# self.kinematic_wander()

		# TODO implement the brain interface to control motion here
		# update the brain with the velocity from the last cycle
		self.bi.update_brain_inputs({"vel_r":self.vel_r, "vel_l":self.vel_l})

		# call the brain to update the velocities
		self.vel_r, self.vel_l = self.bi.activate()

		#  use the velocities and the kinematic model to move the bug
		delta_x, delta_y, delta_theta = self.kinematic_move(self.vel_r, self.vel_l)  # assume bugbot with two wheels
		dist_moved = delta_x + delta_y  # want to reward for forward movement so use actual values

		self.set_abs_position(base)

		# update subcomponents
		self.update_subcomponents(self.abs_position)

		#update the score for this iteration
		self.update_score(dist_moved)  # reward for forward movement

		#update the energy used for this iteration
		amt = abs(dist_moved)+abs(delta_theta)  # it costs energy to move or rotate
		self.update_energy(amt)

	def update_score(self, dist_moved):
		"""override this method to change how a bug's score is calculated"""
		self.score += dist_moved

	def update_energy(self, dist_moved):
		"""override this method to change how a bug's energy is calculated"""
		self.energy -= dist_moved

	def kill(self):  # overridden to include bug specific stuff
		super().kill()
		try:
			self.pi.deregister()  # if part of a population, deregister it
		except:
			pass


	############ Movement stuff #######################
	def move_forward(self, amount_to_move=DEFAULT_MOVE_AMT):
		# assume bug's 'forward' is along the x direction in the bug's local coord frame
		tM = bw.BugWorld.get_pos_transform(x=amount_to_move, y=0, z=0, theta=0)  # create an incremental translation
		self.set_rel_position(np.matmul(self.rel_position, tM))  # update the new position

	def turn_left(self, theta=DEFAULT_TURN_AMT):
		rM = bw.BugWorld.get_pos_transform(x=0, y=0, z=0, theta=theta)  # create an incremental rotation
		self.set_rel_position(np.matmul(self.rel_position, rM))  # update the new position

	def turn_right(self, theta=DEFAULT_TURN_AMT):
		# 'turning right is just a negative angle passed to turn left'
		self.turn_left(-theta)

	def wander(self):
		"""this method deprecated. use the kinematics of the bug instead"""
		rand_x = random.randint(0, Bug.DEFAULT_MOVE_AMT)
		rand_theta = random.uniform(-Bug.DEFAULT_TURN_AMT, Bug.DEFAULT_TURN_AMT)
		wM = bw.BugWorld.get_pos_transform(x=rand_x, y=0, z=0, theta=rand_theta)  # create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position

	def kinematic_wander(self):
		rand_vr = random.uniform(-.5, 1)  # random right wheel velocity normalized
		rand_vl = random.uniform(-.5, 1)  # biased to move forward though
		# eventually will be driven by a neuron

		delta_x, delta_y, delta_theta = self.kinematic_move(rand_vr, rand_vl)
		wM = bw.BugWorld.get_pos_transform(x=delta_x, y=delta_y, z=0, theta=delta_theta)  # create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position

	def kinematic_move(self, vel_r, vel_l):  # assume bugbot with two wheels on each side of it.
		# taken from GRIT robotics course
		wheel_radius = self.size * 0.5  # wheel radius is some proportion of the radius of the body
		wheel_separation = self.size * 2  # wheels are separated by the size of the bug
		delta_theta = (wheel_radius / wheel_separation) * (vel_r - vel_l)
		temp_vect = (wheel_radius / 2) * (vel_r + vel_l)
		delta_x = temp_vect * np.cos(delta_theta)
		delta_y = temp_vect * np.sin(delta_theta)
		wM = bw.BugWorld.get_pos_transform(x=delta_x, y=delta_y, z=0, theta=delta_theta)  # create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position
		return delta_x, delta_y, delta_theta




