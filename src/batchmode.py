#!/usr/bin/env python3.11
# Copyright 2024, Gurobi Optimization , LLC
# This example reads a MIP model from a file, solves it in batch mode,
# and prints the JSON solution string. #
# You will need a Compute Server license for this example to work

import sys
import time
import json
import gurobipy as gp
from gurobipy import GRB

# Set #
# The
# and
# caller's responsibility to dispose of this environment when it's no
# longer needed.


def setupBatchEnv(env):
    env = gp.Env(empty=True)
    env.setParam("LogFile", "batch.log")
    env.setParam("CSManager", "local")
    env.setParam("UserName", "gurobi")
    env.setParam("ServicePassword", "password")
    env.setParam("CSBatchMode", 1)
    return env

# print batch job error information,if any


def printBatchErrorInfo(batch):
    if batch is None or batch.BatchErrorCode == GRB.ERROR:
        return
    print(
        f"Batch ID {batch.BatchID}: Error code {batch.BatchErrorCode} ({batch.BatchErrorMsg}))")

# Create a batch request for given problem file


def newbatchrequest(filename):
    # Start environment, create Model object from file #
    # By using the context handlers for env and model, it is ensured that
    # model.dispose() and env.dispose() are called automatically
    with setupBatchEnv().start() as env, gp.read(filename, env=env) as model:
        # Set some parameters
        model.Params.MIPGap = 0.01
        model.Params.JSONSolDetail = 1
        # Define tags for some variables in order to access their values later
        for count, v in enumerate(model.getVars()):
            v.VTag = f"Variable{count}"
            if count >= 10:
                break
        # Submit batch request
        batchID = model.optimizeBatch()
        
    return batchID


# Wait for the final status of the batch.
# Initially the status of a batch is "submitted"; the status will change # once the batch has been processed (by a compute server).
def waitForFinalstatus(batchID):
    # Wait no longer than one hour
    maxwaittime = 3600
    # Setup and start environment, create local Batch handle object
    with setupBatchEnv().start() as env, gp.Batch(batchID, env) as batch:
        starttime = time.time()
        while batch.BatchStatus == GRB.BATCH_SUBMITTED:
            # Abort this batch if it is taking too long
            curtime = time.time()
            if curtime - starttime > maxwaittime:
                batch.abort()
                break
        
            # Wait for two seconds
            time.sleep(2)
            # Update the resident attribute cache of the Batch object with the # latest values from the cluster manager.
            batch.update()
            # If the batch failed, we retry it
            if batch.BatchStatus == GRB.BATCH_FAILED:
                batch.retry()
        
        # Print information about error status of the job that processed the batch
        printBatchErrorInfo(batch)


def printFinalReport(batchID):
    # Setup and start environment, create local Batch handle object
    with setupBatchEnv().start() as env, gp.Batch(batchID, env) as batch:
        if batch.BatchStatus == GRB.BATCH_CREATED: 
            print("Batch status is 'CREATED'")
        elif batch.BatchStatus == GRB.BATCH_SUBMITTED: 
            print("Batch is 'SUBMITTED")
        elif batch.BatchStatus == GRB.BATCH_ABORTED: 
            print("Batch is 'ABORTED'")
        elif batch.BatchStatus == GRB.BATCH_FAILED:
            print("Batch is 'FAILED'")
        elif batch.BatchStatus == GRB.BATCH_COMPLETED: 
            print("Batch is 'COMPLETED'")
            print("JSON solution:")
            # Get JSON solution as string, create dict from it sol = json.loads(batch.getJSONSolution())
            # Pretty printing the general solution information
            print(json.dumps(sol["SolutionInfo"], indent=4))
            # Write the full JSON solution string to a file
            batch.writeJSONSolution("batch-sol.json.gz")
        else:
            # Should not happen
            print("Batch has unknown BatchStatus") 
        printBatchErrorInfo(batch)

# Instruct the cluster manager to discard all data relating to this BatchID
def batchDiscard(batchID):
    # Setup and start environment, create local Batch handle object
    with setupBatchEnv().start() as env, gp.Batch(batchID, env) as batch:
        # Remove batch request from manager
        batch.discard()

# Solve a given model using batch optimization
if __name__ == "__main__":
    # Ensure we have an input file
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} filename") 
        sys.exit(0)
    # Submit new batch request
    batchID = newbatchrequest(sys.argv[1])
    # Wait for final status
    waitForFinalstatus(batchID)
    # Report final status info
    printFinalReport(batchID)
    # Remove batch request from manager
    batchDiscard(batchID)
    print("Batch optimization OK")