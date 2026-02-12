from enum import Enum
import re
from vitamin_model_checker.models.costCGS.costCGS import costCGS  # ajusta el import si tu ruta es distinta

class TimedCGS(costCGS):
    def __init__(self):
        super().__init__()
        self.clock_constraints_dict = {}
        self.clocks_dict = {}
        self.clocks = []

    def read_file(self, filename):
        # 1) parse base CGS (states, labels, transitions)
        super().read_file(filename)

        with open(filename, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f.readlines()]

        # 2) SAFE parse of Clocks section (always rebuild clocks_dict)
        self.clocks = []
        self.clocks_dict = {}
        if "Clocks" in lines:
            idx = lines.index("Clocks")
            # find next non-empty line
            j = idx + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines):
                self.clocks = lines[j].split()
                self.clocks_dict = {c: i for i, c in enumerate(self.clocks)}

        if not self.clocks_dict:
            raise ValueError("Clocks section not found or empty. Cannot build clocks_dict.")

        # 3) init timed structures
        n = len(self.states)
        self.clock_constraint_struct = [[''] * n for _ in range(n)]
        self.invariants_arr = [[] for _ in range(n)]

        # 4) parse Clock_constraints + Invariants
        current = None
        row_index = 0

        for ln in lines:
            if ln == "Clock_constraints":
                current = "Clock_constraints"
                row_index = 0
                continue
            if ln == "Invariants":
                current = "Invariants"
                row_index = 0
                continue
            if ln in ("Transition", "Name_State", "Initial_State", "Atomic_propositions", "Labelling", "Number_of_agents", "Clocks"):
                current = None
                continue
            if not ln:
                continue

            if current == "Clock_constraints":
                vals = ln.split()
                self._parse_clock_constraints(vals, row_index)
                row_index += 1

            elif current == "Invariants":
                vals = ln.split()
                self._parse_invariants(vals, row_index)
                row_index += 1

    def _parse_clock_constraints(self, line: list[str], row: int):
        for col, constraint in enumerate(line):
            parts = constraint.split(',')
            for part in parts:
                if re.search(r'(\w+)(=|>|>=|==|<|<=)(\d+)', part):
                    if len(self.clock_constraint_struct[row][col]) > 0:
                        self.clock_constraint_struct[row][col] += f",{part}"
                    else:
                        self.clock_constraint_struct[row][col] = str(part)

    def _parse_invariants(self, line: list[str], location: int):
        for value in line:
            invariants = value.split(',')
            for invariant in invariants:
                m = re.match(r'(\w+)(?:<=|<)(\d+)', invariant)
                if m:
                    self.invariants_arr[location] += [m.group(1), float(m.group(2))]

class Sections(Enum):
    CLOCKS = 'Clocks',
    CLOCK_CONSTRAINTS = 'Clock_constraints',
    INVARIANTS = 'Invariants',
    UNKNOWN = 'Unknown'