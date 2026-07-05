import urllib.parse
import random
from typing import List
from core.providers.base_provider import AIProvider

class PollinationsProvider(AIProvider):
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
        Generates image(s) using the free, no-auth Pollinations.ai API.
        Returns a list of URLs pointing to the generated images.
        """
        # Parse size (default to 1024x1024)
        width, height = 1024, 1024
        if size and "x" in size:
            try:
                w_str, h_str = size.split("x")
                width, height = int(w_str), int(h_str)
            except Exception:
                pass
                
        # Incorporate negative prompt if provided
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt} (avoid: {negative_prompt})"
            
        # URL-encode the prompt
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        image_urls = []
        # Generate URLs with different seeds for uniqueness
        for i in range(num_images):
            seed = random.randint(1, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&private=true&seed={seed}"
            image_urls.append(url)
            
        return image_urls
