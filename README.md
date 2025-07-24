# MET

![Logo](assets/Logo.svg)

## Description

**MET** is a Graphical User Interface (GUI) designed to easily set up, configure, and generate experiment configuration files in Excel for molecular optimization workflows. It also allows to upload his own excel files to visualize them from another angle with various graphs.

This GUI is especially useful for chemists, researchers, or data scientists working with Bayesian optimization algorithms. It enables users to define parameters, objectives, and metadata through a friendly UI — avoiding the need to hand-code configuration files.

### Home

- Uplaod your own Excel files
- Select one of them
- Select one page

### Features of dashboard part

- Display the selected Excel page
- Modify it (change cells values, add rows...)
- Save changes

### Features of visualization part

- Automatic grahs when you arrived
- Interactive selection of each column to use

### Features of caracterization part

- TO BE DONE

### Features of optimization part

- Define multiple *parameters* with types (continuous, integer, categorical, ordinal, or chemical).
- Select possible values for all of them (create your experimental landscape)
- Dynamically add *objectives* with "minimize" or "maximize" direction.
- Define *additional metadata columns*.
- Name and generate the final Excel configuration file.

### Background

MET is built to help chemist optimize their reactions by providing a bridge between chemistry knowledge and back-end Bayesian optimization frameworks (in this case it is [entre the name when decided]).

## Badges

<!-- Example Badges -->
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Dash](https://img.shields.io/badge/Dash-2.x-brightgreen)
![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Visuals

<!-- Add demo videos of each part when finished -->
![Parameter Input Demo](path_to_demo_screenshot_or_gif.gif)

## Installation

You can either directly use it at [app link](http://127.0.0.1:8080) or run it locally following these steps:

### Requirements

- Python 3.10+
- `pip` or `conda`

### Setup

1. Clone the repo:

    ```bash
    git clone https://github.com/Mathildec25/dash-chem.git
    cd dash-chem
    ```

2. Create and activate a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the app:

    ```bash
    python app.py
    ```

The app will start and can be accessed at `http://0.0.0.0:8080/`.

## Usage

- **Parameters**: Add as many variables as needed, selecting type (`int`, `float`, `cat`, `ord`, or `chem`).
- **Objectives**: Define one or more target objectives for optimization with their direction (`min` or `max`).
- **Other Columns**: Add additional metadata columns to be included in the Excel output.
- **Excel Export**: Name the Excel file and generate it with a single click.

Example of parameter configuration output:

```json
[
  {
    "name": "Temperature",
    "type": "float",
    "type_info": [20.0, 80.0]
  },
  {
    "name": "Solvent",
    "type": "cat",
    "type_info": ["DMSO", "Water", "Methanol"]
  }
]
