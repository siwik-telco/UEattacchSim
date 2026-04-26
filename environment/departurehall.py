from environment.client import Client
from environment.servicedesk import ServiceDesk
import numpy as np

class DepartureHall:

    def __init__(self):
        self.TPW = 25
        self.TPG = 10
        self.buffer = []
        self.no_users = 0
        self.no_service_Desks = 3
        self.service_Desks= []
        for xx in range(self.no_service_Desks):
            self.service_Desks.append(ServiceDesk())

    def getTPG(self):
        return np.random.randint(1,self.TPG)

    def initialize(self):
        self.buffer = []
        self.no_users = 0
        self.service_Desks= []
        for xx in range(self.no_service_Desks):
            self.service_Desks.append(ServiceDesk())

    def isAnyClient(self):
        return len(self.buffer)>0

    def generate_client(self):
        
        # Use number of users as user ID
        self.no_users +=1
        print(f'Client of id:{self.no_users} entered the departure hall')
        self.buffer.append(Client(self.no_users))

        return self.no_users
    
    def findFreeServiceDesk(self):
        service_desk_id = None
        any_free=False
        for count, servicedesk in enumerate(self.service_Desks):
            if servicedesk.isFree():
                service_desk_id =count
                any_free=True
                break
        if any_free:
            print(f'Service Desk {service_desk_id} is free')
        else:
            print('All service desks are occupied')
        return any_free, service_desk_id   

    def putClientToServiceDesk(self,service_desk_id):
        client = self.buffer.pop(0)
        self.service_Desks[service_desk_id].PutClient(client)

    def removeClientFromServiceDesk(self,service_desk_id):

        self.service_Desks[service_desk_id].RemoveClient()

    def getTPW(self):
        return np.random.randint(1,self.TPW)




