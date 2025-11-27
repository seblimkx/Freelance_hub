class Profile:
    def __init__(self, username, profile_type, password,id = None, services = None, resume = None):
        self.username = username
        self.profile_type = profile_type
        self.password = password
        self.services = services if services else []
        self.id = id
        self.resume = resume

    def is_buyer(self):
        return self.profile_type == "buyer"
    
    def is_seller(self):
        return self.profile_type == "seller"
    