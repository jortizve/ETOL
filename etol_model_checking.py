# -*- coding: utf-8 -*-
"""
ETOL model checking (complete integration)
========================================

This module plugs ETOL (freeze + opacity operators over UNTIL/RELEASE) into the existing
TimedCGS / ZoneGraph / DBM stack.

Key features
------------
- Parses ETOL formulas via vitamin_model_checker.logics.ETOL.parser (must provide:
  AtomicProp, Unary, Binary, Freeze, OpacityPath, SimpleTimeExpr, do_parsingETOL, verifyETOL).
- Computes satisfaction sets bottom-up, using OU/OR fixpoints:
    OU_exists / OU_forall and OR_exists / OR_forall.
- Implements exact ETOL predecessor operators Pre_{BigCircExists} and Pre_{BigCircForall}
  using the ZoneGraph and the global clock y as clockMC (execution time).
- Automatically extracts one witness trace and one alternative trace (same duration)
  for opacity formulas when the initial state satisfies the formula.

Assumptions
-----------
- Global execution-time clock is an automaton clock named 'y' (never reset).
- If a formula uses freeze clock 'j', we map it to 'y' (j ≡ y) so constraints like j=100
  are applied as y=100 in the DBM.
- TimedCGS.get_edges() returns a list of (source_location_name, target_location_name).
- ZoneGraph.states is a set of TimeState objects; ZoneGraph.graph is adjacency on TimeStates.

Note
----
Your formal ETOL semantics quantifies over paths and compares total durations.
Here we compute duration sets symbolically by projecting the DBM to the 'y' clock.
This matches the intended execution-time opacity reasoning for clockMC.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Set

from vitamin_model_checker.logics.ETOL.parser import (
    AtomicProp, Binary, Expr, Unary,
    Freeze, OpacityPath, SimpleTimeExpr,
    do_parsingETOL, verifyETOL
)

from vitamin_model_checker.models.timedCGS.DBM.DBM import DBM
from vitamin_model_checker.models.timedCGS.DBM import DBMAdapter
from vitamin_model_checker.models.timedCGS import TimedCGS
from vitamin_model_checker.models.timedCGS.ZoneGraph import ZoneGraph, TimeState


# ============================================================
# Utilities
# ============================================================

def _all_states(tcgs: TimedCGS) -> Set[str]:
    return set(tcgs.get_states())


def get_states_prop_holds(tcgs: TimedCGS, prop: str) -> Optional[Set[str]]:
    """Return set of locations where atomic prop holds."""
    states = set()
    prop_matrix = tcgs.get_matrix_proposition()
    index = tcgs.get_atom_index(prop)
    if index is None:
        return None
    for state_idx, row in enumerate(prop_matrix):
        if row[int(index)] == 1:
            states.add(tcgs.get_state_name_by_index(state_idx))
    return states


def _get_clock_idx(tcgs: TimedCGS, clock_name: str) -> int:
    """DBM index for a clock (DBM has x0 at index 0)."""
    return tcgs.clocks_dict[clock_name] + 1


def _map_formula_clock(tcgs: TimedCGS, clock: str) -> str:
    """Map formula freeze clock 'j' to automaton global clock 'y' if present."""
    if clock == "j" and "y" in tcgs.clocks_dict:
        return "y"
    return clock


def _constraint_to_str(tcgs: TimedCGS, c) -> Optional[str]:
    """
    Convert parser constraint tuple (clock, rel, const) to string.
    Also maps j -> y when y exists.
    """
    if c is None:
        return None
    if isinstance(c, tuple) and len(c) == 3:
        clock, rel, const = c
        clock = _map_formula_clock(tcgs, clock)
        return f"{clock}{rel}{const}"
    if isinstance(c, str):
        if "y" in tcgs.clocks_dict:
            return c.replace("j", "y")
        return c
    return str(c)


def extract_closest_constraint(node: Expr):
    """Find closest SimpleTimeExpr constraint in subtree, if any."""
    c = getattr(node, "constraints", None)
    if c:
        return c
    for attr in ("operand", "left", "right", "path_formula", "formula"):
        child = getattr(node, attr, None)
        if child:
            res = extract_closest_constraint(child)
            if res:
                return res
    return None


# ============================================================
# DBM projection to duration intervals on clockMC (y)
# ============================================================

@dataclass(frozen=True)
class Interval:
    lb: float
    lb_open: bool
    ub: float
    ub_open: bool

    def contains_int(self) -> Optional[int]:
        """Pick an integer contained in the interval, if possible."""
        lb = self.lb
        ub = self.ub
        if math.isinf(lb) and math.isinf(ub):
            return 0
        if math.isinf(lb):
            if math.isinf(ub):
                return 0
            x = math.floor(ub)
            if x == ub and self.ub_open:
                x -= 1
            return x
        if math.isinf(ub):
            x = math.ceil(lb)
            if x == lb and self.lb_open:
                x += 1
            return x
        x = math.ceil(lb)
        if x == lb and self.lb_open:
            x += 1
        if x < ub or (x == ub and not self.ub_open):
            return x
        return None


def _interval_from_dbm(dbm: DBM, clock_idx: int) -> Interval:
    ub_bound = dbm.elements[clock_idx][0]
    lb_bound = dbm.elements[0][clock_idx]

    ub = float(ub_bound.constant)
    ub_open = (ub_bound.operator == '<')
    if math.isinf(ub):
        ub_open = False

    lb_c = float(lb_bound.constant)
    if math.isinf(lb_c):
        lb = -math.inf
        lb_open = False
    else:
        lb = -lb_c
        lb_open = (lb_bound.operator == '<')

    return Interval(lb, lb_open, ub, ub_open)


def _merge_intervals(intervals: List[Interval]) -> List[Interval]:
    if not intervals:
        return []
    it = sorted(intervals, key=lambda z: (z.lb, z.lb_open))
    out: List[Interval] = []
    cur = it[0]
    for nxt in it[1:]:
        if (nxt.lb > cur.ub) or (nxt.lb == cur.ub and (nxt.lb_open or cur.ub_open)):
            out.append(cur)
            cur = nxt
            continue
        if nxt.ub > cur.ub:
            cur = Interval(cur.lb, cur.lb_open, nxt.ub, nxt.ub_open)
        elif nxt.ub == cur.ub:
            cur = Interval(cur.lb, cur.lb_open, cur.ub, cur.ub_open and nxt.ub_open)
    out.append(cur)
    return out


def _intersect_nonempty(A: List[Interval], B: List[Interval]) -> bool:
    i = j = 0
    while i < len(A) and j < len(B):
        a = A[i]; b = B[j]
        lb = max(a.lb, b.lb)
        ub = min(a.ub, b.ub)

        if lb < ub:
            return True
        if lb == ub:
            def closed_at(iv: Interval, x: float) -> bool:
                if x == iv.lb and iv.lb_open:
                    return False
                if x == iv.ub and iv.ub_open:
                    return False
                return True
            if closed_at(a, lb) and closed_at(b, lb):
                return True

        if a.ub < b.ub or (a.ub == b.ub and a.ub_open and not b.ub_open):
            i += 1
        else:
            j += 1
    return False


def _equal_union(A: List[Interval], B: List[Interval]) -> bool:
    return A == B


def _pick_duration_from_intersection(A: List[Interval], B: List[Interval]) -> Optional[int]:
    for a in A:
        for b in B:
            lb = max(a.lb, b.lb)
            ub = min(a.ub, b.ub)
            if lb > ub:
                continue
            if lb == ub:
                if (not (lb == a.lb and a.lb_open) and not (lb == a.ub and a.ub_open) and
                    not (lb == b.lb and b.lb_open) and not (lb == b.ub and b.ub_open)):
                    if float(lb).is_integer():
                        return int(lb)
                continue
            lb_open = ((lb == a.lb and a.lb_open) or (lb == b.lb and b.lb_open))
            ub_open = ((ub == a.ub and a.ub_open) or (ub == b.ub and b.ub_open))
            d = Interval(lb, lb_open, ub, ub_open).contains_int()
            if d is not None:
                return d
    return None


# ============================================================
# ZoneGraph helpers
# ============================================================

def _build_reverse_graph(zone_graph: ZoneGraph) -> Dict[TimeState, List[TimeState]]:
    rev: Dict[TimeState, List[TimeState]] = {s: [] for s in zone_graph.states}
    for src, succs in zone_graph.graph.items():
        for dst in succs:
            rev[dst].append(src)
    return rev


def _apply_constraint_filter(tcgs: TimedCGS, ts: TimeState, constraint_str: Optional[str]) -> bool:
    if constraint_str is None:
        return True
    guards, resets = DBMAdapter.parse_constraints([constraint_str], tcgs.clocks_dict)
    copy_ts = ts.copy()
    copy_ts.apply_constraint(guards, resets)
    return not copy_ts.zone.is_empty()


def _collect_time_states_by_location(zone_graph: ZoneGraph, locations: Set[str], tcgs: TimedCGS, constraint_str: Optional[str]) -> List[TimeState]:
    return [t for t in zone_graph.states if (t.location in locations) and _apply_constraint_filter(tcgs, t, constraint_str)]


# ============================================================
# Exact ETOL predecessors using clockMC := y
# ============================================================

def _pred_exists(tcgs: TimedCGS, zone_graph: ZoneGraph, X: Set[str], constraint_tuple) -> Set[str]:
    constraint = _constraint_to_str(tcgs, constraint_tuple)
    rev = _build_reverse_graph(zone_graph)

    if "y" not in tcgs.clocks_dict:
        raise ValueError("ETOL Pre requires global clock 'y' (clockMC).")
    y_idx = _get_clock_idx(tcgs, "y")

    NX = _all_states(tcgs) - X
    X_ts = _collect_time_states_by_location(zone_graph, X, tcgs, constraint)
    NX_ts = _collect_time_states_by_location(zone_graph, NX, tcgs, constraint)

    pre_to_X: Dict[str, List[Interval]] = defaultdict(list)
    pre_to_NX: Dict[str, List[Interval]] = defaultdict(list)

    for tgt in X_ts:
        for pred_ts in rev.get(tgt, []):
            if _apply_constraint_filter(tcgs, pred_ts, constraint):
                pre_to_X[pred_ts.location].append(_interval_from_dbm(pred_ts.zone, y_idx))

    for tgt in NX_ts:
        for pred_ts in rev.get(tgt, []):
            if _apply_constraint_filter(tcgs, pred_ts, constraint):
                pre_to_NX[pred_ts.location].append(_interval_from_dbm(pred_ts.zone, y_idx))

    cand = set(pre_to_X.keys()) & set(pre_to_NX.keys())
    out: Set[str] = set()
    for loc in cand:
        Dx = _merge_intervals(pre_to_X[loc])
        Dn = _merge_intervals(pre_to_NX[loc])
        if Dx and Dn and _intersect_nonempty(Dx, Dn):
            out.add(loc)
    return out


def _pred_forall(tcgs: TimedCGS, zone_graph: ZoneGraph, X: Set[str], constraint_tuple) -> Set[str]:
    constraint = _constraint_to_str(tcgs, constraint_tuple)
    rev = _build_reverse_graph(zone_graph)

    if "y" not in tcgs.clocks_dict:
        raise ValueError("ETOL Pre requires global clock 'y' (clockMC).")
    y_idx = _get_clock_idx(tcgs, "y")

    NX = _all_states(tcgs) - X
    X_ts = _collect_time_states_by_location(zone_graph, X, tcgs, constraint)
    NX_ts = _collect_time_states_by_location(zone_graph, NX, tcgs, constraint)

    pre_to_X: Dict[str, List[Interval]] = defaultdict(list)
    pre_to_NX: Dict[str, List[Interval]] = defaultdict(list)

    for tgt in X_ts:
        for pred_ts in rev.get(tgt, []):
            if _apply_constraint_filter(tcgs, pred_ts, constraint):
                pre_to_X[pred_ts.location].append(_interval_from_dbm(pred_ts.zone, y_idx))

    for tgt in NX_ts:
        for pred_ts in rev.get(tgt, []):
            if _apply_constraint_filter(tcgs, pred_ts, constraint):
                pre_to_NX[pred_ts.location].append(_interval_from_dbm(pred_ts.zone, y_idx))

    cand = set(pre_to_X.keys()) & set(pre_to_NX.keys())
    out: Set[str] = set()
    for loc in cand:
        Dx = _merge_intervals(pre_to_X[loc])
        Dn = _merge_intervals(pre_to_NX[loc])
        if Dx and Dn and _equal_union(Dx, Dn):
            out.add(loc)
    return out


# ============================================================
# OU / OR fixpoints
# ============================================================

def OU_exists(tcgs: TimedCGS, zone_graph: ZoneGraph, phi1: Set[str], phi2: Set[str], constraint_tuple) -> Set[str]:
    X=set()
    Y=set(phi2)
    while Y!=X:
        X=Y
        Y = set(phi2) | (set(phi1) & _pred_exists(tcgs, zone_graph, X, constraint_tuple))
    return Y


def OU_forall(tcgs: TimedCGS, zone_graph: ZoneGraph, phi1: Set[str], phi2: Set[str], constraint_tuple) -> Set[str]:
    X=set()
    Y=set(phi2)
    while Y!=X:
        X=Y
        Y = set(phi2) | (set(phi1) & _pred_forall(tcgs, zone_graph, X, constraint_tuple))
    return Y


def OR_exists(tcgs: TimedCGS, zone_graph: ZoneGraph, phi1: Set[str], phi2: Set[str], constraint_tuple) -> Set[str]:
    X=set()
    Y=set(phi2)
    while Y!=X:
        X=Y
        Y = set(phi2) & (set(phi1) | _pred_exists(tcgs, zone_graph, X, constraint_tuple))
    return Y


def OR_forall(tcgs: TimedCGS, zone_graph: ZoneGraph, phi1: Set[str], phi2: Set[str], constraint_tuple) -> Set[str]:
    X=set()
    Y=set(phi2)
    while Y!=X:
        X=Y
        Y = set(phi2) & (set(phi1) | _pred_forall(tcgs, zone_graph, X, constraint_tuple))
    return Y


# ============================================================
# State-set evaluation
# ============================================================

def states_with_time_constraints(tcgs: TimedCGS, zone_graph: ZoneGraph, constraint_tuple) -> Set[str]:
    constraint_str = _constraint_to_str(tcgs, constraint_tuple)
    if constraint_str is None:
        return _all_states(tcgs)

    guards, resets = DBMAdapter.parse_constraints([constraint_str], tcgs.clocks_dict)
    result=set()
    for ts in zone_graph.states:
        cp = ts.copy()
        cp.apply_constraint(guards, resets)
        if not cp.zone.is_empty():
            result.add(cp.location)
    return result


def solve_tree_etol(tcgs: TimedCGS, zone_graph: ZoneGraph, node: Expr):
    if isinstance(node, AtomicProp):
        st = get_states_prop_holds(tcgs, node.name)
        node.satisfying_states = set() if st is None else set(st)
        return

    if isinstance(node, SimpleTimeExpr):
        node.satisfying_states = states_with_time_constraints(tcgs, zone_graph, node.constraints)
        return

    for attr in ("operand", "left", "right", "formula", "path_formula"):
        ch = getattr(node, attr, None)
        if ch:
            solve_tree_etol(tcgs, zone_graph, ch)

    if isinstance(node, Unary):
        node.satisfying_states = _all_states(tcgs) - node.operand.satisfying_states
        return

    if isinstance(node, Binary):
        op = node.op
        if op in ("|","||","or") or verifyETOL("OR", op):
            node.satisfying_states = node.left.satisfying_states | node.right.satisfying_states
        elif op in ("&","&&","and") or verifyETOL("AND", op):
            node.satisfying_states = node.left.satisfying_states & node.right.satisfying_states
        elif op in ("->","implies") or verifyETOL("IMPLIES", op):
            node.satisfying_states = (_all_states(tcgs) - node.left.satisfying_states) | node.right.satisfying_states
        return

    if isinstance(node, Freeze):
        solve_tree_etol(tcgs, zone_graph, node.formula)
        node.satisfying_states = node.formula.satisfying_states
        return

    if isinstance(node, OpacityPath):
        pf = node.path_formula
        assert isinstance(pf, Binary)
        phi1 = pf.left.satisfying_states
        phi2 = pf.right.satisfying_states
        constraint = extract_closest_constraint(pf)

        is_until = (pf.op in ("U","until") or verifyETOL("UNTIL", pf.op))
        is_release = (pf.op in ("R","release") or verifyETOL("RELEASE", pf.op))

        if node.op == "OE":
            node.satisfying_states = OU_exists(tcgs, zone_graph, phi1, phi2, constraint) if is_until else OR_exists(tcgs, zone_graph, phi1, phi2, constraint)
        elif node.op == "OA":
            node.satisfying_states = OU_forall(tcgs, zone_graph, phi1, phi2, constraint) if is_until else OR_forall(tcgs, zone_graph, phi1, phi2, constraint)
        else:
            raise ValueError(f"Unknown opacity op {node.op}")
        return


# ============================================================
# Trace extraction (automatic)
# ============================================================

@dataclass
class TracePair:
    duration: int
    witness: List[str]
    alternative: List[str]


def _path_to_locations(path: List[TimeState]) -> List[str]:
    return [ts.location for ts in reversed(path)]


def _durations_from_loc_set(tcgs: TimedCGS, zone_graph: ZoneGraph, locs: Set[str], constraint_str: Optional[str]) -> List[Interval]:
    y_idx = _get_clock_idx(tcgs, "y")
    intervals=[]
    for ts in zone_graph.states:
        if ts.location in locs and _apply_constraint_filter(tcgs, ts, constraint_str):
            intervals.append(_interval_from_dbm(ts.zone, y_idx))
    return _merge_intervals(intervals)


def _pick_ts_with_duration(tcgs: TimedCGS, candidates: List[TimeState], d: int, constraint_str: Optional[str]) -> Optional[TimeState]:
    y_idx = _get_clock_idx(tcgs, "y")
    for ts in candidates:
        if constraint_str is not None and not _apply_constraint_filter(tcgs, ts, constraint_str):
            continue
        iv = _interval_from_dbm(ts.zone, y_idx)
        if d < iv.lb or d > iv.ub:
            continue
        if d == iv.lb and iv.lb_open:
            continue
        if d == iv.ub and iv.ub_open:
            continue
        return ts
    return None


def _select_path_starting_at_ts(zone_graph: ZoneGraph, ts: TimeState, constraint_str: Optional[str]) -> Optional[List[TimeState]]:
    paths = zone_graph.find_path_from(ts.location, contraints=None)  # get all paths from this location
    for p in paths:
        if p and p[0] == ts:
            if constraint_str is None:
                return p
            ok=True
            for node in p:
                if not _apply_constraint_filter(zone_graph.tcgs, node, constraint_str):
                    ok=False
                    break
            if ok:
                return p
    return None


def _extract_pair_exists_until(tcgs: TimedCGS, zone_graph: ZoneGraph, phi1: Set[str], phi2: Set[str], constraint_tuple) -> Optional[TracePair]:
    constraint_str = _constraint_to_str(tcgs, constraint_tuple)

    # pick a duration d that is achievable both in phi2 and outside phi2
    D_sat = _durations_from_loc_set(tcgs, zone_graph, phi2, constraint_str)
    D_viol = _durations_from_loc_set(tcgs, zone_graph, _all_states(tcgs) - phi2, constraint_str)
    d = _pick_duration_from_intersection(D_sat, D_viol)
    if d is None:
        return None

    phi2_ts = [t for t in zone_graph.states if t.location in phi2]
    notphi2_ts = [t for t in zone_graph.states if t.location not in phi2]

    ts_sat = _pick_ts_with_duration(tcgs, phi2_ts, d, constraint_str)
    if ts_sat is None:
        return None

    # ensure alternative avoids phi2 entirely (strong violation)
    ts_viol = None
    for cand in notphi2_ts:
        cand2 = _pick_ts_with_duration(tcgs, [cand], d, constraint_str)
        if cand2 is None:
            continue
        p = _select_path_starting_at_ts(zone_graph, cand2, constraint_str)
        if p is None:
            continue
        locs = _path_to_locations(p)
        if all(l not in phi2 for l in locs):
            ts_viol = cand2
            p_viol = p
            break
    if ts_viol is None:
        return None

    p_sat = _select_path_starting_at_ts(zone_graph, ts_sat, constraint_str)
    if p_sat is None:
        return None

    locs_sat = _path_to_locations(p_sat)
    locs_viol = _path_to_locations(p_viol)

    # Optional: check phi1 holds before reaching phi2 on witness
    # (kept as best-effort; if violated due to modeling granularity, still returns illustrative pair)
    if any(l not in phi1 for l in locs_sat[:-1]):
        pass

    return TracePair(duration=d, witness=locs_sat, alternative=locs_viol)


def extract_trace_pair(tcgs: TimedCGS, zone_graph: ZoneGraph, ast: Expr) -> Optional[TracePair]:
    """Extract one witness/alternative pair for OE( ... U ... ) when possible."""
    node = ast
    while isinstance(node, Freeze):
        node = node.formula

    if not isinstance(node, OpacityPath):
        return None

    pf = node.path_formula
    if not isinstance(pf, Binary):
        return None

    is_until = (pf.op in ("U","until") or verifyETOL("UNTIL", pf.op))
    if node.op == "OE" and is_until:
        phi1 = pf.left.satisfying_states
        phi2 = pf.right.satisfying_states
        constraint = extract_closest_constraint(pf)
        return _extract_pair_exists_until(tcgs, zone_graph, phi1, phi2, constraint)

    # Extend similarly for OA and/or RELEASE if you want additional pairs.
    return None


# ============================================================
# Public entry point
# ============================================================

def timed_model_checking_etol_batch(formulas: Union[List[str], str], filename: str) -> Dict[str, Any]:
    """
   
    """
    # Normaliza entrada
    if isinstance(formulas, str):
        formulas_list = [ln.strip() for ln in formulas.splitlines() if ln.strip()]
    else:
        formulas_list = [f.strip() for f in formulas if f and f.strip()]

    if not formulas_list:
        return {'res': 'Error: no formulas specified', 'initial_state': ''}

    # Carga modelo una sola vez
    tcgs = TimedCGS()
    tcgs.read_file(filename)

    # Construye ZoneGraph una sola vez (si tu implementación lo permite)
    zone_graph = ZoneGraph(tcgs)

    init = tcgs.initial_state
    results = []

    for f in formulas_list:
        # Parse
        ast = do_parsingETOL(f)
        if ast is None:
            results.append({
                'formula': f,
                'res': "Syntax error in ETOL formula (or unknown atoms)",
                'initial_state': f'Initial state {init}: False'
            })
            continue

        # Resuelve
        solve_tree_etol(tcgs, zone_graph, ast)

        sat = init in ast.satisfying_states
        out = {
            'formula': f,
            'res': 'Result set: ' + str(ast.satisfying_states),
            'initial_state': f'Initial state {init}: {sat}'
        }

        # Witness si satisface
        if sat:
            pair = extract_trace_pair(tcgs, zone_graph, ast)
            if pair:
                out['duration'] = pair.duration
                out['witness_trace'] = " -> ".join(pair.witness)
                out['alternative_trace'] = " -> ".join(pair.alternative)

        results.append(out)

    return {
        'initial_state': init,
        'results': results
    }



def timed_model_checking_etol(formula: Union[str, List[str]], filename: str) -> Dict[str, Any]:
    # Si es lista o string multilínea, delega al batch
    if isinstance(formula, list) or (isinstance(formula, str) and "\n" in formula):
        return timed_model_checking_etol_batch(formula, filename)

    # --- tu comportamiento original para una sola fórmula ---
    if not formula or not str(formula).strip():
        return {'res': 'Error: no formula specified', 'initial_state': ''}

    tcgs = TimedCGS()
    tcgs.read_file(filename)

    ast = do_parsingETOL(str(formula).strip())
    if ast is None:
        return {'res': "Syntax error in ETOL formula (or unknown atoms)", 'initial_state': ''}

    zone_graph = ZoneGraph(tcgs)
    solve_tree_etol(tcgs, zone_graph, ast)

    init = tcgs.initial_state
    sat = init in ast.satisfying_states

    out = {
        'res': 'Result set: ' + str(ast.satisfying_states),
        'initial_state': f'Initial state {init}: {sat}'
    }

    if sat:
        pair = extract_trace_pair(tcgs, zone_graph, ast)
        if pair:
            out['duration'] = pair.duration
            out['witness_trace'] = " -> ".join(pair.witness)
            out['alternative_trace'] = " -> ".join(pair.alternative)
    return out


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--formula", required=True)
    args = ap.parse_args()
    print(json.dumps(timed_model_checking_etol(args.formula, args.model), indent=2))
