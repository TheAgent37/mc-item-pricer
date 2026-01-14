#!/usr/bin/env python3
"""
Minecraft Item Valuation System
Works with any Minecraft version - just provide the _all.json recipe file

Usage:
    python main.py                          # Interactive mode
    python main.py --explore                # Explore existing values
    python main.py --auto                   # Auto-calculate with defaults
    python main.py --multiply 2.0           # Make everything 2x more expensive
    python main.py --set diamond=500        # Set specific base item values
    python main.py --adjust iron_sword=50   # Override specific item values
"""

import json
import argparse
import sys
from collections import defaultdict, deque
from pathlib import Path


class MinecraftItemValuer:
    """Universal Minecraft recipe parser and item valuer"""

    def __init__(self, recipes_file="_all.json"):
        """Initialize with a Minecraft recipes JSON file"""
        self.recipes_file = recipes_file
        self.recipes = {}
        self.item_values = {}
        self.base_items = set()
        self.recipe_graph = defaultdict(list)
        self.dependencies = defaultdict(set)

        if Path(recipes_file).exists():
            with open(recipes_file, "r", encoding="utf-8") as f:
                self.recipes = json.load(f)
            self._parse_recipes()
        else:
            print(f"❌ Recipe file '{recipes_file}' not found!")
            sys.exit(1)

    def _extract_item_name(self, item_ref):
        """Extract clean item name from item reference or tag"""
        if not item_ref:
            return None
        return item_ref.replace("minecraft:", "").lstrip("#")

    def _parse_recipes(self):
        """Parse all recipes and build dependency graph"""
        for recipe_name, recipe_data in self.recipes.items():
            recipe_type = recipe_data.get("type", "")
            result_item = None
            result_count = 1
            ingredients = []

            # Extract result
            if "result" in recipe_data:
                result = recipe_data["result"]
                if isinstance(result, dict):
                    result_item = self._extract_item_name(result.get("id", ""))
                    result_count = result.get("count", 1)
                elif isinstance(result, str):
                    result_item = self._extract_item_name(result)

            if not result_item:
                continue

            # Extract ingredients based on recipe type
            if "crafting" in recipe_type:
                ingredients = self._extract_crafting_ingredients(recipe_data)
            elif recipe_type in [
                "minecraft:smelting",
                "minecraft:blasting",
                "minecraft:smoking",
                "minecraft:campfire_cooking",
            ]:
                ingredients = self._extract_single_ingredient(recipe_data)
            elif recipe_type == "minecraft:stonecutting":
                ingredients = self._extract_single_ingredient(recipe_data)
            elif recipe_type == "minecraft:smithing_transform":
                ingredients = self._extract_smithing_ingredients(recipe_data)

            if ingredients:
                self.recipe_graph[result_item].append(
                    {
                        "name": recipe_name,
                        "ingredients": ingredients,
                        "result_count": result_count,
                    }
                )

                for item, count in ingredients:
                    self.dependencies[result_item].add(item)

    def _extract_crafting_ingredients(self, recipe_data):
        """Extract ingredients from crafting recipes"""
        ingredient_counts = defaultdict(int)

        # Shapeless crafting
        if "ingredients" in recipe_data:
            ingredients = recipe_data["ingredients"]
            if isinstance(ingredients, list):
                for ing in ingredients:
                    if isinstance(ing, str):
                        item = self._extract_item_name(ing)
                        if item:
                            ingredient_counts[item] += 1
                    elif isinstance(ing, dict):
                        item = self._extract_item_name(
                            ing.get("id") or ing.get("item", "")
                        )
                        if item:
                            ingredient_counts[item] += 1

        # Shaped crafting
        if "key" in recipe_data:
            pattern = recipe_data.get("pattern", [])
            key = recipe_data["key"]

            for row in pattern:
                for char in row:
                    if char != " " and char in key:
                        key_value = key[char]
                        if isinstance(key_value, str):
                            item = self._extract_item_name(key_value)
                            if item:
                                ingredient_counts[item] += 1
                        elif isinstance(key_value, list):
                            item = self._extract_item_name(key_value[0])
                            if item:
                                ingredient_counts[item] += 1

        return list(ingredient_counts.items())

    def _extract_single_ingredient(self, recipe_data):
        """Extract ingredient from smelting/stonecutting"""
        ingredient = recipe_data.get("ingredient", "")
        if isinstance(ingredient, str):
            item = self._extract_item_name(ingredient)
            return [(item, 1)] if item else []
        return []

    def _extract_smithing_ingredients(self, recipe_data):
        """Extract ingredients from smithing recipes"""
        ingredients = []
        for key in ["base", "addition", "template"]:
            value = recipe_data.get(key, "")
            if value:
                item = self._extract_item_name(value)
                if item:
                    ingredients.append((item, 1))
        return ingredients

    def identify_base_items(self):
        """Find items that have no recipes (base items)"""
        all_ingredient_items = set()
        for item, recipes in self.recipe_graph.items():
            for recipe in recipes:
                for ingredient, count in recipe["ingredients"]:
                    all_ingredient_items.add(ingredient)

        self.base_items = all_ingredient_items - set(self.recipe_graph.keys())
        return self.base_items

    def set_base_values(self, base_values):
        """Set values for base items"""
        for item, value in base_values.items():
            self.item_values[item] = value

    def calculate_all_values(self):
        """Calculate values for all craftable items using topological sort"""
        in_degree = defaultdict(int)

        for item in self.recipe_graph.keys():
            for dep in self.dependencies[item]:
                if dep in self.recipe_graph:
                    in_degree[item] += 1

        queue = deque()
        for item in self.recipe_graph.keys():
            deps_in_graph = [
                d for d in self.dependencies[item] if d in self.recipe_graph
            ]
            if not deps_in_graph:
                queue.append(item)

        processed = set()

        while queue:
            item = queue.popleft()
            if item in processed:
                continue

            min_cost = float("inf")

            for recipe in self.recipe_graph[item]:
                recipe_cost = 0
                can_calculate = True

                for ingredient, count in recipe["ingredients"]:
                    if ingredient in self.item_values:
                        recipe_cost += self.item_values[ingredient] * count
                    else:
                        can_calculate = False
                        break

                if can_calculate:
                    per_item_cost = recipe_cost / recipe["result_count"]
                    min_cost = min(min_cost, per_item_cost)

            if min_cost != float("inf"):
                self.item_values[item] = min_cost
                processed.add(item)

                for other_item in self.recipe_graph.keys():
                    if (
                        item in self.dependencies[other_item]
                        and other_item not in processed
                    ):
                        can_process = all(
                            dep in self.item_values
                            for dep in self.dependencies[other_item]
                        )
                        if can_process and other_item not in queue:
                            queue.append(other_item)

    def multiply_all_values(self, multiplier):
        """Multiply all values by a factor"""
        for item in self.item_values:
            self.item_values[item] *= multiplier

    def adjust_values(self, adjustments):
        """Override specific item values"""
        for item, value in adjustments.items():
            self.item_values[item] = value

    def export_json(self, filename="item_values.json"):
        """Export to JSON format"""
        data = {
            "base_items": sorted(list(self.base_items)),
            "item_values": {
                k: round(v, 2) for k, v in sorted(self.item_values.items())
            },
            "statistics": {
                "total_recipes": len(self.recipes),
                "total_items": len(self.recipe_graph),
                "base_items_count": len(self.base_items),
                "valued_items_count": len(self.item_values),
            },
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filename

    def export_csv(self, filename="item_values.csv"):
        """Export to CSV format"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Item,Value,Type\n")

            for item in sorted(self.base_items):
                value = self.item_values.get(item, 1)
                f.write(f"{item},{value:.2f},base\n")

            for item, value in sorted(self.item_values.items()):
                if item not in self.base_items:
                    f.write(f"{item},{value:.2f},crafted\n")

        return filename

    def get_default_base_values(self):
        """Get recommended default values for common base items"""
        defaults = {item: 1 for item in self.base_items}

        # Common valuable items (works across versions)
        value_map = {
            "diamond": 100,
            "emerald": 80,
            "netherite_scrap": 200,
            "ancient_debris": 250,
            "iron_ore": 10,
            "gold_ore": 15,
            "copper_ore": 5,
            "coal": 2,
            "lapis_lazuli": 8,
            "redstone": 5,
            "quartz": 3,
            "deepslate_iron_ore": 12,
            "deepslate_gold_ore": 18,
            "deepslate_copper_ore": 6,
            "deepslate_diamond_ore": 110,
            "deepslate_emerald_ore": 90,
            "raw_iron": 8,
            "raw_gold": 12,
            "raw_copper": 4,
            "cobblestone": 0.5,
            "dirt": 0.1,
            "sand": 0.5,
            "gravel": 0.5,
            "netherrack": 1,
            "end_stone": 2,
            "obsidian": 5,
            "blaze_rod": 20,
            "ender_pearl": 15,
            "ghast_tear": 25,
            "bone": 2,
            "string": 2,
            "gunpowder": 5,
            "slime_ball": 8,
            "leather": 4,
            "wool": 2,
            "feather": 1,
            "echo_shard": 100,
            "heart_of_the_sea": 150,
            "nether_star": 500,
            "dragon_egg": 1000,
            "elytra": 300,
            "totem_of_undying": 200,
            # Material tags
            "iron_tool_materials": 10,
            "gold_tool_materials": 15,
            "diamond_tool_materials": 100,
            "stone_tool_materials": 0.5,
            "wooden_tool_materials": 0.25,
            "copper_tool_materials": 5,
            "netherite_tool_materials": 400,
        }

        for item, value in value_map.items():
            if item in defaults:
                defaults[item] = value

        return defaults


def interactive_mode():
    """Interactive CLI for customizing values"""
    print("=" * 70)
    print("MINECRAFT ITEM VALUATION SYSTEM")
    print("=" * 70)

    # Initialize
    valuer = MinecraftItemValuer()
    print(f"\n✓ Loaded {len(valuer.recipes)} recipes")

    base_items = valuer.identify_base_items()
    print(f"✓ Identified {len(base_items)} base items")

    # Get base values
    print("\n" + "=" * 70)
    print("BASE ITEM VALUES")
    print("=" * 70)
    print("1. Use default values (recommended)")
    print("2. Set all base items to custom value")
    print("3. Customize specific items")

    choice = input("\nChoice (1-3, default=1): ").strip() or "1"

    if choice == "1":
        base_values = valuer.get_default_base_values()
        print("✓ Using default values")
    elif choice == "2":
        value = float(input("Set all base items to: "))
        base_values = {item: value for item in base_items}
        print(f"✓ All base items set to {value}")
    else:
        base_values = valuer.get_default_base_values()
        print("\nEnter items to customize (format: item=value, blank to finish):")
        while True:
            entry = input("> ").strip()
            if not entry:
                break
            try:
                item, value = entry.split("=")
                base_values[item.strip()] = float(value.strip())
                print(f"  ✓ {item.strip()} = {value.strip()}")
            except:
                print("  ❌ Invalid format, use: item_name=value")

    valuer.set_base_values(base_values)

    # Calculate
    print("\n" + "=" * 70)
    print("CALCULATING VALUES...")
    print("=" * 70)
    valuer.calculate_all_values()
    print(f"✓ Calculated values for {len(valuer.item_values)} items")

    # Multiplier
    mult = input("\nMultiply all values by (default=1.0): ").strip()
    if mult and mult != "1" and mult != "1.0":
        multiplier = float(mult)
        valuer.multiply_all_values(multiplier)
        print(f"✓ All values multiplied by {multiplier}")

    # Adjustments
    print("\nOverride specific items? (format: item=value, blank to skip):")
    adjustments = {}
    while True:
        entry = input("> ").strip()
        if not entry:
            break
        try:
            item, value = entry.split("=")
            adjustments[item.strip()] = float(value.strip())
            print(f"  ✓ {item.strip()} = {value.strip()}")
        except:
            print("  ❌ Invalid format")

    if adjustments:
        valuer.adjust_values(adjustments)
        print(f"✓ Adjusted {len(adjustments)} items")

    # Export
    print("\n" + "=" * 70)
    print("EXPORTING...")
    print("=" * 70)
    json_file = valuer.export_json()
    csv_file = valuer.export_csv()
    print(f"✓ Exported to {json_file}")
    print(f"✓ Exported to {csv_file}")

    # Stats
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    values = list(valuer.item_values.values())
    print(f"Total recipes: {len(valuer.recipes)}")
    print(f"Base items: {len(base_items)}")
    print(f"Valued items: {len(valuer.item_values)}")
    print(f"Min value: {min(values):.2f}")
    print(f"Max value: {max(values):.2f}")
    print(f"Average: {sum(values)/len(values):.2f}")

    print("\n" + "=" * 70)
    print("✓ DONE!")
    print("=" * 70)


def explore_mode(data_file="item_values.json"):
    """Interactive exploration mode"""
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"\n❌ Error: {data_file} not found!")
        print("Run 'python main.py --auto' first to generate values.")
        return

    def search_items(search_term):
        """Search for items containing the search term."""
        search_term = search_term.lower()
        results = []
        for item, value in data["item_values"].items():
            if search_term in item.lower():
                item_type = "base" if item in data["base_items"] else "crafted"
                results.append((item, value, item_type))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def get_most_expensive(n=20):
        """Get the N most expensive items."""
        items = [(item, value) for item, value in data["item_values"].items()]
        return sorted(items, key=lambda x: x[1], reverse=True)[:n]

    def get_cheapest(n=20):
        """Get the N cheapest items."""
        items = [(item, value) for item, value in data["item_values"].items()]
        return sorted(items, key=lambda x: x[1])[:n]

    def compare_items(item1, item2):
        """Compare two items."""
        print(f"\n{'='*60}")
        print(f"COMPARISON: {item1} vs {item2}")
        print(f"{'='*60}")

        if item1 in data["item_values"] and item2 in data["item_values"]:
            val1 = data["item_values"][item1]
            val2 = data["item_values"][item2]
            type1 = "base" if item1 in data["base_items"] else "crafted"
            type2 = "base" if item2 in data["base_items"] else "crafted"

            print(f"{item1:30} {val1:>10.2f} ({type1})")
            print(f"{item2:30} {val2:>10.2f} ({type2})")
            print(f"\nDifference: {abs(val1 - val2):.2f}")

            if val1 > val2:
                print(f"{item1} is {val1/val2:.2f}x more valuable")
            else:
                print(f"{item2} is {val2/val1:.2f}x more valuable")
        else:
            if item1 not in data["item_values"]:
                print(f"❌ {item1} not found in valued items")
            if item2 not in data["item_values"]:
                print(f"❌ {item2} not found in valued items")

    def get_items_by_category():
        """Categorize items by type."""
        categories = defaultdict(list)
        for item, value in data["item_values"].items():
            if any(
                tool in item
                for tool in ["pickaxe", "axe", "shovel", "hoe", "sword", "spear"]
            ):
                categories["Tools & Weapons"].append((item, value))
            elif any(
                armor in item
                for armor in ["helmet", "chestplate", "leggings", "boots", "armor"]
            ):
                categories["Armor"].append((item, value))
            elif any(
                block in item
                for block in ["planks", "log", "wood", "stone", "brick", "block"]
            ):
                categories["Building Blocks"].append((item, value))
            elif any(
                x in item
                for x in ["door", "trapdoor", "fence", "gate", "stairs", "slab"]
            ):
                categories["Decorative/Building"].append((item, value))
            elif any(x in item for x in ["dye", "banner", "carpet", "wool", "stained"]):
                categories["Decorative/Dyes"].append((item, value))
            elif any(
                x in item
                for x in [
                    "rail",
                    "minecart",
                    "boat",
                    "piston",
                    "redstone",
                    "repeater",
                    "comparator",
                ]
            ):
                categories["Redstone/Transport"].append((item, value))
            elif any(x in item for x in ["ingot", "nugget", "ore", "raw", "scrap"]):
                categories["Materials"].append((item, value))
            else:
                categories["Other"].append((item, value))
        for category in categories:
            categories[category].sort(key=lambda x: x[1], reverse=True)
        return dict(categories)

    def show_recipe_breakdown(item_name):
        """Show the recipe breakdown for an item."""
        valuer = MinecraftItemValuer("_all.json")
        base_items = valuer.identify_base_items()

        base_values = {item: 1 for item in base_items}
        for item, value in data["item_values"].items():
            if item in base_items:
                base_values[item] = value

        valuer.set_base_values(base_values)
        valuer.calculate_all_values()

        if item_name not in valuer.recipe_graph:
            print(f"❌ {item_name} has no recipe (it's a base item or not found)")
            return

        print(f"\n{'='*70}")
        print(f"RECIPE BREAKDOWN: {item_name}")
        print(f"{'='*70}")

        recipes = valuer.recipe_graph[item_name]
        for i, recipe in enumerate(recipes, 1):
            print(f"\nRecipe {i}: {recipe['recipe_name']}")
            print(f"Produces: {recipe['result_count']} {item_name}")
            print(f"\nIngredients:")

            total_cost = 0
            for ingredient, count in recipe["ingredients"]:
                ing_value = valuer.item_values.get(ingredient, 0)
                cost = ing_value * count
                total_cost += cost
                print(f"  - {count}x {ingredient:30} @ {ing_value:.2f} = {cost:.2f}")

            per_item = total_cost / recipe["result_count"]
            print(f"\nTotal cost: {total_cost:.2f}")
            print(f"Cost per item: {per_item:.2f}")

    # Main explore loop
    while True:
        print("\n" + "=" * 70)
        print("MINECRAFT ITEM VALUATION EXPLORER")
        print("=" * 70)
        print("1. Search for items")
        print("2. Show most expensive items")
        print("3. Show cheapest items")
        print("4. Compare two items")
        print("5. Show items by category")
        print("6. Show recipe breakdown")
        print("7. Show statistics")
        print("0. Exit")
        print("=" * 70)

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            term = input("Search for: ").strip()
            results = search_items(term)
            if results:
                print(f"\nFound {len(results)} items matching '{term}':")
                print(f"{'Item':<40} {'Value':>10} {'Type':<10}")
                print("-" * 62)
                for item, value, item_type in results[:30]:
                    print(f"{item:<40} {value:>10.2f} {item_type:<10}")
                if len(results) > 30:
                    print(f"\n... and {len(results) - 30} more items")
            else:
                print(f"No items found matching '{term}'")

        elif choice == "2":
            n = int(input("How many items? (default 20): ") or "20")
            items = get_most_expensive(n)
            print(f"\nTop {n} most expensive items:")
            print(f"{'Item':<40} {'Value':>10}")
            print("-" * 52)
            for item, value in items:
                print(f"{item:<40} {value:>10.2f}")

        elif choice == "3":
            n = int(input("How many items? (default 20): ") or "20")
            items = get_cheapest(n)
            print(f"\nTop {n} cheapest items:")
            print(f"{'Item':<40} {'Value':>10}")
            print("-" * 52)
            for item, value in items:
                print(f"{item:<40} {value:>10.2f}")

        elif choice == "4":
            item1 = input("First item: ").strip()
            item2 = input("Second item: ").strip()
            compare_items(item1, item2)

        elif choice == "5":
            categories = get_items_by_category()
            print("\nCategories:")
            for i, category in enumerate(sorted(categories.keys()), 1):
                print(f"{i}. {category} ({len(categories[category])} items)")

            cat_choice = int(input("\nSelect category (number): ")) - 1
            cat_name = sorted(categories.keys())[cat_choice]

            print(f"\n{cat_name}:")
            print(f"{'Item':<40} {'Value':>10}")
            print("-" * 52)

            for item, value in categories[cat_name][:30]:
                print(f"{item:<40} {value:>10.2f}")

            if len(categories[cat_name]) > 30:
                print(f"\n... and {len(categories[cat_name]) - 30} more items")

        elif choice == "6":
            item = input("Item name: ").strip()
            show_recipe_breakdown(item)

        elif choice == "7":
            print("\n" + "=" * 70)
            print("STATISTICS")
            print("=" * 70)
            print(f"Total base items: {len(data['base_items'])}")
            print(f"Total valued items: {len(data['item_values'])}")

            values = list(data["item_values"].values())
            if values:
                print(f"\nValue statistics:")
                print(f"  Minimum: {min(values):.2f}")
                print(f"  Maximum: {max(values):.2f}")
                print(f"  Average: {sum(values)/len(values):.2f}")
                print(f"  Median: {sorted(values)[len(values)//2]:.2f}")

            ranges = [
                (0, 1),
                (1, 10),
                (10, 50),
                (50, 100),
                (100, 500),
                (500, float("inf")),
            ]
            print(f"\nValue distribution:")
            for low, high in ranges:
                count = sum(1 for v in values if low <= v < high)
                print(f"  {low}-{high if high != float('inf') else '∞'}: {count} items")

        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice!")


def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Item Valuation System - Works with any version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Interactive mode
  python main.py --explore                    # Explore existing values
  python main.py --auto                       # Auto-calculate with defaults
  python main.py --multiply 2.5               # Make everything 2.5x more expensive
  python main.py --set diamond=500 iron=20    # Set specific base values
  python main.py --adjust diamond_sword=1000  # Override calculated values
  python main.py --all-base=10                # Set all base items to 10
  python main.py --output my_values           # Custom output name (creates .json and .csv)
        """,
    )

    parser.add_argument(
        "--auto", action="store_true", help="Auto-calculate with default values"
    )
    parser.add_argument(
        "--explore", action="store_true", help="Explore existing calculated values"
    )
    parser.add_argument(
        "--multiply", type=float, help="Multiply all values by this factor"
    )
    parser.add_argument(
        "--set", nargs="+", help="Set base item values (format: item=value)"
    )
    parser.add_argument(
        "--adjust",
        nargs="+",
        help="Override calculated item values (format: item=value)",
    )
    parser.add_argument(
        "--all-base", type=float, help="Set all base items to this value"
    )
    parser.add_argument(
        "--output",
        default="item_values",
        help="Output filename prefix (default: item_values)",
    )
    parser.add_argument(
        "--recipes", default="_all.json", help="Recipe JSON file (default: _all.json)"
    )

    args = parser.parse_args()

    # Explore mode
    if args.explore:
        explore_mode()
        return

    # Interactive mode if no flags
    if not args.auto and not args.set and not args.adjust and not args.all_base:
        interactive_mode()
        return

    # Command-line mode
    print("=" * 70)
    print("MINECRAFT ITEM VALUATION SYSTEM - AUTO MODE")
    print("=" * 70)

    valuer = MinecraftItemValuer(args.recipes)
    print(f"\n✓ Loaded {len(valuer.recipes)} recipes")

    base_items = valuer.identify_base_items()
    print(f"✓ Identified {len(base_items)} base items")

    # Set base values
    if args.all_base:
        base_values = {item: args.all_base for item in base_items}
        print(f"✓ Set all base items to {args.all_base}")
    else:
        base_values = valuer.get_default_base_values()
        print("✓ Using default base values")

    if args.set:
        for entry in args.set:
            try:
                item, value = entry.split("=")
                base_values[item] = float(value)
                print(f"✓ Set {item} = {value}")
            except:
                print(f"❌ Invalid format: {entry}")

    valuer.set_base_values(base_values)

    # Calculate
    print("\n✓ Calculating values...")
    valuer.calculate_all_values()
    print(f"✓ Calculated {len(valuer.item_values)} items")

    # Multiply
    if args.multiply:
        valuer.multiply_all_values(args.multiply)
        print(f"✓ Multiplied all values by {args.multiply}")

    # Adjust
    if args.adjust:
        adjustments = {}
        for entry in args.adjust:
            try:
                item, value = entry.split("=")
                adjustments[item] = float(value)
            except:
                print(f"❌ Invalid format: {entry}")
        if adjustments:
            valuer.adjust_values(adjustments)
            print(f"✓ Adjusted {len(adjustments)} items")

    # Export
    json_file = valuer.export_json(f"{args.output}.json")
    csv_file = valuer.export_csv(f"{args.output}.csv")
    print(f"\n✓ Exported to {json_file}")
    print(f"✓ Exported to {csv_file}")

    print("\n" + "=" * 70)
    print("✓ DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
