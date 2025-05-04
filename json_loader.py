import json
import os

class OblivionDataLoader:
    """Class to load and organize all JSON data for the Oblivion Console Manager"""
    
    def __init__(self, data_directory="data"):
        self.data_directory = data_directory
        self.categories = []
        self.commands = {}
        self.items = {}
        self.category_map = {}
        
        # Define category icons and descriptions
        self.category_info = {
            "Useful Cheats": {"icon": "⭐", "description": "Commonly used cheats and commands"},
            "Character": {"icon": "🧙", "description": "Commands affecting your character's abilities and stats"},
            "Items": {"icon": "🎒", "description": "Commands for adding or removing items"},
            "World": {"icon": "🌍", "description": "Commands affecting the game world and environment"},
            "Toggle": {"icon": "🔄", "description": "Commands that toggle game features on/off"},
            "Targeted": {"icon": "🎯", "description": "Commands that affect a specific target"},
            "Quest": {"icon": "📜", "description": "Commands related to quests"},
            "Weapons": {"icon": "⚔️", "description": "All weapon IDs in the game"},
            "Armor": {"icon": "🛡️", "description": "All armor IDs in the game"},
            "Spells": {"icon": "✨", "description": "All spell IDs in the game"},
            "Potions": {"icon": "🧪", "description": "All potion and drink IDs in the game"},
            "Books": {"icon": "📚", "description": "All book and scroll IDs in the game"},
            "Clothing": {"icon": "👕", "description": "All clothing, amulet, and ring IDs in the game"},
            "Miscellaneous": {"icon": "🔮", "description": "All miscellaneous item IDs in the game"},
            "NPCs": {"icon": "👤", "description": "All NPC IDs in the game"},
            "Locations": {"icon": "🏙️", "description": "All location IDs in the game"},
            "Keys": {"icon": "🔑", "description": "All key IDs in the game"},
            "Horses": {"icon": "🐴", "description": "All horse IDs in the game"},
            "Soul Gems": {"icon": "💎", "description": "All soul gem IDs in the game"},
            "Sigil Stones": {"icon": "🌟", "description": "All sigil stone IDs in the game"},
            "Alchemy Equipment": {"icon": "⚗️", "description": "All alchemy equipment IDs in the game"},
            "Alchemy Ingredients": {"icon": "🌿", "description": "All alchemy ingredient IDs in the game"},
            "Arrows": {"icon": "🏹", "description": "All arrow IDs in the game"},
            "Favorites": {"icon": "❤️", "description": "Your favorite commands and items"}
        }
        
        # Map filename prefixes to categories
        self.file_category_map = {
            "useful cheats": "Useful Cheats",
            "all toggle commands": "Toggle",
            "all quest commands": "Quest",
            "target commands": "Targeted",
            "all weapons ids": "Weapons",
            "all armor ids": "Armor",
            "all spells ids": "Spells",
            "all potions and drinks ids": "Potions",
            "all books and scrolls ids": "Books",
            "all clothing_amulets_and_rings ids": "Clothing",
            "all clothing_ amulets_ and rings ids": "Clothing",  # Alternative spacing format
            "all miscellaneous ids": "Miscellaneous",
            "all npc ids": "NPCs",
            "all locations ids": "Locations",
            "all keys ids": "Keys",
            "all horses ids": "Horses",
            "all soul gems ids": "Soul Gems",
            "all sigil stone ids": "Sigil Stones",
            "all alchemy equipment ids": "Alchemy Equipment",
            "all alchemy ingredients ids": "Alchemy Ingredients",
            "all arrow ids": "Arrows"
        }
        
    def load_all_json_data(self):
        """Load all JSON files and organize them into appropriate structures"""
        # Ensure the data directory exists
        if not os.path.exists(self.data_directory):
            print(f"Data directory not found: {self.data_directory}")
            return False
        
        # List all JSON files in the directory
        json_files = [f for f in os.listdir(self.data_directory) if f.endswith('.json')]
        
        for json_file in json_files:
            file_path = os.path.join(self.data_directory, json_file)
            file_base = json_file.lower().replace('.json', '')
            
            # Find the category for this file
            category = None
            
            # First try direct mapping
            for prefix, cat in self.file_category_map.items():
                if file_base == prefix or file_base.startswith(prefix):
                    category = cat
                    break
            
            # If not found, try a more flexible approach by checking if key parts are in the filename
            if category is None:
                for prefix, cat in self.file_category_map.items():
                    # Extract key parts from the prefix (excluding common words like "all" and "ids")
                    key_parts = [p for p in prefix.split() if p not in ["all", "ids"]]
                    
                    # Check if all key parts are in the filename
                    if all(part in file_base for part in key_parts):
                        category = cat
                        break
            
            if category is None:
                print(f"Unknown category for file: {json_file}")
                # Special handling for specific files we know about
                if "clothing" in file_base and "amulets" in file_base and "rings" in file_base:
                    category = "Clothing"
                    print(f"  -> Assigning to Clothing category")
                elif "potions" in file_base:
                    category = "Potions"
                    print(f"  -> Assigning to Potions category")
                else:
                    continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Process based on category type
                self._process_file_data(data, category, file_base)
                
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        # Create category list for UI
        for category, info in self.category_info.items():
            if category != "Favorites":  # Skip Favorites - handled separately
                self.categories.append({
                    "name": category,
                    "icon": info["icon"],
                    "description": info["description"]
                })
        
        return True
    
    def _process_file_data(self, data, category, file_base):
        """Process data from a file based on its category"""
        # Skip if empty data
        if not data:
            return
        
        # Handle different file types based on their content structure
        if category == "Useful Cheats":
            self._process_command_data(data, category)
        elif category == "Toggle":
            self._process_command_data(data, category)
        elif category == "Quest":
            self._process_command_data(data, category)
        elif category == "Targeted":
            self._process_command_data(data, category)
        else:
            # Process item data (weapons, armor, spells, etc.)
            self._process_item_data(data, category)
    
    def _process_command_data(self, data, category):
        """Process command data"""
        for item in data:
            if "Command" not in item:
                continue
                
            # Extract command name and parameters
            cmd_text = item["Command"]
            cmd_parts = cmd_text.split(" ")
            cmd_name = cmd_parts[0]
            
            # Build command structure
            cmd_data = {
                "description": item.get("Description", "No description available"),
                "syntax": cmd_text,
                "parameters": cmd_parts[1:] if len(cmd_parts) > 1 else [],
                "category": category,
                "example": item.get("Example", "")
            }
            
            # Store command
            self.commands[cmd_name] = cmd_data
            
            # Track which commands belong to which category
            if category not in self.category_map:
                self.category_map[category] = []
            
            self.category_map[category].append(cmd_name)
    
    def _process_item_data(self, data, category):
        """Process item data"""
        for item in data:
            # Determine item name and ID based on the file type
            item_name = None
            item_id = None
            command = None
            
            # Try to extract common fields
            if "Name" in item:
                item_name = item["Name"]
            
            # Extract ID based on category
            if category == "Weapons":
                item_id = item.get("Weapon ID")
            elif category == "Armor":
                item_id = item.get("Armor ID")
            elif category == "Spells":
                item_id = item.get("Spell ID")
            elif category == "Books":
                item_id = item.get("Book ID")
            elif category == "Clothing":
                item_id = item.get("ID")
            elif category == "Miscellaneous":
                item_id = item.get("ID")
            elif category == "NPCs":
                item_id = item.get("NPC ID")
            elif category == "Locations":
                item_id = item.get("Location ID")
                item_name = item_id  # Use location ID as name if no name provided
            elif category == "Keys":
                item_id = item.get("Key ID")
            elif category == "Horses":
                item_id = item.get("Horse ID")
            elif category == "Soul Gems":
                item_id = item.get("Soul Gem ID")
            elif category == "Sigil Stones":
                # Sigil stones have multiple IDs - use Ascendent as default
                item_id = item.get("Ascendent ID")
                item_name = item.get("Effect")
            elif category == "Alchemy Equipment":
                item_id = item.get("Equipment ID")
            elif category == "Alchemy Ingredients":
                item_id = item.get("Ingredient ID")
            elif category == "Arrows":
                item_id = item.get("Arrow ID")
            elif category == "Potions":
                # Try different possible ID field names
                item_id = (item.get("Ingredient ID") or 
                          item.get("Potion ID") or 
                          item.get("ID"))
            
            # Extract command if available
            command = item.get("Copy Paste Cheat")
            
            # Skip if missing essential data
            if not item_name or not item_id:
                continue
            
            # Build item structure
            item_data = {
                "name": item_name,
                "id": item_id,
                "command": command if command else self._get_default_command(category, item_id),
                "category": category,
                # Copy all original fields
                "original_data": {k: v for k, v in item.items()}
            }
            
            # Generate a unique key for this item
            item_key = f"{category}_{item_name}"
            
            # Store item
            self.items[item_key] = item_data
            
            # Track which items belong to which category
            if category not in self.category_map:
                self.category_map[category] = []
            
            self.category_map[category].append(item_key)
    
    def _get_default_command(self, category, item_id):
        """Get the default command for an item based on its category"""
        if category == "NPCs":
            return f"player.placeatme {item_id}"
        elif category == "Spells":
            return f"player.addspell {item_id}"
        elif category == "Locations":
            return f"coc {item_id}"
        else:
            # Default for items (weapons, armor, etc.)
            return f"player.additem {item_id} 1"
    
    def get_all_commands(self):
        """Get all commands"""
        return self.commands
    
    def get_all_items(self):
        """Get all items"""
        return self.items
    
    def get_category_commands(self, category):
        """Get all commands in a category"""
        if category not in self.category_map:
            return []
        
        result = []
        for cmd_key in self.category_map[category]:
            if cmd_key in self.commands:
                result.append((cmd_key, self.commands[cmd_key]))
        
        return result
    
    def get_category_items(self, category):
        """Get all items in a category"""
        if category not in self.category_map:
            return []
        
        result = []
        for item_key in self.category_map[category]:
            if item_key in self.items:
                result.append((item_key, self.items[item_key]))
        
        return result
    
    def get_categories(self):
        """Get all categories"""
        return self.categories
    
    def get_category_info(self, category):
        """Get information about a category"""
        return self.category_info.get(category, {
            "icon": "⚙️",
            "description": "Miscellaneous data"
        })

# Usage example:
if __name__ == "__main__":
    loader = OblivionDataLoader()
    if loader.load_all_json_data():
        print(f"Loaded {len(loader.commands)} commands and {len(loader.items)} items")
        
        # Print categories
        for category in loader.categories:
            print(f"{category['icon']} {category['name']}: {category['description']}")