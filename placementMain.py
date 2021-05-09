import random
import ILP
import experimentConfiguration
import myConfig
import myPlots
import devFailures
import CNoptimization



#****************************************************************************************************

#inizializations and set up

#****************************************************************************************************
random.seed(8)
verbose_log = False

generatePlots = True

ILPoptimization = True
CommunityOptimization = True



cnf_ = myConfig.myConfig()
ec = experimentConfiguration.experimentConfiguration(cnf_)
ec.loadConfiguration(cnf_.myConfiguration_)

ec.networkGeneration()
ec.appGeneration()
ec.userGeneration()



#########################
#    GRAPH PARTITION OPTIMIZATION
#########################

if CommunityOptimization:

    
    cno_ = CNoptimization.CNoptimization(ec,cnf_)
    service2DevicePlacementMatrix = cno_.solve()
    
#########################
#    ILP OPTIMIZATION
#########################


if ILPoptimization:
    ilp_ = ILP.ILP(ec,cnf_)
    service2DevicePlacementMatrixILP = ilp_.solve()


#########################
#    PLOTS FOR THE PAPER
#########################


if generatePlots:

    #****************************************************************************************************
    # unavailability calculation
    #****************************************************************************************************

    failures_ = devFailures.devFailures(ec,cno_, ilp_)
    failures_.createFails()    

    #****************************************************************************************************
    # creating the plots
    #****************************************************************************************************

    
    plot_ = myPlots.myPlots(cno_, ilp_, cnf_, failures_)
    plot_.plotDistanceRequest()
    plot_.plotNodeResource()
    plot_.plotFailures()
    

















    






