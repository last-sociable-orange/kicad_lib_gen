# Kicad CIP workflow

The goal of this work flow is to streamline Kicad database library, symbol and footprint pulled from either Digikey or manufacturer's website, and using Digikey CIP app to fill up component information stored in the database. The CIP app is designed specificlly for pulling component information from Digikey using its web API. It is possbile to pull information from other website but for now we only support Digikey.

#### Create Digikey Developer Account

Register at https://developer.digikey.com/

Create a Organization -> Memeber -> Production Apps

- Callback URL https://localhost:8000/oauth2/callback (has to match the callback URL in python code)
- Copy Client ID and Client Secrete

#### Prepare Python environmnet

- Install `uv`​: [docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- Copy python files into folder
- Run `uv run digikey_auth.py` to get token file from Digikey Dev portal
- Run `uv run kicad_cip.py` to retrieve component information from Digikey and store it into Sqlite database

#### Create Kicad Project

- Create Kicad project
- Create `Library`​, `Library/Symbol`​, `Library/Footprint/Footprint.pretty`​, `Library/Step` folders under project folder

```bash
mkdir -p Library
mkdir -p Library/Symbol Library/Footprint/Footprint.pretty Library/Step
```

- Copy `components_db.kicad_dbl`​ under project folder. This is the `ODBC` setup file for the system to interact with the Sqlite database.
- Copy `components.db`​under `Library`if you have an existing database
- Copy python CIP scripts under `Library`​. You can also use it in any other folder and use `-o` option to specify the database file name in the commandline.
- Copy `Standard.kicad_sym`​ to `Library/Symbol`. This is a library that contains standard symbols and Power/GND symbols that can be used across projects. It is recommended to use these standard symbols to keep schematics design consistant across projects but user can also use their own symbols at their own discretion.
- Copy folder `Standard.pretty`​ to `Library/Footprint`​. This folder contains generic footprints like `R_0402`​, `SOT23` that can be used for components that have standard footprints, etc.
- A starter `Standard.kicad_sym`​ and `Library/Sdandard.pretty` will be provided for new project.

#### Prepare symbol, footprint and step files

Symbols and Footprints are organized following below rules:

Symbol high-level rules:

- ​`Standard.kicad_sym`​ contains generic symbols that are vendor agnostic. Field `KicadSymbolLibrary`​ in Sqlite database maps to the symbol names in `Standard.kicad_sym`​. To link them together, one must enter `Standard:<symbol_name>`​correctly when creating a component instance in the component information database. For example: A resistor's symbol name in database would be: `Standard:R`​ when entering the resistor's `KicadSymbolLibrary` field.
- No standard symbols are stored seperately per component in `Library/Symbol` folder. This makes it easier to manage symbols from project perspective. One can change a symbol and manage revision using git or other revision control tools without affecting other symbols. Naming convetions are covered below.

Footprint high-level rules:

- Footprints are stored seperately per component (or per footprint for generic footprints) in `Standard.pretty`​ or `Footprint.pretty` folders respectively

Symbol and Footprint Workflow:

- Use standard symbols/footprint if they are available in `Standard.kicad_sym`​ and `Standard.pretty`
- Download symbol and footprint (and step file) from Digikey/Mouser/Ultralibrarian/SanpEDA
- **Important!** ​ **Check symbol and footprint integrity and correctness against datasheet.**
- Create symbol and footprint if they are not available
- Copy symbol, footprint and step files to `Library/Symbol`​, `Library/Footprint/Footprint.pretty`​ and `Library/Step` folders respectively
- Rename symbol/footprint/step files following below rules:

  - [component_type]_[component_product_number]
  - component_type is one of the followings, or best fit:

    - IC, for integrated circuit chips
    - DIO, for diodes, including schottky, tvs
    - IND, for inductors, coils, chocks, ferrite beads
    - TRANS, for transistors, including BJTs, FETs
    - CON, for connectors
    - SW, for switches
    - ...
  - component_product_number is the full part number including package suffix
  - All chars are capital letters
- **Symbol extra steps**:

  - Open symbol with Kicad Symbol Editor, edit/delete unneccessary fields to avoid them polluting the database information. Only leave Kicad default fields.
  - Save symbol in the same name as the file name. The purpose of this step is to match the database information entered in CIS app
- **Footprint extra steps**:

  - Make sure Reference field is **REF****
  - Make sure Value field visibility is **Unchecked**
  - Add Text in F.Fab layer with value ${REFERENCE}. This is used as Reference Designator in Assembly Drawing
- **Step file extra steps**:

  - Renanme *.stp file to *.step
  - Recommend using environment variables to define the step file path when doing the step file mapping in Footprint Editor
    - Step file path example = ${KIPRJMOD}/../Library/your_step_file.step

#### Add component information into database

There are two ways to add components into database:

**Interactive mode (single component):**
```bash
uv run kicad_cip.py -k "keywords"
```
- Prompts you to select one product from search results
- Prompts you to enter KiCad symbol and footprint library names
- Supports auto-completion of existing library entries
- Use `?` as a placeholder in the symbol/footprint name to automatically insert the product number. For example:
  - `Standard:?` becomes `Standard:LM324N` if the product number is `LM324N`
  - `MyFootprint:?_Rev1` becomes `MyFootprint:LM324N_Rev1`

**Batch mode (multiple components):**
```bash
uv run kicad_cip.py -b parts.csv
```

The CSV file must have:
- A header line with exactly 3 columns: `manufacturer_product_number`, `kicad_symbol_library`, `kicad_footprint_library`
- One component per data row
- All three fields must be provided

Example `parts.csv`:
```csv
manufacturer_product_number,kicad_symbol_library,kicad_footprint_library
LM324N,Standard:LM324,Standard:LM324_SOIC-14
ATMega328P,Standard:ATMega328P,Standard:ATMega328P_DIP-28
```

Batch mode behavior:
- Automatically searches for the manufacturer product number on Digikey
- If exactly 1 result found: auto-selects and proceeds without prompts
- If 0 results: exits with error "Searching {product} returns no results. --batch mode failed."
- If multiple results: exits with error "Searching {product} returns multiple results. --batch mode failed."
- Symbol and footprint values from CSV are used directly (no interactive prompts)

**Note:** If you only provide the product number without symbol/footprint in the CSV (single column format or empty fields), the tool falls back to interactive mode where you manually select the product and enter symbol/footprint names.

**Authentication:**
- Before first use, run `uv run digikey_auth.py` to obtain a Digikey access token saved to `.token` file
- The `.token` file must exist in the current directory. If missing, the tool will raise an error.

‍
