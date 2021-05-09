import networkx as nx
import random
import copy

class devFailures:
    
    def __init__(self, ec, cna, ilp):
        
        self.ec = ec
        self.cna = cna
        self.ilp = ilp
    
            
    
    
    def isServiceReachableFromGtw(self,userGtwId, servId, G_, placement_):
        
        if userGtwId not in G_.nodes:
            return False
        
        for devId,allocated in enumerate(placement_[servId]):
            if allocated:
                if devId in G_.nodes:
                    if nx.has_path(G_,userGtwId,devId):
                        return True
        

        return False
    
    
    def generateFauls(self,failOrdered, G_, unavailableList, placement_):
    
        for i in failOrdered:
            
            G_.remove_node(i)
        
            unavailable = 0
            total = 0
            
            for appId,userGtwSet in enumerate(self.ec.appsRequests):
                for userGtwId in userGtwSet:
                    for servId in self.ec.apps[appId].nodes:
                        available_ = self.isServiceReachableFromGtw(userGtwId, servId, G_, placement_)
                        
                        if not available_:
                            break
                    if not available_:
                        unavailable = unavailable + 1
                    
                    total = total + 1
                        

            unavailableList.append(unavailable)
    
    
    def createFails(self):
        
        Gilp = copy.deepcopy(self.ec.G)
        Gcommunity = copy.deepcopy(self.ec.G)

                
                
        
        iSeed = 28
        failRnd = random.Random()
        failRnd.seed(iSeed)
        failOrdered = list(range(0,len(self.ec.G.nodes)))
        failRnd.shuffle(failOrdered)
        
        self.unavailableILPrnd = list()
        self.unavailableCommunityrnd = list()
        self.unavailableAllinGtwsrnd = list()
        
        
        G_ = copy.deepcopy(Gilp)
        self.generateFauls(failOrdered, G_, self.unavailableILPrnd, self.ilp.service2DevicePlacementMatrixILP)
        
        
        
        
        G_ = copy.deepcopy(Gcommunity)
        self.generateFauls(failOrdered, G_, self.unavailableCommunityrnd, self.cna.service2DevicePlacementMatrix)
        

        
        G_ = copy.deepcopy(Gcommunity)
        placement_ = [[0 for j in range(len(self.ec.G.nodes))] for i in range(self.ec.numberOfServices)]     
        for appId,userGtwSet in enumerate(self.ec.appsRequests):
            for userGtwId in userGtwSet:
                for servId in self.ec.apps[appId].nodes:
                    placement_[servId][userGtwId]=1       
        self.generateFauls(failOrdered, G_, self.unavailableAllinGtwsrnd, placement_)
        
    
