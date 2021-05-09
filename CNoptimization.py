import numpy as np
import random as random
import sys
import population as pop
import matplotlib.pyplot as plt3d
import copy
from datetime import datetime



class GA:
    
    
    
    def __init__(self, system, populationSeed,evolutionSeed):
        
        
        
        self.system = system
        

import operator
import networkx as nx
import json
import time
from networkx.algorithms import community
import itertools
import myTime

class CNoptimization:
    
    def __init__(self, ec,cnf):
        
        self.ec = ec
        self.cnf = cnf
        
        #(deadline,shortestdistance):occurrences
        self.statisticsDistanceDeadline = {}
        
        #(service,deadline):occurrences
        self.statisticsServiceInstances = {}
        
        
        #distance:numberOfuserThatRequest
        self.statisticsDistancesRequest = {}
        
        #nodeid:numberOfuserThatRequest
        self.statisticsNodesRequest = {}
        
        #(nodeid,serviceId):ocurrences
        self.statisticsNodesServices = {}
        
        #(centrality,resources):occurrences
        self.statisticsCentralityResources = {}
        

   


    def communityCalculation(self, GRAPH,reverseOrd):
        
        timecom = time.time()
        communities_generator = community.girvan_newman(GRAPH)
        print ("Calculating the communities in ...."+str(time.time()-timecom))
    
    
        allCommunities = set()
        communityLevel = {}
        allCommunities.add(frozenset(GRAPH.nodes))
        communityLevel[frozenset(GRAPH.nodes)]=0
        i = 1
        for communities in itertools.islice(communities_generator, GRAPH.number_of_nodes()):
            if self.cnf.verbose_log:
                print(tuple(sorted(c) for c in communities))
            for c in communities:
                allCommunities.add(frozenset(c))
                communityLevel[frozenset(c)]=i
            i=i+1
    
        sorted_ = sorted(communityLevel.items(), key=operator.itemgetter(1), reverse=reverseOrd)
    
        return sorted_
    


 

        
    def solve(self):
        
        
        t = time.time()
        
        m = myTime.myTime(True)
        
        self.sortedCommunities=self.communityCalculation(self.ec.G, reverseOrd=True)
        m.c("community calculated in ")
        self.appsCommunities = list()
        for APP in self.ec.apps:
            topologicorder_ = list(nx.topological_sort(APP))
            source = topologicorder_[0]
            self.appsCommunities.append(self.transitiveClosureCalculation(source,APP))
        
        self.service2DevicePlacementMatrix = [[0 for j in range(len(self.ec.G.nodes))] for i in range(self.ec.numberOfServices)]

        
        self.centralityValuesNoOrdered = nx.betweenness_centrality(self.ec.G,weight="weight")
        

        
        community2AppPlacementDict = {}
        for myCommunity in self.sortedCommunities:
            community2AppPlacementDict[myCommunity[0]]=set()
        
        self.nodeBussyResources = {}
        for i in self.ec.G.nodes:
            self.nodeBussyResources[i]=0.0
        
     
        
        sortedAppsDeadlines = sorted(self.ec.appsDeadlines.items(), key=operator.itemgetter(1))
        

        
        print ("Starting placement policy.....")
        
        for appToAllocate in sortedAppsDeadlines:
            appId=appToAllocate[0]
            self.weightNetwork(appId)
            nodesWithClients = self.ec.appsRequests[appId]
            for clientId in nodesWithClients:
                if self.cnf.verbose_log:
                    print ("Starting placement of app "+str(appId)+" for client "+str(clientId))
                placed_=False
                for myCommunity in self.sortedCommunities:
                    if clientId in myCommunity[0]:
                        if appId in community2AppPlacementDict[myCommunity[0]]:
                            if self.cnf.verbose_log:
                                print ("    App "+str(appId)+" already placed in community "+str(myCommunity[0]))
                            break
                        else:
                            placed_,servicePlacement=self.placeAppInCommunity(appId, clientId, myCommunity[0])
                            if placed_:
                                if self.cnf.verbose_log:
                                    print ("    Performed allocation of app "+str(appId)+" in community "+str(myCommunity[0]))
                                for servId,deviceId in servicePlacement.items():
                                    self.service2DevicePlacementMatrix[servId][deviceId]=1
                                    self.nodeBussyResources[deviceId]=self.nodeBussyResources[deviceId]+self.ec.appsResources[appId][servId]
                                community2AppPlacementDict[myCommunity[0]].add(appId)
                                placed_=True
                                break
                            
        m.c("placement finished")
        
        
        self.writeStatisticsDevices(self.service2DevicePlacementMatrix)
        
        servicesInCloud = 0
        servicesInFog = 0
        
        allAlloc = {}
        myAllocationList = list()
        for idServ in range(self.ec.numberOfServices):
            for idDevice in range(len(self.ec.G.nodes)):
                if self.service2DevicePlacementMatrix[idServ][idDevice]==1:
                    myAllocation = {}
                    myAllocation['app']=self.ec.mapService2App[idServ]
                    myAllocation['module_name']=self.ec.mapServiceId2ServiceName[idServ]
                    myAllocation['id_resource']=idDevice
                    myAllocationList.append(myAllocation)
                    servicesInFog = servicesInFog +1
          
            myAllocation = {}
            myAllocation['app']=self.ec.mapService2App[idServ]
            myAllocation['module_name']=self.ec.mapServiceId2ServiceName[idServ]
            myAllocation['id_resource']=self.ec.cloudId
            myAllocationList.append(myAllocation)
            servicesInCloud = servicesInCloud +1    
        
        self.nodeResUse, self.nodeNumServ = self.calculateNodeUsage(self.service2DevicePlacementMatrix)
        print ("Number of services in cloud (partition) (servicesInCloud): "+str(servicesInCloud))
        print ("Number of services in fog (partition) (servicesInFog): "+str(servicesInFog))
        
        
        allAlloc['initialAllocation']=myAllocationList
        
        file = open(self.cnf.resultFolder+"/allocDefinition.json","w")
        file.write(json.dumps(allAlloc))
        file.close()
        
        print (str(time.time()-t)+" time for partition-based optimization")
        
        return self.service2DevicePlacementMatrix
        

    def devicesFirstFitDescendingOrder(self,community,clientId,appId):
    
        mips_ = float(self.ec.appsTotalMIPS[appId])
        nodeFitness = {}
    
        for devId in community:
            if self.cnf.verbose_log:
                print ("fitness for device "+str(devId)+ " from client "+str(clientId))
            processTime = mips_ / float(self.ec.devices[devId]['IPT']) 
            if self.cnf.verbose_log:
                print (processTime)
            netTime = nx.shortest_path_length(self.ec.G,source=clientId,target=devId,weight="weight")    
            if self.cnf.verbose_log:
                print (netTime)
            nodeFitness[devId] = processTime + netTime
    
    
        sorted_ = sorted(nodeFitness.items(), key=operator.itemgetter(1))
    
        sortedList = list()
    
        for i in sorted_:
            sortedList.append(i[0])
    
        return sortedList
    

    
    def weightNetwork(self,appId):
        size = float(self.ec.appsSourceMessage[appId]['bytes'])
        for e in self.ec.G.edges:
            self.ec.G[e[0]][e[1]]['weight']=float(self.ec.G[e[0]][e[1]]['PR'])+ (size/float(self.ec.G[e[0]][e[1]]['BW']))
    
    

    
    
    
    def placeAppInCommunity(self,appId, clientId, candidateCommunity):
    
        servicesToPlace = set()
        for i in self.ec.apps[appId].nodes:
            servicesToPlace.add(i)
    
        orderedDevices=self.devicesFirstFitDescendingOrder(candidateCommunity,clientId,appId) 
    
        availableResourcesNodes = {}
        availableSpeedNodes = {}
    
        tempServiceAlloc = {}
        for servId in self.ec.apps[appId].nodes:
            tempServiceAlloc[servId]= None
    
        for devId in orderedDevices:
            availableResourcesNodes[devId]=self.ec.nodeResources[devId]-self.nodeBussyResources[devId]
            availableSpeedNodes[devId]=self.ec.nodeSpeed[devId]
    
    
    
            for appCommu in self.appsCommunities[appId].items():
    
                listOfTransitiveClosures = sorted(appCommu[1], key=lambda x: len(x),reverse=True)
                
                
    
    
    
                for serviceSet in listOfTransitiveClosures:
    
    
                    if len(serviceSet & servicesToPlace)>0:  
                        requiredResources = 0.0
                        for service in serviceSet:
                            requiredResources = requiredResources + self.ec.appsResources[appId][service]
                        if availableResourcesNodes[devId]>requiredResources:
                            servicesToPlace = servicesToPlace - serviceSet
                            if self.cnf.verbose_log:
                                print ("        Temp-allocation of services "+str(serviceSet)+" in device "+str(devId))
                            for service in serviceSet:
                                tempServiceAlloc[service]= devId
                            availableResourcesNodes[devId] = availableResourcesNodes[devId] - requiredResources
    
                            if len(servicesToPlace)==0:
                                self.writeStatisticsAllocation(tempServiceAlloc,clientId,appId)
                                return True,tempServiceAlloc
    
        if self.cnf.verbose_log:
            print ("        Rejected the temporal allocations")
            print ("        Application not allocated in community")
        myemptydict = {}
        return False, myemptydict
    
    

    def writeStatisticsAllocation(self,tempServiceAlloc,clientId,appId):
    
        for talloc_ in tempServiceAlloc.items():
    
            dist_ = nx.shortest_path_length(self.ec.G,source=clientId,target=talloc_[1],weight="weight")
    
            mykey_=dist_
            if mykey_ in self.statisticsDistancesRequest:
                self.statisticsDistancesRequest[mykey_]= self.statisticsDistancesRequest[mykey_]+1
            else:
                self.statisticsDistancesRequest[mykey_]=1
    
            mykey_=talloc_[1]
            if mykey_ in self.statisticsNodesRequest:
                self.statisticsNodesRequest[mykey_]= self.statisticsNodesRequest[mykey_]+1
            else:
                self.statisticsNodesRequest[mykey_]=1
    
            mykey_=(talloc_[1],talloc_[0])
            if mykey_ in self.statisticsNodesServices:
                self.statisticsNodesServices[mykey_]= self.statisticsNodesServices[mykey_]+1
            else:
                self.statisticsNodesServices[mykey_]=1
    
    
            mykey_=(self.ec.appsDeadlines[appId],dist_)
            if mykey_ in self.statisticsDistanceDeadline:
                self.statisticsDistanceDeadline[mykey_]= self.statisticsDistanceDeadline[mykey_]+1
            else:
                self.statisticsDistanceDeadline[mykey_]=1
    
            mykey_=(talloc_[0],self.ec.appsDeadlines[appId])
            if mykey_ in self.statisticsServiceInstances:
                self.statisticsServiceInstances[mykey_]=self.statisticsServiceInstances[mykey_]+1
            else:
                self.statisticsServiceInstances[mykey_]=1
    

    
    
    def writeStatisticsDevices(self,service2DevicePlacementMatrix):
    
    
        for devId in self.ec.G.nodes:
            mypercentageResources_ = float(self.nodeBussyResources[devId])/float(self.ec.nodeResources[devId])
            mycentralityValues_ = self.centralityValuesNoOrdered[devId]
            mykey_=(mycentralityValues_,mypercentageResources_)
            if mykey_ in self.statisticsCentralityResources:
                self.statisticsCentralityResources[mykey_]=self.statisticsCentralityResources[mykey_]+1
            else:
                self.statisticsCentralityResources[mykey_]=1
    
    
    
    
    def calculateNodeUsage(self,service2DevicePlacementMatrix):
        
        
        nodeResUse = list()
        nodeNumServ = list()
        
        for i in service2DevicePlacementMatrix[0]:
            nodeResUse.append(0.0)
            nodeNumServ.append(0)
            
        for idServ in range(0,len(service2DevicePlacementMatrix)):
            for idDev in range(0,len(service2DevicePlacementMatrix[idServ])):
                if service2DevicePlacementMatrix[idServ][idDev]==1:
                    nodeNumServ[idDev]=nodeNumServ[idDev]+1
                    nodeResUse[idDev]=nodeResUse[idDev]+self.ec.servicesResources[idServ]
                    
        for idDev in range(0,len(service2DevicePlacementMatrix[0])):
            nodeResUse[idDev] = nodeResUse[idDev] / self.ec.nodeResources[idDev]
            
        nodeResUse = sorted(nodeResUse)
        nodeNumServ = sorted(nodeNumServ)
        
    
        return nodeResUse, nodeNumServ 
    
    
    
    #****************************************************************************************************
    
    #funtions for the transitive closures
    
    #****************************************************************************************************
    
    
    
    def normalizeSmallerSetsInSameLevel(self,transitivesClosures):
    
    
        for n in transitivesClosures:
            tmpList = list(transitivesClosures[n])
            for i in range(0,len(tmpList)):
                for j in range(i+1,len(tmpList)):
                    if (tmpList[i] & tmpList[j])==tmpList[i]:
                        transitivesClosures[n].remove(tmpList[i])
    
    
    
    def createSetFromSetOfSets(self,setofsets):
    
        finalset = set()
        for i in setofsets:
            finalset = finalset | set(i)
    
        return finalset
    
    
    def normalizeIncludePrevious(self,transitivesClosures):
    
    
        previous = transitivesClosures[0]
    
        for n in transitivesClosures:
            if self.cnf.verbose_log:
                print ("level")
                print (n)
            toInclude = set()
            for i in transitivesClosures[n]:
                current =  self.createSetFromSetOfSets(transitivesClosures[n])
                for j in previous:
                    if len(j & current)==0:
                        if self.cnf.verbose_log:
                            print ("individual")
                            print (j)
                        toInclude.add(j)
            if self.cnf.verbose_log:
                print ("final")
                print (toInclude)
            transitivesClosures[n] = transitivesClosures[n] | toInclude
            previous = transitivesClosures[n]
    
    
    
    
    
    def getTransitiveClosures(self,source, app_, transitivesClosures,cycles_, level):

    
        if self.cnf.verbose_log:
            print (source)

        neighbords_=list(app_.neighbors(source))
        if not level in transitivesClosures:
            transitivesClosures[level] = set()
    
        descendantsOfNeighbords = set()
        for i in neighbords_:
            descendantsOfNeighbords = descendantsOfNeighbords | set(nx.descendants(app_,i))
    
    
    

    
        tmp=set(nx.descendants(app_,source))
        tmp.add(source)
        tmp = frozenset(tmp)

        if not tmp in transitivesClosures[level]:
            if self.cnf.verbose_log:
                print (tmp)
            transitivesClosures[level].add(tmp)
            if not tmp in cycles_:
    
    
    
                if len(neighbords_)>0:
                    if not (level+1) in transitivesClosures:
                        transitivesClosures[level+1] = set()
    
    
    
                    tmp = set()
                    tmp.add(source)
                    transitivesClosures[level+1].add(frozenset(tmp))
    
    
                for n in neighbords_:
    

    
                    self.getTransitiveClosures(n,app_,transitivesClosures,cycles_,level+1)

    



    def transitiveClosureCalculation(self,source,app_):
    
    
        transitivesClosures = {}
    
    
        cycles_ = set()
    
        for i in nx.simple_cycles(app_):
            if self.cnf.verbose_log:
                print (i)
            tmp = frozenset(i)
            if self.cnf.verbose_log:
                print (tmp)
            cycles_.add(tmp)
    
    
        self.getTransitiveClosures(source,app_,transitivesClosures,cycles_,0)
    
        self.normalizeSmallerSetsInSameLevel(transitivesClosures)
    
        self.normalizeIncludePrevious(transitivesClosures)
    
        return transitivesClosures


                
        
    
