import numpy as np
from vitamin_model_checker.models.CGS.CGS import CGS

class costCGS(CGS):
    def __init__(self):
        super().__init__()
        self.costs = []
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

    def read_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

        current_section = None
        rows_graph = []
        rows_prop = []

        for line in lines:
            line = line.strip()

            # CRITICAL: ignore empty lines (prevents [] rows in Transition/Labelling)
            if not line:
                continue

            # Section headers
            if line == 'Transition':
                current_section = 'Transition'
                continue
            elif line == 'Transition_With_Costs':
                current_section = 'Transition'
                self.usesCostsInsteadOfActions = True
                continue
            elif line == 'Unkown_Transition_by':
                current_section = 'Unknown_Transition_by'
                continue
            elif line == 'Name_State':
                current_section = 'Name_State'
                continue
            elif line == 'Initial_State':
                current_section = 'Initial_State'
                continue
            elif line == 'Atomic_propositions':
                current_section = 'Atomic_propositions'
                continue
            elif line == 'Labelling':
                current_section = 'Labelling'
                continue
            elif line == 'Number_of_agents':
                current_section = 'Number_of_agents'
                continue
            elif line == 'Costs_for_actions':
                current_section = 'Costs_for_actions'
                continue
            elif line == 'Costs_for_actions_split':
                current_section = 'Costs_for_actions_split'
                continue

            # Section contents
            if current_section == 'Transition':
                rows_graph.append(line.split())

            elif current_section == 'Unknown_Transition_by':
                # not used in this simplified pipeline
                pass

            elif current_section == 'Name_State':
                values = line.split()
                self.states = np.array(values)

            elif current_section == 'Initial_State':
                self.initial_state = line

            elif current_section == 'Atomic_propositions':
                values = line.split()
                self.atomic_propositions = np.array(values)

            elif current_section == 'Labelling':
                rows_prop.append(line.split())

            elif current_section == 'Number_of_agents':
                self.number_of_agents = line

            elif current_section == "Costs_for_actions":
                values = line.split()
                action_name = values[0]
                state_and_cost_string = values[1].split(";")
                for couple in state_and_cost_string:
                    state_and_cost = couple.split("$")
                    costs = [int(c) for c in state_and_cost[1].split(':')]
                    self.cost_for_action.update({
                        self.translate_action_and_state_to_key(action_name, state_and_cost[0]): costs
                    })

            elif current_section == "Costs_for_actions_split":
                values = line.split()
                action_name = values[0]
                state_and_cost_string = values[1].split(";")
                for couple in state_and_cost_string:
                    state_and_cost = couple.split("$")
                    costs_res = state_and_cost[1].split(':')
                    costs = [[int(cc) for cc in c.split(',')] for c in costs_res]
                    self.cost_for_action.update({
                        self.translate_action_and_state_to_key(action_name, state_and_cost[0]): costs
                    })

        # Normalize Transition matrix to N x N BEFORE np.array(...)
        N = len(self.states)
        if N == 0:
            raise ValueError("Name_State section missing or empty.")

        # Keep only first N rows, pad/truncate each row to length N
        rows_graph = rows_graph[:N]
        rows_graph = [
            (row[:N] + ["0"] * max(0, N - len(row)))
            for row in rows_graph
        ]
        grafo_prov = np.array(rows_graph, dtype=object)

        # Build graph
        actions = []
        for row in grafo_prov:
            new_row = []
            for item in row:
                if item == '0':
                    new_row.append(0)
                else:
                    if self.usesCostsInsteadOfActions:
                        new_row.append(item)
                    else:
                        new_row.append(str(item))
                        parts = str(item).split(",")
                        for elem in parts:
                            actions.append(elem)
            self.graph.append(new_row)

        #  Normalize Labelling matrix to N x P
        P = len(self.atomic_propositions)
        rows_prop = rows_prop[:N]
        rows_prop = [
            (row[:P] + ["0"] * max(0, P - len(row)))
            for row in rows_prop
        ]
        matrix_prop_prov = np.array(rows_prop, dtype=object)

        for row in matrix_prop_prov:
            new_row = []
            for item in row:
                if item == '0':
                    new_row.append(0)
                elif item == '1':
                    new_row.append(1)
                else:
                    new_row.append(str(item))
            self.matrix_prop.append(new_row)

    def read_from_model_object(self, model):
        super(costCGS, self).read_from_model_object(model)
        self.capacities_assignment = model.capacities_assignment
        self.action_capacities = model.actions_for_capacities
        self.capacities = np.array(model.capacities)
        self.cost_for_action = model.cost_for_action

    def get_cost_for_action(self, action, state):
        return self.cost_for_action[self.translate_action_and_state_to_key(action, state)]

    def get_cost_for_action_all(self):
        return self.cost_for_action