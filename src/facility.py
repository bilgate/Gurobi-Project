import gurobipy as gp
from gurobipy import GRB


# Warehouse demand in thousands of units
demand = [15, 18, 14, 20]
# Plant capacity in thousands of units
capacity = [20, 22, 17, 19, 18]
# Fixed costs for each plant
fixedCosts = [12000, 15000, 17000 , 13000 , 16000]

# Transportation costs per thousand units
transCosts =[
    [4000,2000,3000,2500,4500], 
    [2500,2600,3400,3000,4000],
    [1200,1800,2600,4100,3000],
    [2200,2600,3100,3700,3200],
]

# Range of plants and warehouses
plants = range(len(capacity)) 
warehouses = range(len(demand))
# Model
m = gp.Model("facility")

# Plant open decision variables: open[p] == 1 if plant p is open.
open = m.addVars(plants , vtype=GRB.BINARY , obj=fixedCosts , name="open")
# Transportation decision variables: transport[w,p] captures the
# optimal quantity to transport to warehouse w from plant p
transport = m.addVars(warehouses , plants , obj=transCosts , name="trans")

m.ModelSense = GRB.MINIMIZE

m.addConstrs(
(transport.sum("*", p) <= capacity[p] * open[p] for p in plants), "Capacity")
m.addConstrs((transport.sum(w) == demand[w] for w in warehouses), "Demand")
m.write("facilityPY.lp")

# First open all plants
for p in plants: 
    open[p].Start = 1.0
# Now close the plant with the highest fixed cost
print("Initial guess:")
maxFixed = max(fixedCosts)
for p in plants:
    if fixedCosts[p] == maxFixed: 
        open[p].Start = 0.0 
        print(f"Closing plant {p}")
        break
print("")


# Use barrier to solve root relaxation
m.Params.Method = 2
# Solve
m.optimize()
# Print solution
print(f"\nTOTAL COSTS: {m.ObjVal:g}") 
print("SOLUTION:")
for p in plants:
    if open[p].X > 0.99: 
        print(f"Plant {p} open") 
        for w in warehouses:
            if transport[w, p].X > 0:
                print(f" Transport {transport[w, p].X:g} units to warehouse {w}")
    else:
        print(f"Plant {p} closed!")
