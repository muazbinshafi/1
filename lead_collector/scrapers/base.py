from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def fetch_leads(self):
        """
        Fetches leads from a source.
        Returns a list of dictionaries with keys: name, type, city, phone.
        """
        pass
