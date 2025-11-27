# Migration Guide - Old to New Structure

This document explains how the project was restructured for MLOps.

## What Changed?

### Old Structure (Single File)
```
chile-house-pricing/
├── main.py                    # Everything in one 1500-line file
├── README.md                  # Docs
├── USAGE_GUIDE.md
├── WEB_SCRAPING_STUDY_GUIDE.md
├── *.json                     # Data files scattered
└── properties.db
```

### New Structure (Modular MLOps)
```
chile-house-pricing/
├── data-pipeline/             # ✨ NEW: Organized data collection
│   ├── scrapers/             # Modular scraping code
│   ├── database/             # DB management
│   └── jobs/                 # Runnable jobs
│
├── ml/                        # ✨ NEW: ML workspace
│   ├── data/raw/             # Your data moved here
│   ├── notebooks/            # For experimentation
│   └── src/                  # ML code (future)
│
├── api/                       # ✨ NEW: FastAPI service
│   └── app/                  # API code
│
├── infrastructure/            # ✨ NEW: DevOps tools
│   ├── docker/               # Containerization
│   └── scripts/              # Helper scripts
│
└── docs/                      # ✨ NEW: Organized docs
    └── *.md                  # All docs moved here
```

## File Mapping

### Code Migration

| Old Location | New Location | Changes |
|-------------|-------------|---------|
| `main.py` (lines 13-41) | `data-pipeline/scrapers/models.py` | ScrapingConfig & PropertyData |
| `main.py` (lines 102-146) | `data-pipeline/scrapers/rate_limiter.py` | RateLimiter class |
| `main.py` (lines 147-1383) | `data-pipeline/scrapers/portal_inmobiliario.py` | Main scraper |
| `main.py` (lines 163-256) | `data-pipeline/database/db_manager.py` | Database operations |
| `main.py` (lines 1384-1536) | `data-pipeline/jobs/scrape_job.py` | main() and demo functions |

### Data Migration

| Old Location | New Location |
|-------------|-------------|
| `portal_inmobiliario_listings.json` | `ml/data/raw/` |
| `demo_detailed_properties.json` | `ml/data/raw/` |
| `detailed_properties_batch_*.json` | `ml/data/raw/` |
| `properties.db` | `ml/data/raw/` |

### Documentation Migration

| Old Location | New Location |
|-------------|-------------|
| `README.md` | `docs/data-pipeline-guide.md` |
| `USAGE_GUIDE.md` | `docs/scraper-usage.md` |
| `WEB_SCRAPING_STUDY_GUIDE.md` | `docs/web-scraping-study-guide.md` |

## How to Use the New Structure

### Running the Scraper

**Old way:**
```bash
python main.py
```

**New way:**
```bash
# Option 1: Direct Python
python -m data-pipeline.jobs.scrape_job --demo

# Option 2: Using helper script
bash infrastructure/scripts/run_scraper.sh --demo
```

### Importing Code

**Old way:**
```python
# Everything in main.py
from main import PortalInmobiliarioScraper, ScrapingConfig
```

**New way:**
```python
# Clean imports from organized modules
from data_pipeline.scrapers import PortalInmobiliarioScraper, ScrapingConfig
from data_pipeline.database import DatabaseManager
```

## Benefits of New Structure

### 1. **Separation of Concerns**
- Data pipeline code is separate from ML code
- API code is separate from scraping code
- Each component can evolve independently

### 2. **Easier Testing**
- Test each module independently
- Mock dependencies easily
- Clearer test organization

### 3. **Better Collaboration**
- Multiple people can work on different components
- Clearer ownership of code sections
- Easier code reviews

### 4. **MLOps Ready**
- CI/CD pipelines can target specific components
- Docker containers for each service
- Clear deployment boundaries

### 5. **Learning Path**
- Work on one component at a time
- Clear progression: Data → ML → API → Deploy
- Each phase builds on the previous

## Next Steps

### Immediate (Week 1)
1. ✅ **Test the scraper** with new structure
   ```bash
   python -m data-pipeline.jobs.scrape_job --demo
   ```

2. ✅ **Verify data** is in the right place
   ```bash
   ls ml/data/raw/
   ```

3. ✅ **Start the API** to ensure it works
   ```bash
   uvicorn api.app.main:app --reload
   ```

### Phase 2: ML Development (Week 2-5)
1. **Install ML dependencies**
   ```bash
   pip install -e ".[ml,viz]"
   ```

2. **Start with EDA**
   - Open `ml/notebooks/01_eda.ipynb`
   - Load data from `ml/data/raw/properties.db`
   - Explore distributions, correlations

3. **Feature Engineering**
   - Create features in `ml/src/features/build_features.py`
   - Save processed data to `ml/data/processed/`

4. **Model Training**
   - Train models in `ml/src/models/train.py`
   - Track experiments with MLflow
   - Save best model to `ml/models/`

### Phase 3: API Integration (Week 6-7)
1. **Implement prediction endpoint**
   - Load trained model
   - Create `/api/v1/predict` endpoint
   - Add proper error handling

2. **Add model versioning**
   - Load different model versions
   - A/B testing support

### Phase 4: Deployment (Week 8+)
1. **Containerize with Docker**
   ```bash
   docker-compose up
   ```

2. **Set up CI/CD**
   - GitHub Actions for tests
   - Automated deployment

3. **Add monitoring**
   - Model performance tracking
   - Data drift detection

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`:
```bash
# Make sure you're in the project root
pwd  # Should show .../chile-house-pricing

# Reinstall in editable mode
pip install -e .
```

### Scraper Not Working
```bash
# Reinstall Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### Database Not Found
The database moved to `ml/data/raw/`. Update the config:
```python
config = ScrapingConfig(
    database_path="ml/data/raw/properties.db"
)
```

## Questions?

- Check `README.md` for quick start
- Check `docs/` for detailed guides
- Each component has its own README:
  - `ml/notebooks/README.md`
  - `ml/data/README.md`
  - `api/README.md`

## Summary

The migration transforms your scraper into a professional MLOps project by:
- **Organizing code** into logical modules
- **Preparing for ML** with proper data structure
- **Enabling deployment** with API and Docker
- **Supporting learning** with clear progression

You can now work on each phase independently while the overall structure supports the complete ML lifecycle! 🚀
