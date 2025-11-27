# ML Data Directory

This directory contains all data used for machine learning.

## Directory Structure

- **raw/** - Original scraped data (JSON files, database exports)
- **processed/** - Cleaned and feature-engineered datasets
- **splits/** - Train/validation/test splits

## Data Versioning

Consider using DVC (Data Version Control) to track data changes:

```bash
pip install dvc
dvc init
dvc add ml/data/raw/properties.db
git add ml/data/raw/properties.db.dvc .gitignore
git commit -m "Track properties database with DVC"
```
