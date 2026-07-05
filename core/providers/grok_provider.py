import json
import urllib.request
import urllib.error
from typing import List
from core.providers.base_provider import AIProvider

class GrokProvider(AIProvider):
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
        Generates image(s) using the xAI Grok API.
        Returns a list of URLs pointing to the generated images.
        """
        if not api_key:
            raise ValueError("API Key is missing. Please configure it in Settings.")
            
        url = "https://api.x.ai/v1/images/generations"
        
        # Map size dropdown values to xAI-native resolution & aspect_ratio
        resolution = "2k" if quality == "HD" else "1k"
        aspect_ratio = "1:1"
        
        if size == "1024x768":
            aspect_ratio = "4:3"
        elif size == "768x1024":
            aspect_ratio = "3:4"
            
        payload = {
            "model": "grok-2-image-gen",
            "prompt": prompt,
            "n": num_images,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "response_format": "url"
        }
        
        # If negative prompt is specified, incorporate it into the prompt structure
        if negative_prompt:
            payload["prompt"] = f"{prompt} | Avoid: {negative_prompt}"
            
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "OptiWebP/1.0"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                
            image_urls = []
            if "data" in resp_data:
                for item in resp_data["data"]:
                    if "url" in item:
                        image_urls.append(item["url"])
                    elif "b64_json" in item:
                        image_urls.append(f"data:image/png;base64,{item['b64_json']}")
            
            if not image_urls:
                raise ValueError("No image data returned from Grok API.")
                
            return image_urls
            
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_val = err_json.get("error", "")
                if isinstance(err_val, dict):
                    err_msg = err_val.get("message", str(e))
                elif isinstance(err_val, str) and err_val:
                    err_msg = err_val
                else:
                    err_msg = err_json.get("message", str(e))
            except Exception:
                err_msg = str(e)
            raise RuntimeError(f"Grok API Error ({e.code}): {err_msg}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network Connection Error: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Unexpected Error during generation: {e}")
