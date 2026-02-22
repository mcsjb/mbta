# Tech Screen: MBTA subway questions

## Requirements

- Python 3.10+
- MBTA API Key (free from https://api-v3.mbta.com/)

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:


2. Add your MBTA API key to the `.env` file:
```
MBTA_API_KEY=your_api_key_here
```

You can obtain a free API key from: https://api-v3.mbta.com/

## Project Goal:
 * The goal of this project is use the MBTA API to answer a set of questions about the subway lines. 
#### Question 1:
 * What are the long names of all the subway routes in the MBTA.  Subway routes are defined as those with a type of 0 or 1
#### Question 2:
 * What is the subway route with the most stops?  How many stops does it have?
 * What is the subway route with the fewest stops?  How many stops does it have?
 * List the stops that connect two or more subway routes along with the relevant route names for each stop.
#### Question 3:
Allow the user to provide any two stops on the subway lines from question 1, return the route the user could take from the start stop to the end stop.

* see **service_notes.md** for implementation notes on questions.

## Usage
### make tech-screen

Use the makefile to run the script to answer the three tech screen questions.
Give START="Station Name" and STOP="Station Name" as inputs for question 3

```bash
make tech-screen START='Kenmore' STOP='State'
```

Or use the command directly:

```bash
cd main
python main.py --start "Downtown Crossing" --stop "Alewife"
```

### Example invocations

```bash
# Red Line trip
make tech-screen START='Ashmont' STOP='Alewife'

# Green Line trip
make tech-screen START='Park Street' STOP='Arlington'

# Cross-line trip
make tech-screen START='Kenmore' STOP='State'
```

## Project Structure

```
mbta/
├── main/
│   ├── mbta_client/          # MBTA API client
│   │   ├── client.py         # HTTP client for MBTA API
│   │   ├── config.py         # Url and API key for MBTA
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── models.py         # API response models - pydantic models
│   ├── models/               # Domain models
│   │   └── subway_models.py  # Custom MBTA data structures
│   ├── repositories/         # Data access layer
│   │   └── subway_repository.py  # MBTA CLIENT repository
│   ├── main.py              # Application entry point
│   └── services.py          # Business logic
├── tests/                   # Test suite
│   └── unit/                # Unit tests
├── .env                     # Environment variables (not in git)
├── makefile                 # Make commands
├── pyproject.toml           # Pytest configuration
└── requirements.txt         # Python dependencies
```

## Development

### Running Tests

Run all unit tests:
```
make test
```

### Code Formatting

This project uses Black for code formatting:
```
make black
```
