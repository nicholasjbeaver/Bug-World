import logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

"""
Collision API

	CollisionInterface() - objects that want to participate in collisions must implement one of these
	CollisionGroup() - container for the list of objects that can collide.
						There are two types of objects in a Group: emitters and detectors.  Detectors only detect things in the emitters list.
	CollisionMatrix() - so can contain the dictionary and then the logic to invoke the methods.  Would also do error checking
						allows the extraction of different types of collision data
	Collisions() - contains all of the CollisionGroups and defines the different valid CollisionTypes

	Usage:
		1) Create an interface object on the object that is to participate (CO)
		2) The CO is responsible for know what collisions it needs to register for
		3) The CO must have a pointer to its container.  This allows a recursive search to make sure it isn't "colliding" with itself
		4) The CO must have a callback method to call when they do collide with something
		5) The CO shouldn't asked to be removed from the lists when it is marked from deletion.

"""


class CollisionInterface:
	"""Encapsulates everything an object needs to participate in collisions"""
	_emitter = 'emitter'
	_detector = 'detector'

	def __init__(self, collisions, owner):
		self.collisions = collisions  #the container for all collisions
		self.collision_registration_list = []  # this holds all of the registrations an object has registered for
		self.owner = owner  # This is the ultimate owner of all of the sub-components...very top of hierarchy

	def register_as_emitter(self, collision_object, collision_type):
		if collision_type not in self.collisions.valid_types:
			logging.error("Unsupported collision type: ", collision_type)
			return
		else:
			self.collisions.register_emitter(collision_object, collision_type)
			self.collision_registration_list.append((collision_object, collision_type, self._emitter))

	def register_as_detector(self, collision_object, collision_type):
		if collision_type not in self.collisions.valid_types:
			logging.error("Unsupported collision type: ", collision_type)
			return
		else:
			self.collisions.register_detector(collision_object, collision_type)
			self.collision_registration_list.append((collision_object, collision_type, self._detector))

	def deregister_all(self):
		for collision_object, collision_type, emitter_or_detector in self.collision_registration_list:
			if emitter_or_detector == self._emitter:
				self.collisions.deregister_emitter(collision_object, collision_type)
			else:
				self.collisions.deregister_detector(collision_object, collision_type)

		self.collision_registration_list.clear()
		self.collisions = None
		self.owner = None

	def is_this_me(self, co2):
		if self.owner == co2.ci.owner:
			return True
		else:
			return False


class CollisionGroup:
	"""A group is all of the emmitters and detectors for a particular sensor (i.e., type) e.g., physical or visual"""

	def __init__(self, handler_method):
		""" handler_method is the method to call when a detector collides with an emitter """
		self._emitters = []
		self._detectors = []
		self._enabled = True  # can be used to ignore a certain type of collisions
		self._cb = handler_method

	def __repr__(self):
		return 'Emitters(' + str(len(self._emitters)) + '): ' + ' '.join(map(str, self._emitters )) + '\n' + 'Detectors: ' + ' '.join(map(str, self._detectors))

	def enable_collisions(self):
		""" Sets a state such that the collisions of this group will be checked """
		self._enabled = True

	def disable_collisions(self):
		""" Sets a state such that the collisions of this group will be checked """
		self._enabled = False

	def set_handler(self, handler):
		self._cb = handler

	def add_emitter(self, collision_object):
		self._emitters.append(collision_object)

	def add_detector(self, collision_object):
		self._detectors.append(collision_object)

	def del_emitter(self, collision_object):
		#find object in list and remove it
		#should be called in the destructor method so that it is removed from all lists
		#See article: https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating
		#somelist[:] = [x for x in somelist if not determine(x)]
		self._emitters = [co for co in self._emitters if not co == collision_object]

	def del_detector(self, collision_object):
		self._detectors = [co for co in self._detectors if not co == collision_object]

	def circle_collision(self, co1, co2):
		"""takes two objects presumed to have a center and a size circle."""

		dx = co1.get_abs_x() - co2.get_abs_x()
		dy = co1.get_abs_y() - co2.get_abs_y()

		dist_sqrd = (dx * dx) + (dy * dy)

		#size is assummed to be the radius of object's circular hit box
		if dist_sqrd < (co1.get_size() + co2.get_size())**2:
			return True
		else:
			return False

	def detect_collisions(self):
		if not self._enabled:
			return

		#loop through solid bodies
		#call collision handlers on each object
		for co1 in self._detectors:
			for co2 in self._emitters:
				if co1.ci.is_this_me(co2):
					continue #make sure the object is not part of the bug that owns it
				elif self.circle_collision(co1, co2):
					logging.debug("Detector: " + co1.name + " detected Emitter:" + co2.name )
					self._cb(co1, co2) #call the callback handler


class CollisionMatrix:
	"""This class encapsulates what happens between two objects once the collision is detected"""

	def __init__(self, collision_dictionary):
		self.collision_dictionary = collision_dictionary

	def invoke_handler(self, detector, emitter):
		self.print_collision(detector, emitter)
		collision_data = self.extract_collision_data(detector, emitter)
		try:
			self.collision_dictionary[(detector.type, emitter.type)](detector, emitter)  # use types to lookup function to call and then call it
		except KeyError:
			logging.warning('No handler for: ' + detector.name + ' T:' + str(detector.type) + ", " + emitter.name + ' T:' + str(emitter.type))

	def extract_collision_data(self, detector, emitter):
		"""
			can be overwritten so that different collisions can return different data.
			expected return is a dictionary of name-value pairs
			by default it returns a dictionary containing the distance between the two objects squared
			leaving as an instance method in case there is a subclass instance variable that needs to be accessed
		"""
		dx = detector.get_abs_x() - emitter.get_abs_x()
		dy = detector.get_abs_y() - emitter.get_abs_y()
		dist_sqrd = (dx * dx) + (dy * dy)
		return {'dist_sqrd':dist_sqrd}

	def print_collision(self, OB1, OB2):
		logging.debug(OB1.name + ' T:' + str(OB1.type) + ", " + OB2.name + ' T:' + str(OB2.type))
		pass


class Collisions:
	"""This contains all of the collision groups, detection between objects"""

	PHYSICAL = 'physical'
	VISUAL = 'visual'
	valid_types = [PHYSICAL, VISUAL] #"sound, smell, communication, click
	collision_groups = {}

	def default_handler(self, *kwargs ):  # this should only be called if no handler is set for a collision group.
		logging.error("Error, no handler set for the group.  Need to instantiate a CollisionMatrix and assign handler")

	def __init__(self):
		#for each type, create a group
		#add the group to the dictionary
		for collision_type in Collisions.valid_types:
			self.collision_groups[collision_type] = CollisionGroup(self.default_handler)  #add a collision group

	def lookup_group(self, collision_type):
		"""use to encapsulate error handling for groups that are found"""
		try:
			return self.collision_groups[collision_type]
		except KeyError:
			logging.warning("invalid collision type: ", collision_type)
			exit()

	def set_collision_handler(self, collision_type, handler):
		"""this is used so a particular collision type can set the specific handler to set the collision data."""
		group = self.lookup_group(collision_type)
		group.set_handler(handler)

	def register_emitter(self, collision_object, collision_type):
		#look up in the dictionary to get correct group
		#invoke add emitter on that group
		group = self.lookup_group(collision_type)
		group.add_emitter(collision_object)

	def register_detector(self, collision_object, collision_type):
		group = self.lookup_group(collision_type)
		group.add_detector(collision_object)

	def deregister_emitter(self, collision_object, collision_type):
		group = self.lookup_group(collision_type)
		group.del_emitter(collision_object)

	def deregister_detector(self, collision_object, collision_type):
		group = self.lookup_group(collision_type)
		group.del_detector(collision_object)

	def detect_collisions(self):
		#loop through all of the groups and check for collisions
		for collision_type, collision_group in self.collision_groups.items():
			collision_group.detect_collisions()


# --- Testing Code after this point --------------------------------------------------------------------------------

'''
	For an object to participate in must implement the CollisionsInterface
	For the world to process collisions, a Collisions object must be created
	For each type of collision, define a collision matrix that determines what methods to call and contains implementaions
'''

class CTOType:  #similar to BugWorldTypes
	#use integers so it is faster for dict lookups
	OBJ = int(1)  #catch all for the base class.  Shouldn't ever show up
	BUG = int(2)  #handles any bug interaction
	HERB = int(3) # Herbivore
	OMN = int(4)  # Omnivore
	CARN = int(5) # Carnivore 
	OBST = int(6) # Obstacle
	MEAT = int(7) # Food for Carnivore and Omnivore
	PLANT = int(8)# Food for Herbivore and Omnivore
	EYE = int(9)  # An eye that used for visual detection	


class CollisionTestObject: #simlar to BugWorldObject

	def __init__(self, collisions, name, x, y, size):
		self.type = CTOType.OBJ #needs to be overwritten
		self.name = name
		self.x = x
		self.y = y
		self.size = size
		self.ci = CollisionInterface(collisions, self)

	def __repr__(self):
		return self.name

	def get_abs_x(self):
		return self.x

	def get_abs_y(self):
		return self.y

	def get_size(self):
		return self.size

	def kill(self):
		self.ci.deregister_all()
		logging.debug('About to die: ' + self.name)


class CollisionTestBody(CollisionTestObject):

	def __init__(self, collisions, name, test_type, x, y, size):
		super().__init__(collisions, name, x, y, size)
		self.type = test_type

		self.ci.register_as_emitter(self, 'visual')
		self.ci.register_as_emitter(self, 'physical')
		self.ci.register_as_detector(self, 'physical')


class CollisionTestEye(CollisionTestObject):
	def __init__(self, collisions, owner, name, x, y, size):
		super().__init__(collisions, name, x, y, size)
		self.type = CTOType.EYE
		self.ci.owner = owner
		self.ci.register_as_detector(self, 'visual')


class PhysicalCollisionMatrix(CollisionMatrix):

	def __init__(self, collisions):
		super().__init__(self.get_collision_dictionary())
		self.collisions = collisions
		self.collisions.set_collision_handler('physical', self.invoke_handler)

	def herb_carn(self, herb, carn):
		self.print_test_message(herb,carn)

	def carn_herb(self, carn, herb):
		self.print_test_message(carn,herb)

	def herb_herb(self, herb1, herb2):
		self.print_test_message(herb1,herb2)

	def carn_carn(self, carn1, carn2 ):
		self.print_test_message(carn1,carn2)

	def get_collision_dictionary(self):
		cd = { # look up which function to call when two objects of certain types collide
			(CTOType.HERB, CTOType.CARN): self.herb_carn,
			(CTOType.HERB, CTOType.HERB): self.herb_herb,
			(CTOType.CARN, CTOType.CARN): self.carn_carn,
			(CTOType.CARN, CTOType.HERB): self.carn_herb,
			}
		return cd

	def print_test_message(self, obj1, obj2):
		logging.debug("handling: ", obj1.name, " + ", obj2.name)

class VisualCollisionMatrix(CollisionMatrix):

	def __init__(self, collisions):
		super().__init__(self.get_collision_dictionary())
		self.collisions = collisions
		self.collisions.set_collision_handler('visual', self.invoke_handler)

	def bug_eye(self, bug, eye):
		self.print_test_message(bug,eye)

	def get_collision_dictionary(self):
		cd = {  # look up which function to call when two objects of certain types collide
			(CTOType.EYE,CTOType.HERB ): self.bug_eye,
			(CTOType.EYE,CTOType.CARN ): self.bug_eye,
		}
		return cd

	def print_test_message(self, obj1, obj2):
		logging.debug("handling: ", obj1.name, " + ", obj2.name)


class CollisionTestWorld():  # Similar to BugWorld

	Bodies = []
	Eyes = []

	def __init__(self):
		self.collisions = Collisions()
		self.vcm = VisualCollisionMatrix(self.collisions)
		self.pcm = PhysicalCollisionMatrix(self.collisions)

	def add_bodies(self):
		#x, y, size 
		locs = [[CTOType.HERB,0,0,5], [CTOType.HERB, 7,0,5], [CTOType.CARN, 9,5,3], [CTOType.HERB,6,3,2]]
		ctr = 0

		for pos in locs:
			ctr += 1
			name = "body" + str(ctr)
			self.Bodies.append(CollisionTestBody(self.collisions, name, *pos))

	def add_eyes(self):
		#x, y, size 
		locs = [(-2,0,2), (5,0,2), (0,-20, 2)]
		ctr = 0

		for pos in locs:
			ctr += 1
			name = "Eye" + str(ctr)
			self.Eyes.append(CollisionTestEye(self.collisions, None, name, *pos))

	def del_body( Self ):
#TODO - not sure this is correct way of handling...really 
		#delete first object in list to see if destructors are called
		to_kill = Self.Bodies[0]
		to_kill.kill()
		Self.Bodies[:] = Self.Bodies[2:]
		del to_kill

	def test_all(self):
		#add the elements to the World

		logging.debug("--- before any adds ---")
		self.add_bodies()
		logging.debug("--- after add bodies ---")

		self.add_eyes()
		logging.debug("--- after add eyes ---")

		self.collisions.detect_collisions()
		logging.debug("After Collision Check")
		logging.debug()

		self.del_body()
		logging.debug("After delete body")

		#Test cases

		#See if they were added properly

		#See if there are collisions

		#Delete an item ... make sure it isn't something iterating over

		#See if it was removed from the collision list

		#See if there collisions

		#Add another item
		#handle two subclasses colliding....eg carn,herb


	#test recursive isThisMe

	#test adding handler methods

	#test hitbox type checking

	#test bad cases: empty lists, wrong types, no handler, no bounding box type

	#test logging/printing

	#for eyes, sound etc, register only the closest one if multiple collisions

	

if __name__ == "__main__":
	g = CollisionTestWorld()
	g.test_all()
