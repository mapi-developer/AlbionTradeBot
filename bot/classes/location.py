class Location:
    def __init__(self):
        self.location_id = ''
        self.location_type = ''
        self.location_name = ''

    def __repr__(self):
        return f"Id: {self.location_id} | Type: {self.location_type} | Name: {self.location_name}"