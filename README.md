# Minecraft Item Valuation System

A universal Python tool that calculates item values based on crafting recipes. Works with **any Minecraft version** - just provide the `_all.json` recipe file.

## Getting Recipe Files

You need the `_all.json` recipe file for your Minecraft version to use this tool.

**Download recipes for all Minecraft versions:**  
🔗 https://github.com/InventivetalentDev/minecraft-assets

1. Navigate to the version you want (e.g., `1.21.4/`)
2. Go to `data/minecraft/recipe/`
3. Download the `_all.json` file
4. Place it in the same folder as `main.py`

**That's it!** The code only needs the `_all.json` file to work.

## Quick Start

### Interactive Mode (Recommended)

```bash
python main.py
```

Follow the prompts to customize values and generate results.

### Auto Mode with Defaults

```bash
python main.py --auto
```

Instantly generates `item_values.json` and `item_values.csv` using default values.

### Explore Existing Values

```bash
python main.py --explore
```

Interactive browser to search, compare, and analyze calculated values.

## Command-Line Options

### Basic Usage

```bash
# Auto-calculate with default values
python main.py --auto

# Explore existing calculated values
python main.py --explore

# Set all base items to a specific value
python main.py --all-base 10

# Make everything 2x more expensive
python main.py --auto --multiply 2.0

# Use custom output name
python main.py --auto --output my_prices
```

### Setting Base Item Values

Base items are materials that don't have recipes (ores, mob drops, etc.)

```bash
# Set specific items
python main.py --set diamond=500 iron_ore=20 coal=5

# Combine with auto mode
python main.py --auto --set diamond=500 emerald=400

# Set all base items to same value
python main.py --all-base 1
```

### Adjusting Calculated Values

Override specific item values after calculation:

```bash
# Override specific items
python main.py --auto --adjust diamond_sword=1000 iron_pickaxe=100

# Combine multiple adjustments
python main.py --auto --adjust diamond_sword=1000 diamond_pickaxe=1500
```

### Advanced Combinations

```bash
# Set base values, calculate, then multiply everything
python main.py --set diamond=100 iron_ore=10 --multiply 1.5

# Full custom workflow
python main.py --set diamond=200 emerald=150 \
               --multiply 2.0 \
               --adjust diamond_sword=2000 \
               --output expensive_mode

# Economy rebalance
python main.py --all-base 5 --multiply 0.5 --output balanced
```

## How It Works

### 1. Base Items

Items without recipes (must be manually valued):

- Ores: diamond, iron, gold, coal, etc.
- Natural blocks: dirt, stone, sand, gravel
- Mob drops: bone, string, ender pearl
- Plants: wheat, carrot, flowers

**Default base value: 1** (unless specified)

### 2. Craftable Items

Items with recipes (automatically calculated):

```
diamond_sword = (2 × diamond_value) + (1 × stick_value)
              = (2 × 100) + (1 × 0.5)
              = 200.5
```

### 3. Multiple Recipes

If an item has multiple recipes, the **cheapest** one is used automatically.

## Output Files

### JSON Format (`item_values.json`)

```json
{
  "base_items": ["diamond", "iron_ore", ...],
  "item_values": {
    "diamond": 100,
    "diamond_sword": 200.5,
    "iron_pickaxe": 31.0
  },
  "statistics": {
    "total_recipes": 1470,
    "base_items_count": 207,
    "valued_items_count": 844
  }
}
```

### CSV Format (`item_values.csv`)

```
Item,Value,Type
diamond,100.00,base
iron_ore,10.00,base
diamond_sword,200.50,crafted
iron_pickaxe,31.00,crafted
```

## Default Values

Recommended defaults for common items:

| Category        | Examples                        | Default Value |
| --------------- | ------------------------------- | ------------- |
| **Precious**    | diamond, emerald                | 100, 80       |
| **Common Ores** | iron, gold, copper              | 10, 15, 5     |
| **Fuels**       | coal, charcoal                  | 2             |
| **Building**    | cobblestone, dirt               | 0.5, 0.1      |
| **Rare**        | netherite_scrap, ancient_debris | 200, 250      |
| **Legendary**   | dragon_egg, nether_star         | 1000, 500     |

## Recipe Types Supported

✅ Shaped Crafting  
✅ Shapeless Crafting  
✅ Smelting / Blasting / Smoking  
✅ Stonecutting  
✅ Smithing Transform  
✅ Campfire Cooking

## Examples

### Example 1: Quick Default Setup

```bash
python main.py --auto
```

Output:

- Uses recommended defaults
- `item_values.json` + `item_values.csv` created
- Diamond sword: 200.50
- Iron pickaxe: 31.00

### Example 2: Custom Base Values

```bash
python main.py --set diamond=500 iron_ore=25 gold_ore=40
```

Now diamond sword = 500 × 2 + 0.5 = 1000.50

### Example 3: Make Everything More Expensive

```bash
python main.py --auto --multiply 3.0
```

Diamond sword: 200.50 × 3 = 601.50

### Example 4: Server Economy

```bash
# Set prices for server shop
python main.py --all-base 10 \
               --set diamond=1000 emerald=800 netherite_scrap=5000 \
               --multiply 0.8 \
               --output server_economy
```

### Example 5: Survival Challenge Mode

```bash
# Make everything expensive
python main.py --all-base 50 --multiply 5.0 --output hardcore
```

## Interactive Mode Details

When you run `python main.py` without flags:

```
1. Choose base value strategy:
   - Use defaults (recommended)
   - Set all to same value
   - Customize specific items

2. Optionally multiply all values

3. Optionally override specific items

4. Exports JSON + CSV automatically
```

## Works With Any Minecraft Version

Just need the recipe JSON file:

```bash
# Minecraft 1.21
python main.py --recipes minecraft_1.21_recipes.json --auto

# Minecraft 1.20
python main.py --recipes minecraft_1.20_recipes.json --auto

# Modded Minecraft
python main.py --recipes modded_recipes.json --auto
```

## Exploring Results

After generating values, use the built-in explorer:

```bash
python main.py --explore
```

Interactive menu to:

- 🔍 Search items by name
- 💎 Show most/least expensive items
- ⚖️ Compare two items side-by-side
- 📂 Browse items by category
- 🔧 View detailed recipe breakdowns
- 📊 Display value statistics and distributions

## Tips & Tricks

### Tip 1: Material Tags

Some recipes use tags like `#minecraft:iron_tool_materials`. These are automatically set to match the ore value:

- `iron_tool_materials` = `iron_ore` value
- `diamond_tool_materials` = `diamond` value
- etc.

### Tip 2: Finding Base Items

Base items are shown in the JSON output under `"base_items"`. You can customize any of them.

### Tip 3: Balancing Economy

Start with defaults, then adjust based on:

- Rarity (how hard to find)
- Utility (how useful in gameplay)
- Effort (time to gather)

### Tip 4: Batch Operations

Process multiple versions at once:

```bash
for version in 1.20 1.21; do
    python main.py --recipes minecraft_${version}_recipes.json \
                   --output values_${version} \
                   --auto
done
```

### Tip 5: Quick Tests

```bash
# Test different multipliers
python main.py --auto --multiply 0.5 --output test_cheap
python main.py --auto --multiply 2.0 --output test_expensive
python main.py --auto --multiply 10.0 --output test_hardcore
```

## Troubleshooting

**Q: Some items show very low/high values**  
A: Adjust the base items they depend on. Use `python main.py --explore` (option 6) to check recipe breakdowns.

**Q: "Recipe file not found"**  
A: Make sure `_all.json` is in the same directory, or use `--recipes path/to/file.json`

**Q: Can I edit the JSON and recalculate?**  
A: Yes! Edit `_all.json` to add/modify recipes, then run main.py again.

**Q: How do I reset to defaults?**  
A: Just run `python main.py --auto` again.

## Use Cases

- **Server Economies**: Generate shop prices
- **Modpacks**: Balance custom recipes
- **Game Mods**: Calculate crafting costs
- **Data Analysis**: Study recipe complexity
- **Economy Plugins**: Export prices for plugins

## Technical Details

- **Algorithm**: Topological sort with dependency resolution
- **Time Complexity**: O(n log n) where n = number of items
- **Works with**: Python 3.6+
- **Dependencies**: None (pure Python, standard library only)

## Files

- `main.py` - Complete valuation and exploration tool
- `_all.json` - Your Minecraft recipes
- `item_values.json` - Generated values (JSON)
- `item_values.csv` - Generated values (CSV)

---

**Made for Minecraft item valuation - works with any version!**
