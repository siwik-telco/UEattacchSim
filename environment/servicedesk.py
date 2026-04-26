from environment.client import Client

class ServiceDesk:

    _is_free:bool =True
    _client_under_service: Client=None

    def __init__(self):
        self._is_free=True
        self._client_under_service=None

    def isFree(self):
        return self._is_free
    
    def PutClient(self, client):
        self._is_free = False
        self._client_under_service = client
        print(f'Client of id {client.id} started service')

    def RemoveClient(self):
        self._is_free = True
        print(f'Client of id {self._client_under_service.id} ended service')
        self._client_under_service=None

        