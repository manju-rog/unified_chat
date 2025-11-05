import json
import os

class ContactsService:
    def __init__(self, json_path=None):
        if json_path is None:
            json_path = os.path.join(os.getcwd(), "contacts_data.json")
        with open(json_path, "r") as f:
            self.data = json.load(f)

    def get_client_contact(self, company_name):
        for name, details in self.data["clients"].items():
            if name.lower() == company_name.lower():
                return details
        return None

    def get_contractor_contact(self, company_name):
        for name, details in self.data["contractors"].items():
            if name.lower() == company_name.lower():
                return details
        return None
