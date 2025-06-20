"""Example implementation for the Art Objects API."""

from typing import Dict, Any, Tuple


class ArtObjectsAPI:
    """Implementation of the Art Objects API."""
    
    def __init__(self):
        # In-memory storage for demo purposes
        self.art_objects = {}
        self.next_id = 1
        
        # Add some sample data
        self.art_objects[1] = {
            "id": 1,
            "title": "Mona Lisa",
            "artist": "Leonardo da Vinci",
            "year": 1503
        }
        self.art_objects[2] = {
            "id": 2,
            "title": "Starry Night",
            "artist": "Vincent van Gogh",
            "year": 1889
        }
        self.next_id = 3
    
    def create_art_object(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Create a new art object."""
        art_object = {
            "id": self.next_id,
            "title": data["title"],
            "artist": data.get("artist", "Unknown"),
            "year": data.get("year")
        }
        
        self.art_objects[self.next_id] = art_object
        self.next_id += 1
        
        return art_object, 201
    
    def get_art_object(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Get an art object by ID."""
        art_object_id = int(data["art_object_id"])
        
        if art_object_id not in self.art_objects:
            return {"error": "Art object not found"}, 404
        
        return self.art_objects[art_object_id], 200
    
    def update_art_object(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Update an art object."""
        art_object_id = int(data["art_object_id"])
        
        if art_object_id not in self.art_objects:
            return {"error": "Art object not found"}, 404
        
        art_object = self.art_objects[art_object_id]
        
        # Update fields that are provided
        if "title" in data:
            art_object["title"] = data["title"]
        if "artist" in data:
            art_object["artist"] = data["artist"]
        if "year" in data:
            art_object["year"] = data["year"]
        
        return art_object, 200
    
    def delete_art_object(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Delete an art object."""
        art_object_id = int(data["art_object_id"])
        
        if art_object_id not in self.art_objects:
            return {"error": "Art object not found"}, 404
        
        del self.art_objects[art_object_id]
        return {}, 204
    
    def list_art_objects(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """List all art objects with pagination."""
        limit = int(data.get("limit", 10))
        offset = int(data.get("offset", 0))
        
        all_objects = list(self.art_objects.values())
        total = len(all_objects)
        
        # Apply pagination
        paginated_objects = all_objects[offset:offset + limit]
        
        return {
            "art_objects": paginated_objects,
            "total": total
        }, 200