from abc import ABC, abstractmethod
from typing import List

class AIProvider(ABC):
    @abstractmethod
    def generate_image(
        self, 
        prompt: str, 
        negative_prompt: str, 
        size: str, 
        num_images: int, 
        quality: str,
        api_key: str
    ) -> List[str]:
        """
        Generates images based on prompt and parameters.
        Returns a list of URLs or image bytes/data that can be downloaded/saved.
        """
        pass
