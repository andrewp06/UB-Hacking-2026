

class GuyController:
    def __init__(self, morphology, network):
        self.morphology = morphology
        self.network = network

    def get_inputs(self, state):
        #state is some sort of object to be recived from the physics engine including all of the info we need for the inputs
        pass

    def calculate_outputs(self, inputs):
        return self.network.activate(inputs)