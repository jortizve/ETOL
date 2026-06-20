# Input Format Description

This document briefly describes the input formats supported by the ETOL artifact.

## 1. Model files

Model files describe timed automata. A model file contains the following components:

- a finite set of states or locations,
- an initial state,
- a set of atomic propositions,
- a labeling function assigning propositions to states,
- a finite set of clocks,
- invariants attached to locations,
- transitions, optionally equipped with guards and reset sets.

A typical model file therefore specifies both the structure of the automaton and the timing constraints used during model checking.

## 2. Formula files

Each `.etol` file contains a single ETOL formula.

The supported formula language includes:

- `T` for truth,
- atomic propositions P, Q, ...,
- negation, written `!`,
- conjunction, written `&`,
- disjunction, written `|`,
- freeze operators such as `j.(...)`,
- existential opacity operator `OE`,
- universal opacity operator `OA`,
- temporal operators `U` (until) and `R` (release).

## 3. Examples

j.OA(!(MAQ | MAN) U (j<=100))
j.OE(!C U (E & j=100))
j.OE(!cash U j>= 20)
j.OA(DB U j=10)
j.OA(PQW -> !(MAW | MAN) U j>=15)
j.OE(T U (cash & j=100))
j.OE(T U cash)
j.OE(T U j=100)
OE(T U cash)
j.OA(!(MAQ | MAN) U (E & j<=100)) 
OE(T U j.(takeCash & j <= 20))
OA((PQW & x<= 15) U j.(takeCash & j<= 5)) 
x.((!C & x <= 100) & j.OE(correctPwd U (takeCash & j <= 30))) 
OA(!takeCash U j.(E & j =10)) 

### Example model
See:

```text
models/atm.model

Transition 
0 1 0 0 0 0 0 0 0 0 0 0 0 0
0 0 1 0 0 0 0 0 0 0 0 0 0 0
0 0 1 1 0 0 0 0 0 0 0 0 1 0
0 0 0 0 1 0 1 1 0 0 0 0 0 0
0 0 0 0 0 1 0 0 0 0 0 0 1 0
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
0 0s