# Input Format Description

This document explains the input formats supported by the ETOL artifact.

The artifact uses two main kinds of input files:

- **model files**, which describe timed automata;
- **formula files**, which describe ETOL properties to be checked on those models.

The purpose of this document is to help users:

- understand the structure of the packaged ATM example;
- run the provided experiments correctly;
- create new models and formulas if needed;
- understand clearly how the model is constructed;
- understand clearly how the formula is constructed;
- understand how the verifier combines the model and the formula during model checking.

# 1. General Overview

A verification task in the ETOL artifact is based on two inputs:

1. a **timed automaton model**, stored in a model file;
2. an **ETOL formula**, stored in a formula file or provided directly through the command line.

The model file defines the timed system to be verified.

The formula file defines the logical property that must be checked on this timed system.

In other words, the verification problem has the following structure:

model + formula = verification problem

The verifier reads the model, constructs an internal timed automaton, reads the formula, builds its abstract syntax tree, and then checks whether the formula is satisfied by the initial state of the model.

The general workflow is:

model file  ---> parser ---> timed automaton  
formula     ---> parser ---> ETOL formula  

timed automaton + ETOL formula  
            |  
            v  
model checking algorithm  
            |  
            v  
SAT or UNSAT

The result is usually either:

SAT

or:

UNSAT

where:

- `SAT` means that the initial state of the model satisfies the formula;
- `UNSAT` means that the initial state of the model does not satisfy the formula.

# 2. Model Files

A model file describes a timed automaton.

It is written as a sequence of named sections. Each section describes one part of the model.

A typical model file contains the following sections:

Transition  
Name_State  
Initial_State  
Atomic_propositions  
Labelling  
Number_of_agents  
Clocks  
Clock_constraints  
Invariants

The ATM example included in the artifact follows this format.

The model is constructed progressively from these sections.

Each section has a specific role:

- `Name_State` declares the set of states;
- `Initial_State` declares the initial state;
- `Transition` declares the edges between states;
- `Atomic_propositions` declares the logical propositions used in formulas;
- `Labelling` assigns propositions to states;
- `Number_of_agents` declares the number of agents used by the model;
- `Clocks` declares the clocks of the timed automaton;
- `Clock_constraints` assigns timing guards and resets to transitions;
- `Invariants` assigns timing restrictions to states.

# 3. Construction of the Model

The model is built step by step from the input file.

A timed automaton is composed of:

1. a finite set of states;
2. one initial state;
3. a finite set of transitions;
4. a finite set of atomic propositions;
5. a labeling function;
6. a finite set of clocks;
7. clock constraints on transitions;
8. invariants on states.

Formally, the model can be viewed as a structure:

A = (S, s0, AP, L, X, R, G, Inv)

where:

- `S` is the finite set of states;
- `s0` is the initial state;
- `AP` is the set of atomic propositions;
- `L` is the labeling function;
- `X` is the set of clocks;
- `R` is the transition relation;
- `G` assigns clock guards and resets to transitions;
- `Inv` assigns invariants to states.

Each section of the input file contributes to one component of this structure.

# 4. Name_State

The section `Name_State` lists all states, also called locations, of the automaton.

## Syntax

Name_State  
s0 s1 s2 ... sn

## ATM Example

Name_State  
I W WP WC WA PNW PQW DB MAN MAQ OO T C E

This declares the following states:

I  
W  
WP  
WC  
WA  
PNW  
PQW  
DB  
MAN  
MAQ  
OO  
T  
C  
E

Each name represents one possible state of the ATM system.

For the ATM benchmark, the intended interpretation is:

- `I` means initial state;
- `W` means welcome or waiting state;
- `WP` means waiting for password;
- `WC` means waiting for choice;
- `WA` means waiting for amount;
- `PNW` means preparing normal withdrawal;
- `PQW` means preparing quick withdrawal;
- `DB` means displaying balance;
- `MAN` means money available for normal withdrawal;
- `MAQ` means money available for quick withdrawal;
- `OO` means other operation;
- `T` means terminating;
- `C` means cancelling;
- `E` means end.

The important rule is:

Every state used in transitions, labels, constraints, or invariants must be declared in `Name_State`.

If a state appears later in the file but is not declared in `Name_State`, the parser should report an error.

# 5. Initial_State

The section `Initial_State` defines where the execution of the model starts.

## Syntax

Initial_State  
state_name

## Example

Initial_State  
I

This means that the first state of the model is `I`.

The initial state must belong to the set declared in `Name_State`.

For example, if the model declares:

Name_State  
I W WP DB T C E

then the following initial state is valid:

Initial_State  
I

However, the following one is invalid:

Initial_State  
Unknown

because `Unknown` is not declared in `Name_State`.

The verifier starts the model checking procedure from the symbolic initial state:

(initial location, initial clock zone)

For example:

(I, x = 0 and y = 0)

if the model starts with all clocks equal to zero.

# 6. Transition

The section `Transition` defines the transition relation of the automaton.

A transition describes how the system can move from one state to another.

In the ATM artifact, transitions are represented by a matrix.

The matrix is constructed from the graph of the input model. In other words, every arrow that appears in the ATM graph must appear as a non-zero entry in the transition matrix.

The transition matrix is therefore a compact representation of the edges of the graph.

## 6.1 Matrix Interpretation

The order of the rows and columns is the same as the order of the states declared in `Name_State`.

For the ATM model:

Name_State  
I W WP WC WA PNW PQW DB MAN MAQ OO T C E

the index order is:

0  -> I  
1  -> W  
2  -> WP  
3  -> WC  
4  -> WA  
5  -> PNW  
6  -> PQW  
7  -> DB  
8  -> MAN  
9  -> MAQ  
10 -> OO  
11 -> T  
12 -> C  
13 -> E

The meaning of the matrix is:

row = source state  
column = target state  
0 = no transition  
non-zero value = transition exists

For example, the first row:

0 1 0 0 0 0 0 0 0 0 0 0 0 0

means that there is a transition from `I` to `W`.

This is because row 0 corresponds to `I`, and column 1 corresponds to `W`.

Therefore:

Transition[0][1] = 1

means:

I -> W

## 6.2 Important Rule

The transition matrix must match the graph of the model.

If the graph contains an arrow:

OO -> WC

then the transition matrix must contain a non-zero value at the row corresponding to `OO` and the column corresponding to `WC`.

Using the ATM state order:

OO = row 10  
WC = column 3

so the row of `OO` must contain a non-zero value in column 3.

Therefore, the correct row for `OO` should contain a non-zero value at column 3.

For example:

0 0 0 1 0 0 0 0 0 0 0 1 0 0

This means:

OO -> WC  
OO -> T

If instead the row is:

0 1 0 0 0 0 0 0 0 0 0 1 0 0

then it means:

OO -> W  
OO -> T

This is not the same graph.

Therefore, a transition matrix is correct only if every non-zero entry corresponds exactly to an arrow in the model graph.

## 6.3 Binary or Numbered Transition Matrices

Some parsers use a binary transition matrix:

0 = no transition  
1 = transition exists

Other parsers use a numbered transition matrix:

0 = no transition  
1, 2, 3, ... = transition/action identifiers

In the ATM artifact, the working example may use numbers greater than 1. These numbers may identify actions or internal transition labels.

Therefore, one must not change the numbers arbitrarily unless the parser is known to accept a binary matrix.

If the parser expects only the existence of transitions, then every non-zero number may be replaced by 1.

If the parser expects action identifiers, then the original numbers must be preserved.

## 6.4 Correct ATM Transition Matrix in Binary Form

Using the state order:

I W WP WC WA PNW PQW DB MAN MAQ OO T C E

and following the ATM graph, the binary transition matrix is:

Transition  
0 1 0 0 0 0 0 0 0 0 0 0 0 0  
0 0 1 0 0 0 0 0 0 0 0 0 0 0  
0 0 1 1 0 0 0 0 0 0 0 0 1 0  
0 0 0 0 1 0 1 1 0 0 0 0 0 0  
0 0 0 0 1 1 0 0 0 0 0 0 1 0  
0 0 0 0 0 0 0 0 1 0 0 0 0 0  
0 0 0 0 0 0 0 0 0 1 0 0 0 0  
0 0 0 0 0 0 0 0 0 0 1 0 0 1  
0 0 0 0 0 0 0 0 0 0 1 0 1 0  
0 0 0 0 0 0 0 0 0 0 0 0 1 1  
0 0 0 1 0 0 0 0 0 0 0 1 0 0  
0 0 0 0 0 0 0 0 0 0 0 0 0 1  
0 0 0 0 0 0 0 0 0 0 0 0 0 1  
0 0 0 0 0 0 0 0 0 0 0 0 0 0

This matrix represents the following transitions:

I   -> W  
W   -> WP  
WP  -> WP  
WP  -> WC  
WP  -> C  
WC  -> WA  
WC  -> PQW  
WC  -> DB  
WA  -> WA  
WA  -> PNW  
WA  -> C  
PNW -> MAN  
PQW -> MAQ  
DB  -> OO  
DB  -> E  
MAN -> OO  
MAN -> C  
MAQ -> C  
MAQ -> E  
OO  -> WC  
OO  -> T  
T   -> E  
C   -> E

# 7. Atomic_propositions

The section `Atomic_propositions` declares the logical propositions used to describe states.

Atomic propositions are the basic logical facts that may be true or false in a state.

## Syntax

Atomic_propositions  
p1 p2 p3 ... pk

## Example

Atomic_propositions  
cash balance correctPwd

This declares the following propositions:

cash  
balance  
correctPwd

Atomic propositions are used inside ETOL formulas.

For example:

F(cash)

means:

Eventually, the system reaches a state where `cash` is true.

Another example is:

G(!balance)

which means:

The system never reaches a state labeled with `balance`.

Atomic propositions do not define transitions. They only describe properties of states.

# 8. Labelling

The section `Labelling` assigns atomic propositions to states.

This tells the verifier which propositions are true in which states.

In the ATM artifact, the labeling may be represented as a matrix.

The order of the rows follows `Name_State`.

The order of the columns follows `Atomic_propositions`.

For example:

Atomic_propositions  
cash balance correctPwd

The columns are:

0 -> cash  
1 -> balance  
2 -> correctPwd

A row such as:

0 1 0

means that the corresponding state satisfies `balance`.

A row such as:

1 0 0

means that the corresponding state satisfies `cash`.

A row such as:

0 0 1

means that the corresponding state satisfies `correctPwd`.

## ATM Example

Atomic_propositions  
cash balance correctPwd

Labelling  
0 0 0  
0 0 0  
0 0 0  
0 0 1  
0 0 0  
0 0 0  
0 0 0  
0 1 0  
1 0 0  
1 0 0  
0 0 0  
0 0 0  
0 0 0  
0 0 0

With the state order:

I W WP WC WA PNW PQW DB MAN MAQ OO T C E

this means:

WC satisfies `correctPwd`  
DB satisfies `balance`  
MAN satisfies `cash`  
MAQ satisfies `cash`

Formally, this section defines a labeling function:

L : S -> 2^AP

where:

- `S` is the set of states;
- `AP` is the set of atomic propositions;
- `L(s)` is the set of propositions true in state `s`.

# 9. Number_of_agents

The section `Number_of_agents` gives the number of agents involved in the model.

## Syntax

Number_of_agents  
n

## Example

Number_of_agents  
1

This means that the system contains one agent.

In an ATM model, agents may represent, for example:

- the user;
- the ATM machine;
- the bank server;
- an external observer;
- an attacker or intruder.

The precise interpretation depends on the model.

In ETOL, the notion of agent is useful because opacity often depends on what an observer can see, infer, or distinguish.

# 10. Clocks

The section `Clocks` declares the clocks used by the timed automaton.

A clock is a real-valued variable that evolves with time.

All clocks increase at the same rate as time passes, unless they are reset by a transition.

## Syntax

Clocks  
x y z

## Example

Clocks  
x y

This declares two clocks:

x  
y

Initially, clocks are usually equal to zero:

x = 0  
y = 0

After 3 time units, if no reset occurs:

x = 3  
y = 3

If a transition resets `x`, then:

x = 0

while the other clocks continue according to their own values.

Clocks are used in:

- transition guards;
- state invariants;
- timed formulas;
- symbolic zones;
- DBM-based reachability analysis.

# 11. Clock_constraints

The section `Clock_constraints` defines timing conditions attached to transitions.

A clock constraint is a guard. It tells when a transition may be taken.

In the ATM artifact, this section may also be represented as a matrix.

The position of each constraint must match the position of the corresponding transition in the `Transition` matrix.

For example, if the transition matrix contains a non-zero value at row `i` and column `j`, then the clock constraint at row `i` and column `j` is the guard or reset attached to that transition.

If there is no transition at row `i` and column `j`, the corresponding clock constraint should normally be `0`.

## Example

If:

Transition[I][W] = 1

and:

Clock_constraints[I][W] = x:=0,y:=0

then the transition from `I` to `W` resets both clocks `x` and `y`.

If:

Transition[W][WP] = 1

and:

Clock_constraints[W][WP] = x=3,x:=0

then the transition from `W` to `WP` can be taken when `x = 3`, and then `x` is reset to `0`.

## Important Rule

The transition matrix and the clock-constraint matrix must be aligned.

If a transition exists in `Transition`, the corresponding timing constraint must be placed in the same row and same column in `Clock_constraints`.

For example:

Transition row of `OO`:

0 0 0 1 0 0 0 0 0 0 0 1 0 0

means:

OO -> WC  
OO -> T

Therefore, the clock constraints for these two transitions must be placed in the row of `OO`, column `WC`, and column `T`.

# 12. Invariants

The section `Invariants` defines timing restrictions on states.

An invariant describes how long the system is allowed to remain in a state.

In the ATM model, each row corresponds to one state, in the same order as `Name_State`.

Since the clocks are:

Clocks  
x y

each invariant row contains two entries: one for `x` and one for `y`.

For example:

x<=3 0

means that the corresponding state has the invariant:

x <= 3

and no invariant on `y`.

The value:

0

means that there is no invariant for that clock.

## ATM Example

Invariants  
0 0  
x<=3 0  
x<=10 0  
x<=10 0  
x<=10 0  
x<=15 0  
x<=15 0  
x<=10 0  
x<=20 0  
x<=20 0  
x<=10 0  
0 y<=100  
0 y<=100  
0 0

With the state order:

I W WP WC WA PNW PQW DB MAN MAQ OO T C E

this means:

I   : true  
W   : x <= 3  
WP  : x <= 10  
WC  : x <= 10  
WA  : x <= 10  
PNW : x <= 15  
PQW : x <= 15  
DB  : x <= 10  
MAN : x <= 20  
MAQ : x <= 20  
OO  : x <= 10  
T   : y <= 100  
C   : y <= 100  
E   : true

Invariants are important because they restrict time elapse.

For example, if a state has the invariant:

x <= 5

then the automaton cannot stay in that state once `x` becomes greater than `5`.

# 13. How the Model Is Built Internally

After reading the model file, the verifier builds an internal timed automaton.

This construction is done in several stages.

## Stage 1: Reading States

The verifier reads the section:

Name_State

and creates the finite set of states.

For the ATM example:

Name_State  
I W WP WC WA PNW PQW DB MAN MAQ OO T C E

it creates:

S = {I, W, WP, WC, WA, PNW, PQW, DB, MAN, MAQ, OO, T, C, E}

## Stage 2: Reading the Initial State

The verifier reads:

Initial_State  
I

and stores:

s0 = I

This means that model checking starts from state `I`.

## Stage 3: Reading Transitions

The verifier reads:

Transition

and constructs the transition relation:

R ⊆ S × S

For a matrix representation, every non-zero entry creates one transition.

For example:

Transition[0][1] = 1

creates:

I -> W

The transition relation is therefore obtained directly from the graph encoded by the matrix.

## Stage 4: Reading Atomic Propositions

The verifier reads:

Atomic_propositions

and creates the set:

AP = {p1, p2, ..., pk}

For example:

Atomic_propositions  
cash balance correctPwd

creates:

AP = {cash, balance, correctPwd}

## Stage 5: Reading Labels

The verifier reads:

Labelling

and builds the labeling function:

L : S -> 2^AP

For example:

DB satisfies `balance`  
MAN satisfies `cash`  
MAQ satisfies `cash`  
WC satisfies `correctPwd`

This labeling function is used when evaluating atomic propositions in formulas.

## Stage 6: Reading Agents

The verifier reads:

Number_of_agents

and stores the number of agents.

For example:

Number_of_agents  
1

means:

There is 1 agent in the model.

## Stage 7: Reading Clocks

The verifier reads:

Clocks

and creates the set of clocks.

For example:

Clocks  
x y

creates:

X = {x, y}

The initial clock valuation is usually:

x = 0 and y = 0

## Stage 8: Reading Clock Constraints

The verifier reads:

Clock_constraints

and attaches timing guards and resets to transitions.

For example:

Clock_constraints[I][W] = x:=0,y:=0

means that the transition:

I -> W

resets clocks `x` and `y`.

## Stage 9: Reading Invariants

The verifier reads:

Invariants

and attaches timing restrictions to states.

For example:

Inv(WP) = x <= 10

means that the automaton cannot remain in state `WP` when `x > 10`.

## Stage 10: Building Symbolic States

The verifier does not enumerate all possible real-valued clock valuations.

Instead, it constructs symbolic states.

A symbolic state has the form:

(location, zone)

where:

- `location` is a discrete state;
- `zone` is a symbolic set of clock valuations.

For example:

(DB, x <= 10)

means that the system is in state `DB`, and the possible clock valuations satisfy:

x <= 10

Zones are usually represented using DBMs, that is, Difference Bound Matrices.

# 14. Complete ATM Model Example

The following model follows the ATM graph and uses the matrix format.

Transition  
0 1 0 0 0 0 0 0 0 0 0 0 0 0  
0 0 1 0 0 0 0 0 0 0 0 0 0 0  
0 0 1 1 0 0 0 0 0 0 0 0 1 0  
0 0 0 0 1 0 1 1 0 0 0 0 0 0  
0 0 0 0 1 1 0 0 0 0 0 0 1 0  
0 0 0 0 0 0 0 0 1 0 0 0 0 0  
0 0 0 0 0 0 0 0 0 1 0 0 0 0  
0 0 0 0 0 0 0 0 0 0 1 0 0 1  
0 0 0 0 0 0 0 0 0 0 1 0 1 0  
0 0 0 0 0 0 0 0 0 0 0 0 1 1  
0 0 0 1 0 0 0 0 0 0 0 1 0 0  
0 0 0 0 0 0 0 0 0 0 0 0 0 1  
0 0 0 0 0 0 0 0 0 0 0 0 0 1  
0 0 0 0 0 0 0 0 0 0 0 0 0 0

Name_State  
I W WP WC WA PNW PQW DB MAN MAQ OO T C E

Initial_State  
I

Atomic_propositions  
cash balance correctPwd

Labelling  
0 0 0  
0 0 0  
0 0 0  
0 0 1  
0 0 0  
0 0 0  
0 0 0  
0 1 0  
1 0 0  
1 0 0  
0 0 0  
0 0 0  
0 0 0  
0 0 0

Number_of_agents  
1

Clocks  
x y

Clock_constraints  
0 x:=0,y:=0 0 0 0 0 0 0 0 0 0 0 0 0  
0 0 x=3,x:=0 0 0 0 0 0 0 0 0 0 0 0  
0 0 0 x:=0 0 0 0 0 0 0 0 0 x=10 0  
0 0 0 0 x:=0 0 x:=0 x:=0 0 0 0 0 0 0  
0 0 0 0 0 x:=0 0 0 0 0 0 0 x=12 0  
0 0 0 0 0 0 0 0 x=15,x:=0 0 0 0 0 0  
0 0 0 0 0 0 0 0 0 x=15,x:=0 0 0 0 0  
0 0 0 0 0 0 0 0 0 0 x=10,x:=0 0 0 0  
0 0 0 0 0 0 0 0 0 0 x:=0 0 x=20 0  
0 0 0 0 0 0 0 0 0 0 0 0 x=20 0  
0 0 0 0 0 0 0 0 0 0 0 x=10 0 0  
0 0 0 0 0 0 0 0 0 0 0 0 0 y=100  
0 0 0 0 0 0 0 0 0 0 0 0 0 y=100  
0 0 0 0 0 0 0 0 0 0 0 0 0 0

Invariants  
0 0  
x<=3 0  
x<=10 0  
x<=10 0  
x<=10 0  
x<=15 0  
x<=15 0  
x<=10 0  
x<=20 0  
x<=20 0  
x<=10 0  
0 y<=100  
0 y<=100  
0 0

This model describes the ATM benchmark.

The system starts in state `I`.

It then follows the transition graph encoded by the transition matrix.

State labels are used to evaluate logical formulas.

Clock constraints and invariants are used to evaluate timed behavior.

# 15. Formula Files

A formula file contains one ETOL formula.

The formula describes the property that should be checked on the model.

A formula may use:

- atomic propositions;
- Boolean operators;
- temporal operators;
- opacity operators;
- timing constraints;
- freeze variables.

A typical formula file may contain:

F(cash)

or:

OA(G(!balance))

or:

j.(OE(F(balance & j <= 3)))

Each formula is evaluated from the initial symbolic state of the model.

# 16. Construction of an ETOL Formula

An ETOL formula is built recursively.

This means that simple formulas can be combined to construct more complex formulas.

The grammar is based on the following forms:

T  
p  
!phi  
phi & psi  
phi | psi  
F(phi)  
G(phi)  
phi U psi  
phi R psi  
OE(phi)  
OA(phi)  
j.(phi)

where:

- `T` means true;
- `p` is an atomic proposition;
- `phi` and `psi` are formulas;
- `!phi` means not phi;
- `phi & psi` means phi and psi;
- `phi | psi` means phi or psi;
- `F(phi)` means eventually phi;
- `G(phi)` means globally phi;
- `phi U psi` means phi until psi;
- `phi R psi` means phi release psi;
- `OE(phi)` means existential opacity over phi;
- `OA(phi)` means universal opacity over phi;
- `j.(phi)` freezes the current time into variable `j` and then evaluates `phi`.

# 17. Atomic Propositions in Formulas

Atomic propositions are the simplest formulas.

For example:

balance

This formula is true exactly in states labeled with `balance`.

If the model contains:

DB satisfies `balance`

then the formula:

balance

is true in state `DB`.

Another example:

cash

is true in states labeled with `cash`, for example `MAN` and `MAQ`.

# 18. Boolean Operators

ETOL supports standard Boolean operators.

## 18.1 Negation

Negation is written using `!`.

!balance

This means:

balance is false

The formula `!balance` is true in every state that is not labeled with `balance`.

## 18.2 Conjunction

Conjunction is written using `&`.

cash & !balance

This means:

cash is true and balance is false

The formula is true in states where both conditions hold.

## 18.3 Disjunction

Disjunction is written using `|`.

cash | balance

This means:

cash is true or balance is true

The formula is true if at least one of the two propositions holds.

# 19. Temporal Operators

Temporal operators describe the behavior of the model along executions.

An execution is a path through the timed automaton.

A path may be seen as a sequence of symbolic states:

(s0, Z0) -> (s1, Z1) -> (s2, Z2) -> ...

where each `si` is a location and each `Zi` is a zone of clock valuations.

## 19.1 Eventually `F`

The eventually operator is written as:

F(phi)

It means that `phi` becomes true at some future point along a path.

Example:

F(cash)

Meaning:

Eventually, the system reaches a state where `cash` is true.

This is a reachability property.

## 19.2 Globally `G`

The globally operator is written as:

G(phi)

It means that `phi` remains true at all future states along a path.

Example:

G(!balance)

Meaning:

The system never reaches a state labeled with `balance`.

This is a safety property.

## 19.3 Until `U`

The until operator is written as:

phi U psi

It means that `phi` must remain true until `psi` becomes true.

Example:

!cash U balance

Meaning:

cash is false until balance becomes true.

## 19.4 Release `R`

The release operator is written as:

phi R psi

Release is the dual of until.

Intuitively, `psi` must remain true unless and until `phi` becomes true.

Example:

cash R !balance

Meaning:

!balance must remain true unless cash becomes true.

# 20. Opacity Operators

ETOL contains two opacity operators:

OE  
OA

These operators are used to reason about whether a secret behavior can be hidden from an observer.

Opacity is useful when the system has secret states or confidential behaviors.

For example, in the ATM model, a balance display state may be labeled as:

balance

The verifier can then check whether this confidential state can be inferred by an external observer.

## 20.1 Existential Opacity `OE`

The existential opacity operator is written as:

OE(phi)

It means:

There exists an opacity-compatible execution satisfying phi.

Example:

OE(balance)

This checks whether there exists an execution compatible with the observer's information in which the system is in a balance state.

Another example:

OE(F(balance))

This means:

There exists an opacity-compatible execution where a balance state is eventually reached.

## 20.2 Universal Opacity `OA`

The universal opacity operator is written as:

OA(phi)

It means:

All opacity-compatible executions satisfy phi.

Example:

OA(G(!balance))

This means:

Along all opacity-compatible executions, the balance state is never revealed.

This is a strong opacity property.

It states that every execution compatible with the observer's information avoids revealing the confidential state.

# 21. Freeze Variables

Freeze variables are used to store the current time.

The syntax is:

j.(phi)

This means:

store the current time in j, then evaluate phi

Example:

j.(F(cash))

The variable `j` stores the time at which the formula evaluation begins.

Freeze variables are useful when combined with timing constraints.

Important restriction:

In this ETOL artifact, timed constraints in formulas should be written directly using the freeze variable, for example:

j <= 10

Do not write constraints such as:

x - j <= 10

because this artifact does not support clock-difference constraints between a model clock and a freeze variable inside formulas.

Therefore, instead of writing:

j.(F(cash & x - j <= 10))

write:

j.(F(cash & j <= 10))

# 22. Timed Constraints in Formulas

Timed formulas may compare the freeze variable with a constant.

Examples of supported timed constraints are:

j <= 10  
j <= 3  
j >= 0

A typical timed formula is:

j.(F(cash & j <= 10))

This means:

Starting from the current time stored in `j`, the system eventually reaches a cash state within 10 time units.

Another example is:

j.(OE(F(balance & j <= 3)))

This means:

There exists an opacity-compatible execution where a balance state is reached within 3 time units.

Important:

The following style should not be used in this artifact:

x - j <= 10

because the formula language used by the artifact does not support this kind of clock-difference expression between a model clock and a freeze variable.

# 23. Examples of ETOL Formulas

This section gives common examples of formulas that may be used with the ATM model.

## Example 1: Reachability

F(cash)

Meaning:

The system can eventually dispense cash.

## Example 2: Safety

G(!balance)

Meaning:

The system never reaches a balance state.

## Example 3: Balance Reachability

F(balance)

Meaning:

The system can eventually reach the balance display state.

## Example 4: Existential Opacity

OE(balance)

Meaning:

There exists an opacity-compatible execution where the balance information is possible.

## Example 5: Universal Opacity

OA(G(!balance))

Meaning:

For all opacity-compatible executions, balance is always false.

## Example 6: Timed Reachability

j.(F(cash & j <= 10))

Meaning:

Cash is eventually dispensed within 10 time units.

## Example 7: Timed Opacity

j.(OE(F(balance & j <= 3)))

Meaning:

There exists an opacity-compatible execution where a balance state is reached within 3 time units.

## Example 8: Bounded Universal Opacity

j.(OA(G(!balance | j <= 3)))

Meaning:

For all opacity-compatible executions, globally, either the system is not in a balance state or the balance state occurs only within the first 3 time units.

This expresses a bounded timed-opacity property.

# 24. Complete Example of a Formula File

A formula file may contain exactly one formula.

Example:

j.(OA(G(!balance | j <= 3)))

This formula means:

1. store the current time in freeze variable `j`;
2. check all opacity-compatible executions;
3. globally verify that either:
   - the current state is not a balance state;
   - or the elapsed time represented by `j` is at most 3 time units.

This expresses a bounded timed-opacity property.

# 25. How the Formula Is Evaluated

The verifier evaluates the formula over the symbolic states of the model.

A symbolic state has the form:

(location, zone)

For example:

(DB, x <= 10)

The location gives the discrete state.

The zone gives the possible clock valuations.

The formula is evaluated as follows:

- an atomic proposition is checked using the labeling function;
- Boolean operators are evaluated using set operations;
- temporal operators are evaluated over paths of the automaton;
- timed constraints are evaluated over clock zones;
- opacity operators are evaluated using observation-compatible executions;
- freeze variables store time values for later comparison.

For example, suppose the symbolic state is:

(DB, x <= 10)

and the labeling function contains:

L(DB) = {balance}

Then:

balance

is true in this symbolic state.

The formula:

!balance

is false in this symbolic state.

# 26. Model Checking Process

The full verification process follows these steps:

1. read the model file;
2. parse the states;
3. parse the initial state;
4. parse the transitions;
5. parse the atomic propositions;
6. parse the labeling function;
7. parse the number of agents;
8. parse the clocks;
9. parse the clock constraints;
10. parse the invariants;
11. construct symbolic zones using DBMs;
12. build the symbolic reachability graph;
13. read and parse the ETOL formula;
14. evaluate the formula on the symbolic graph;
15. return whether the initial symbolic state satisfies the formula.

The result is usually:

SAT

or:

UNSAT

# 27. Creating a New Model

To create a new model, follow the steps below.

## Step 1: Choose the States

Identify the important phases of the system.

Example:

Name_State  
Idle Request Check Success Failure

These states represent the possible locations of the system.

## Step 2: Choose the Initial State

Select where the system starts.

Example:

Initial_State  
Idle

The initial state must be declared in `Name_State`.

## Step 3: Define the Transitions

Describe how the system moves between states.

If the model is written as a graph, first draw or define the arrows between states.

Then convert each arrow into the transition matrix.

For example, if the graph contains:

Idle -> Request  
Request -> Check  
Check -> Success  
Check -> Failure

then the transition matrix must contain non-zero values at exactly these positions.

This is the key idea:

the transition matrix is created from the graph of the input model.

Each non-zero entry corresponds to one arrow in the graph.

## Step 4: Define Atomic Propositions

Choose the logical properties you want to verify.

Example:

Atomic_propositions  
idle checking success failure secret

These propositions can later be used in formulas such as:

F(success)

or:

G(!failure)

## Step 5: Label the States

Assign propositions to states.

Example:

Labelling  
Idle idle  
Check checking secret  
Success success  
Failure failure

This means:

- `Idle` satisfies `idle`;
- `Check` satisfies both `checking` and `secret`;
- `Success` satisfies `success`;
- `Failure` satisfies `failure`.

## Step 6: Declare Clocks

Choose the clocks needed to describe timing.

Example:

Clocks  
x

This declares one clock named `x`.

## Step 7: Add Clock Constraints

Attach guards and resets to transitions.

The clock constraints must be placed at the same positions as the corresponding transitions.

Example:

If the transition matrix contains:

Idle -> Request

then the clock constraint for that transition must also be placed at:

row Idle, column Request

## Step 8: Add Invariants

Restrict how long the system can stay in each state.

Example:

Invariants  
Idle x<=10  
Request x<=5  
Check x<=10  
Success 0  
Failure 0

States `Success` and `Failure` have no timing restriction.

# 28. Creating a New Formula

To create a new formula, follow the steps below.

## Step 1: Identify the Property

First, decide what you want to verify.

Example:

The system should eventually reach success.

## Step 2: Choose the Atomic Proposition

If success is represented by the atomic proposition:

success

then the basic formula is:

success

## Step 3: Add a Temporal Operator

To express eventual reachability, use:

F(success)

This means:

Eventually, success is reached.

## Step 4: Add Timing if Needed

To express that success must be reached within 10 time units, use:

j.(F(success & j <= 10))

This means:

After storing the current time in `j`, success must be reached within 10 time units.

Do not write:

j.(F(success & x - j <= 10))

because this artifact does not support clock-difference constraints such as `x - j` in ETOL formulas.

## Step 5: Add Opacity if Needed

To express that a secret can remain possible under opacity, use:

OE(secret)

To express timed opacity, use:

j.(OE(F(secret & j <= 5)))

This means:

There exists an opacity-compatible execution where a secret state is reached within 5 time units.

# 29. Common Errors

This section lists common input mistakes.

## Unknown State

Example:

Transition  
Idle Unknown

If `Unknown` is not declared in `Name_State`, the model is invalid.

Correct version:

Name_State  
Idle Unknown

Transition  
Idle Unknown

## Unknown Proposition

Example:

Labelling  
Idle waiting

If `waiting` is not declared in `Atomic_propositions`, the model is invalid.

Correct version:

Atomic_propositions  
waiting

Labelling  
Idle waiting

## Unknown Clock

Example:

Clock_constraints  
Idle Request z <= 5

If `z` is not declared in `Clocks`, the model is invalid.

Correct version:

Clocks  
z

Clock_constraints  
Idle Request z <= 5

## Invalid Formula

Example:

G()

This is invalid because `G` requires a subformula.

Correct version:

G(!error)

## Unsupported Clock Difference in Formulas

Do not write:

x - j <= 10

inside ETOL formulas.

Use:

j <= 10

instead.

## Missing Parentheses

Complex formulas should use parentheses.

Not recommended:

OA G !secret

Recommended:

OA(G(!secret))
