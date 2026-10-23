# 🏥 CareFlow — Clinical Pathway Process Mining

**CareFlow** is a clinical process mining project designed to analyze simulated hospital patient journeys, discover clinical pathways, and identify operational inefficiencies such as repeated triage events.

The project uses Python, Streamlit, Pandas, and PM4Py to transform hospital event logs into meaningful process visualizations and analysis.

## 🎯 Project Objectives

- Simulate hospital patient event logs.
- Explore patient journeys across clinical departments.
- Analyze activity frequencies and patient pathways.
- Discover hospital workflows using process mining.
- Detect repeated triage events and potential rework.
- Visualize process analysis through an interactive dashboard.
- Integrate BigQuery and dbt for data storage and transformation.

## ✨ Features

### 1. Hospital Event Log Generation
- Generate simulated hospital event data.
- Record patient identifiers, event identifiers, activities, timestamps, departments, and resources.
- Represent patient journeys through different hospital activities.

### 2. Interactive Streamlit Dashboard
- View hospital event records in a user-friendly interface.
- Filter events by patient or case.
- Explore clinical activities and timestamps.
- Download displayed event data.

### 3. Process Discovery
- Use PM4Py to discover hospital process flows.
- Generate a process map from event log data.
- Visualize the sequence of activities in patient journeys.

### 4. Triage Rework Detection
- Identify patients with repeated triage events.
- Generate CSV reports containing detected cases.
- Support further investigation of potential rework in clinical workflows.

### 5. Data Analysis
- Analyze activity frequencies.
- Normalize event log fields for process mining.
- Save analysis results and visualizations.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Pandas | Data manipulation and analysis |
| Streamlit | Interactive web dashboard |
| PM4Py | Process mining and process discovery |
| Matplotlib | Data visualization |
| Google BigQuery | Cloud data storage and querying |
| dbt | Data transformation and modeling |
| Git and GitHub | Version control and collaboration |

## 📁 Project Structure

```text
CareFlow/
├── data/
│   └── raw/
│       └── hospital_event_logs.csv
├── process_mining/
│   ├── outputs/
│   │   ├── activity_frequencies.csv
│   │   ├── normalized_event_log.csv
│   │   ├── process_map.png
│   │   ├── triage_rework_cases.csv
│   │   └── triage_rework_patients.csv
│   ├── analysis.py
│   └── triage_rework.py
├── src/
│   └── generate_event_logs.py
├── dbt_careflow/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

*Note: The structure above describes the expected organization. Adjust filenames to match the actual files in your repository.*

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or later
- Visual Studio Code or another Python editor
- Git

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CareFlow
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository's GitHub URL.

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Dashboard

Run the Streamlit application using the actual path of your main application file. If it is `main.py`, use:

```bash
streamlit run main.py
```

If your main file has a different name, replace `main.py` with that filename.

## 📊 Output Files

The process mining analysis can produce:

- `activity_frequencies.csv` — activity frequency statistics.
- `normalized_event_log.csv` — standardized event data.
- `process_map.png` — discovered process visualization.
- `triage_rework_cases.csv` — cases with repeated triage events.
- `triage_rework_patients.csv` — patient-level triage rework results.

Output filenames may vary depending on the current implementation.

## ☁️ BigQuery and dbt

BigQuery and dbt are planned components of the project workflow.

- **BigQuery:** Store and query hospital event log data in the cloud.
- **dbt:** Transform raw event logs into a standardized format suitable for process mining.

These components will be documented as completed once their integration and validation are finished.

## 🔬 Project Scope

CareFlow is an educational project using **simulated hospital event data**. Its purpose is to demonstrate process mining, workflow analysis, and potential operational inefficiency detection.

Repeated triage events are treated as potential rework indicators; they do not independently establish the clinical reason for a patient's return to triage.

## 🚀 Future Improvements

- Complete and validate BigQuery integration.
- Complete dbt models for event log transformation.
- Improve process analysis and visualization.
- Expand automated data quality checks.

## 👨‍💻 Project Information

**Project Name:** CareFlow — Clinical Pathway Process Mining  
**Domain:** Healthcare Analytics and Process Mining  
**Project Type:** Educational Data Analytics Project

---

*CareFlow — Understanding hospital workflows through data.*
