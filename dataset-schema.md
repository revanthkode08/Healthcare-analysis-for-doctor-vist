# Dataset Schema — Healthcare Doctor Visits

Columns (from guide Column Definitions):
- id: record identifier
- visits: number of doctor visits (numeric target)
- gender: female / male (Personal Information)
- age: normalized age (Personal Information)
- income: normalized income (Financial Information)
- illness: illness count/severity numeric (Health Information)
- reduced: reduced? numeric (Health Information)
- health: health status numeric (Health Information)
- private: yes/no (Healthcare Support)
- freepoor: yes/no (Healthcare Support)
- freerepat: yes/no (Healthcare Support)
- nchronic: yes/no (chronic condition) (Health Information)
- lchronic: yes/no (chronic condition) (Health Information)

Guide groupings:
- Personal Information: gender, age
- Health Information: illness, health, reduced, nchronic, lchronic
- Healthcare Support: private, freepoor, freerepat
- Doctor Visit Information: visits
- Record Identification: id

Rows: 5,190. The inline CSV data must be saved to `healthcare_visits.csv` before running the analysis.
