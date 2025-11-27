# 🏠 Chile House Pricing - MLOps Project

An end-to-end MLOps project for predicting house prices in Santiago, Chile. This project demonstrates the complete machine learning lifecycle from data collection to model deployment.

## 📋 Project Overview

This project is structured as a **monorepo** containing:
- **Data Pipeline**: Web scraping from Portal Inmobiliario
- **ML Development**: Feature engineering, model training, and experimentation
- **API**: FastAPI service for serving predictions
- **Infrastructure**: Docker setup and deployment scripts

**Goal**: Learn and implement MLOps best practices while building a real-world house price prediction system.

## 🏗️ Project Structure

```
chile-house-pricing/
│
├── data-pipeline/              # Data Collection & ETL
│   ├── scrapers/              # Web scraping modules
│   │   ├── models.py          # PropertyData and ScrapingConfig
│   │   ├── rate_limiter.py    # Respectful rate limiting
│   │   └── portal_inmobiliario.py  # Main scraper
│   ├── database/              # Database management
│   │   └── db_manager.py      # SQLite operations
│   └── jobs/                  # Scheduled jobs
│       └── scrape_job.py      # Main scraping job
│
├── ml/                        # Machine Learning
│   ├── data/                  # Datasets
│   │   ├── raw/              # Scraped data
│   │   ├── processed/        # Cleaned data
│   │   └── splits/           # Train/val/test
│   ├── notebooks/            # Jupyter notebooks for EDA
│   ├── src/                  # ML source code
│   │   ├── features/         # Feature engineering
│   │   ├── models/           # Training & evaluation
│   │   └── utils/            # Utilities
│   ├── experiments/          # MLflow tracking
│   └── models/               # Saved models
│
├── api/                       # Model Serving API
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── routers/          # API endpoints
│   │   ├── schemas/          # Pydantic models
│   │   └── services/         # Business logic
│   └── tests/
│
├── infrastructure/            # DevOps & MLOps
│   ├── docker/               # Docker configurations
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.scraper
│   │   └── Dockerfile.api
│   └── scripts/              # Helper scripts
│       ├── setup.sh
│       └── run_scraper.sh
│
├── docs/                      # Documentation
│   ├── data-pipeline-guide.md
│   ├── scraper-usage.md
│   └── web-scraping-study-guide.md
│
└── pyproject.toml            # Project dependencies

```

## 🚀 Quick Start

### 1. Setup

Run the setup script:
```bash
bash infrastructure/scripts/setup.sh
```

Or manually:
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### 2. Run the Data Pipeline

```bash
# Run demo (scrapes 3 properties)
python -m data-pipeline.jobs.scrape_job --demo

# Or use the script
bash infrastructure/scripts/run_scraper.sh --demo

# Interactive mode (choose scraping options)
python -m data-pipeline.jobs.scrape_job
```

### 3. Start the API

```bash
uvicorn api.app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

### 4. Explore the Data (Coming Soon)

```bash
# Install ML dependencies
pip install -e ".[ml,viz]"

# Start Jupyter
jupyter notebook ml/notebooks
```

## 🎓 Learning Path

This project is designed as a learning journey through MLOps:

### Phase 1: Data Pipeline ✅ (Current)
- [x] Web scraping with Playwright
- [x] Data storage (SQLite)
- [x] Modular code structure
- [ ] Scheduled data collection
- [ ] Data validation with Great Expectations

### Phase 2: ML Development (Next)
- [ ] Exploratory Data Analysis (EDA)
- [ ] Feature engineering
- [ ] Model training (XGBoost, LightGBM)
- [ ] Experiment tracking with MLflow
- [ ] Hyperparameter tuning with Optuna
- [ ] Model evaluation & validation

### Phase 3: Model Serving
- [ ] Complete API implementation
- [ ] Model loading & inference
- [ ] API testing
- [ ] Input validation

### Phase 4: MLOps
- [ ] Docker containerization
- [ ] CI/CD with GitHub Actions
- [ ] Model monitoring
- [ ] A/B testing infrastructure
- [ ] Prometheus + Grafana dashboards

## 📊 Current Data

The project has scraped initial property data:
- **Location**: Portal Inmobiliario listings
- **Area**: Las Condes, Santiago
- **Format**: SQLite database + JSON files
- **Path**: `ml/data/raw/`

## 🛠️ Tech Stack

### Data Collection
- **Playwright**: Web scraping
- **SQLite**: Local database

### ML & Data Science
- Pandas, NumPy (data manipulation)
- Scikit-learn (preprocessing, baseline models)
- XGBoost, LightGBM (gradient boosting)
- MLflow (experiment tracking)
- Optuna (hyperparameter tuning)

### API & Deployment
- **FastAPI**: REST API
- **Pydantic**: Data validation
- **Docker**: Containerization
- **Uvicorn**: ASGI server

## 📖 Documentation

Detailed documentation is available in the `docs/` folder:
- [Data Pipeline Guide](docs/data-pipeline-guide.md) - Technical details of the scraper
- [Scraper Usage](docs/scraper-usage.md) - How to use the scraper
- [Web Scraping Study Guide](docs/web-scraping-study-guide.md) - Learn Playwright basics

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (when implemented)
pytest
```

## 🐳 Docker Usage

```bash
# Build and run all services
docker-compose -f infrastructure/docker/docker-compose.yml up

# Run only the API
docker-compose -f infrastructure/docker/docker-compose.yml up api

# Run scraper
docker-compose -f infrastructure/docker/docker-compose.yml run scraper
```

## 📝 Development Workflow

1. **Scrape Data**: Collect property listings
2. **Explore Data**: Jupyter notebooks for EDA
3. **Engineer Features**: Create meaningful features
4. **Train Models**: Experiment with different algorithms
5. **Track Experiments**: Use MLflow
6. **Deploy Model**: Update API with best model
7. **Monitor**: Track performance in production

## 🤝 Contributing

This is a learning project, but suggestions and improvements are welcome!

## 📜 License

MIT License

## 🙏 Acknowledgments

- Portal Inmobiliario for property data
- Built following MLOps best practices

---

**Status**: 🚧 Active Development - Phase 1 (Data Pipeline) Complete
