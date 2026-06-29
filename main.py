from parser import Parser
from simulation import Simulation

file = "test.txt"
graph = Parser().main_parser(file)
sim = Simulation(graph)
sim.run()