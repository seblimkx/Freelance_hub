"""Freelance Post model"""

class freelance_post:
    def __init__(self, title, description, price, id, resume, seller_username, image_url=None):
        self.title = title
        self.description = description
        self.price = price
        self.id = id
        self.resume = resume
        self.seller_username = seller_username
        self.image_url = image_url or "/static/default_image.png"

    def post(self):
        return f"Post(title = {self.title}, content = {self.description})"
