## Why I wrote a tool for Kicad Database Library

If you've ever designed a PCB with a team using OrCAD, you've likely used **CIS** (Component Information System) and **CIP** (Component Information Portal). These tools integrate a centralized component database that stores manufacturer part numbers, distributor SKUs, parametric data, and datasheet URLs in one place. **CIS** is critical because it eliminates duplicate data entry and prevents the use of obsolete or unauthorized parts during schematic design. **CIP** is equally essential—it streamlines part request and approval workflows, ensuring that only verified components enter the database. Together, they reduce BOM errors, shorten design cycles, and enforce design consistency across teams, making them indispensable for professional PCB development.

KiCad has included a database library feature since version 7, allowing designers to link symbols and footprints to external data sources like SQLite, MySQL, or PostgreSQL via ODBC connections. However, unlike OrCAD CIS/CIP, KiCad's implementation remains largely manual and lacks a built-in GUI for database management. Users must manually input every component's parameters (part numbers, values, tolerances, datasheet links, etc.) directly into the database using external tools — there is no form-based entry or validation within KiCad itself. Creating a usable component database currently requires manual SQL scripting or third-party database clients (such as SQLiteStudio) — a steep barrier for engineers without database experience.

So I wrote a python script to bring CIS/CIP workflow to Kicad. 

## The Tool: `kicad-lib-gen`

This command-line python script [`kicad-lib-gen`](https://github.com/last-sociable-orange/kicad_lib_gen) brings the CIS/CIP workflow to KiCad. It connects to the **Digikey API**, fetches real-time product data, and stores it directly into a SQLite database that KiCad's symbol and footprint choosers can read natively.

Here's what it does:

- **Search Digikey** by manufacturer part number and pull down descriptions, parameters, pricing, datasheet URLs, and availability
- **Store everything** into a SQLite database with the exact schema KiCad expects
- **Link components** to KiCad symbols and footprints (with tab-completion for existing entries)
- **Batch import** hundreds of parts from a CSV file
- **Auto-refresh** Digikey OAuth tokens so you don't have to babysit authentication

## How It Works

### 1. Authentication

You start by registering a free developer account at [Digikey's Developer Portal](https://developer.digikey.com/). Create an application, get your Client ID and Client Secret, then run:

```bash
uv run digikey_auth.py --user YOUR_CLIENT_ID --secret YOUR_CLIENT_SECRET
```

This kicks off the OAuth2 flow. You paste a URL into your browser, authorize the app, and paste the redirect URL back. The tool saves your tokens to a `.token` file with automatic refresh — you won't need to re-authenticate for months.

### 2. Database Setup

The tool creates a `components.db` SQLite file with the schema KiCad expects. Each record stores:

- Manufacturer and manufacturer product number
- Description, keywords, and category tree
- Package type and parametric data (up to 32 parameters)
- Datasheet URL and product URL
- Distributor info (Digikey product number, pricing, quantity available)
- **KiCad symbol library** and **footprint library** links

The database can live in your project's `Library/` folder, and you configure KiCad to use it via a `.kicad_dbl` ODBC configuration file.

### 3. Interactive Mode: Adding Components One at a Time

The most common workflow is searching for a part and adding it:

```bash
uv run kicad_cip.py -k "LM324N"
```

The tool searches Digikey, shows you the results, and lets you pick:

```
Total 5 products found:
  [1]: LM324N, Texas Instruments, IC OPAMP GP 4 CIRCUIT 14DIP, Qty: 2500, Active
  [2]: LM324NE4, Texas Instruments, IC OPAMP GP 4 CIRCUIT 14DIP, Qty: 1800, Active
  [3]: LM324NP, Texas Instruments, IC OPAMP GP 4 CIRCUIT 14DIP, Qty: 0, Obsolete
  ...
Choose one product, 0 to exit: 1
```

After selecting the part, it prompts you for the KiCad symbol and footprint, with **auto-completion** of existing libraries in your database. These names will link to the component `.kicad_sym` and `.kicad_mod` files in your local project folder.

```
Enter Kicad symbol library name: Symbol:IC_LM324N
Enter Kicad footprint library name: Footprint:IC_LM324N
```

A neat trick: you can use `?` as a placeholder for the product number:

```
Enter Kicad symbol library name: Symbol:IC_?      -> becomes Symbol:IC_LM324N
Enter Kicad footprint library name: Footprint:IC_?   -> becomes Footprint:IC_LM324N
```

This is a huge time-saver when you're importing dozens of parts.

### 4. Batch Mode: Importing from CSV

For setting up a whole BOM at once, batch mode is where the tool really shines:

```bash
uv run kicad_cip.py -b parts.csv
```

Your CSV file looks like this:

```csv
manufacturer_product_number,kicad_symbol_library,kicad_footprint_library
LM324N,Symbol:IC_LM324N,Footprint:IC_LM324N
ATMega328P,Symbol:IC_ATMega328PB-MU,Footprint:IC_ATMega328PB-MU
STM32F103C8T6,Symbol:IC_STM32F103C8T6,Footprint:IC_STM32F103C8T6
```

The tool iterates each row, searches Digikey for an exact match, and auto-inserts the record with the specified symbol and footprint. It's strict — if a search returns zero or multiple results, it fails fast rather than silently picking the wrong part. Log file is provided so that you are fully aware which components are inserted and which are dropped with reasons. 

### 5. Symbol and Footprint Organization

The tool works with a **carefully organized library structure** that keeps projects maintainable at scale:

```
Library/
├── components.db                     # SQLite database
├── components_db.kicad_dbl           # KiCad ODBC config
├── Symbol/
│   ├── Symbol           			  # Per-part symbols
│   │	├── IC_LM324N.kicad_sym       
│   │	└── IC_ATMega328PB-MU.kicad_sym
│   └── Standard           			  # Standard symbols
│   	└── Standard.kicad_sym
├── Footprint/
│   ├── Footprint.pretty/
│   │   ├── IC_LM324N.pretty     	  # Per-part footprints
│   │   └── IC_ATMega328PB-MU.pretty
│   └── Standard.pretty/			  # Standard footprints
│       ├── R_0402.pretty
│       └── SOT23.pretty
└── Step/                              # 3D models
    ├── IC_LM324N.stp
    └── IC_ATMega328PB-MU.stp
```

The key insight: **generic components** (resistors, capacitors, standard logic) use shared symbols in `Standard.kicad_sym`, while **specific ICs, passives, connectors, etc.** each get their own file. This gives you the best of both worlds — reuse for common parts, isolation for complex ones.

## Connecting It to KiCad

Once your database is populated, you configure KiCad to use it. Make sure the way how you setup your Kicad libraries matches what you have entered in your database  `KicadSymbolLibrary` and `KicadFootprintLibrary` fields using the command line prompt.

1. Install SQLite database driver, setup DSN, etc.
2. Place `components_db.kicad_dbl` in your project `Library` folder
3. In KiCad, open the **Manage Symbol Libraries** menu and add your database library file (`.kicad_dbl`) to `Project Specific Libraries`. 
4. Link to your per-part symbols. You have two options to add files to `Project Specific Libraries`:
   + Add each individual files : If you add per-part symbols (i.e.: IC_LM324N.kicad_sym that contains only one symbol named IC_LM324N) in your `Project Specific Libraries`, you have to input `IC_LM324N:IC_LM324N` when you are prompted to enter the Kicad symbol library name. Basically with this scheme, the symbol library name should be `<symbol_file_name>:<symbol_name>` .
   + Add entire folder (Kicad 10 new feature): You can add the folder as opposed to symbol files to your `Project Specific Libraries`. With this scheme, the symbol library name should be  `<symbol_folder_name>:<symbol_file_name>`  
5. Add your `Standard.kicad_sym`  as regular kicad symbol
6. Then open the **Manage Footprint Libraries** menu to ensure the footprint library paths referenced in your database are accessible.
7. In KiCad's Symbol Chooser, you'll see components from your database
8. Browse components by category, search by keyword, and place them on your schematic
9. The footprint is automatically associated — KiCad picks it up from the database record

This mirrors the Orcad CIS experience: you browse a database-driven library, place a symbol, and the footprint and metadata follow.

## Getting Started

The tool is live on [GitHub](https://github.com/last-sociable-orange/kicad_lib_gen). Here's the quick start:

```bash
# Install dependencies
uv sync

# Authenticate with Digikey
uv run digikey_auth.py --user YOUR_ID --secret YOUR_SECRET

# Add a single part interactively
uv run kicad_cip.py -k "LM324N"

# Or batch import from CSV
uv run kicad_cip.py -b bom_parts.csv
```

You'll need a free Digikey developer account, but that's it — no server, no cloud dependency, no vendor lock-in. The database is just a SQLite file on your disk.

If you're using KiCad in a team setting and missing the CIS/CIP workflow from Orcad, give this a try. 

## Disclaimer

I am not a software developer. This script is intended for DIYers and hobbyist use only. It is provided as-is, with no guarantees of correctness, data integrity, or compatibility with future KiCad or Digikey API changes. You assume full responsibility for any issues — including corrupted databases, incorrect BOMs, or fried PCBs. Always verify part data against official manufacturer sources before ordering components.

---

*Have questions or ideas? Drop me a note or open an issue on GitHub.*
