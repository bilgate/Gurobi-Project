import sys
import gurobipy as gp 
from gurobipy import GRB

def dense_optimize(rows,cols, c, Q, A, sense, rhs, lb, ub, vtype, solution):
        model = gp.Model()
        # Add variables to model
        vars = []
        for j in range(cols):
            vars.append(model.addVar(lb=lb[j], ub=ub[j], vtype=vtype[j]))
        # Populate A matrix
        for i in range(rows): 
            expr = gp.LinExpr() 
            for j in range(cols):
                if A[i][j] != 0:
                    expr += A[i][j] * vars[j]
            model.addLConstr(expr, sense[i], rhs[i])
        # Populate objective
        obj = gp.QuadExpr()
        for i in range(cols):
            for j in range(cols): 
                 if Q[i][j] != 0:
                    obj += Q[i][j] * vars[i] * vars[j] 
        for j in range(cols):
            if c[j] != 0:
                obj += c[j] * vars[j]
        model.setObjective(obj)

        # Solve
        model.optimize()
        # Write model to a file
        model.write("dense.lp")

        if model.status == GRB.OPTIMAL:
            x = model.getAttr("X", vars)
            for i in range(cols):
                solution[i] = x[i] 
            return True
        else:
            return False

c = [1, 1, 0]
Q = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
A = [[1, 2, 3], [1, 1, 0]]
sense = [GRB.GREATER_EQUAL , GRB.GREATER_EQUAL]
rhs = [4, 1]
lb = [0, 0, 0]
ub = [GRB.INFINITY , GRB.INFINITY , GRB.INFINITY]
vtype = [GRB.CONTINUOUS , GRB.CONTINUOUS , GRB.CONTINUOUS] 
sol = [0] * 3
# Optimize
success = dense_optimize(2, 3, c, Q, A, sense, rhs, lb, ub, vtype, sol) 
if success:
    print(f"x: {sol[0]:g}, y: {sol[1]:g}, z: {sol[2]:g}")