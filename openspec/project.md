# Project Context

## Purpose

**Chile House Pricing** is an end-to-end MLOps learning project focused on predicting house prices in Santiago, Chile. The primary goals are:

1. **Learn MLOps best practices** through hands-on implementation
2. **Build a complete ML pipeline** from data collection to model deployment
3. **Create a production-ready system** for real estate price prediction
4. **Demonstrate industry-standard practices** in ML engineering

This project serves as an educational journey through the entire ML lifecycle, structured as a monorepo to facilitate understanding of how different components interact.

## Tech Stack

### Current (Phase 1 - Data Pipeline)
- **Python 3.12+** - Primary programming language
- **Playwright** - Web scraping and browser automation
- **SQLite** - Local database for property data
- **FastAPI** - REST API framework (skeleton ready)
- **Pydantic** - Data validation and schemas
- **Uvicorn** - ASGI web server

### Planned (Phase 2+ - ML & MLOps)
- **Pandas, NumPy** - Data manipulation and analysis
- **Scikit-learn** - Preprocessing, feature engineering, baseline models
- **XGBoost, LightGBM** - Gradient boosting models
- **MLflow** - Experiment tracking and model registry
- **Optuna** - Hyperparameter optimization
- **Matplotlib, Seaborn, Plotly** - Data visualization
- **Jupyter** - Interactive notebooks for EDA
- **Docker & Docker Compose** - Containerization
- **Pytest** - Testing framework
- **Black, Ruff** - Code formatting and linting

### Future Options (Advanced)
- **DVC** - Data version control (when datasets grow)
- **GitHub Actions** - CI/CD pipelines
- **Prometheus + Grafana** - Monitoring and dashboards

## Project Conventions

### Code Style

**Python Standards:**
- Follow PEP 8 style guide
- Use **Black** for formatting (line length: 100)
- Use **Ruff** for linting
- Type hints encouraged but not required initially
- Docstrings for all public functions and classes

**Naming Conventions:**
- `snake_case` for functions, variables, and file names
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix private methods with single underscore `_method_name`

**Import Organization:**
```python
# Standard library
import asyncio
import json

# Third-party
from playwright.async_api import async_playwright
from fastapi import FastAPI

# Local imports
from data_pipeline.scrapers import PortalInmobiliarioScraper
```

### Architecture Patterns

**Monorepo Structure:**
- Separate concerns into distinct top-level directories
- Each component (data-pipeline, ml, api) is independently testable
- Shared code goes in appropriate module, not duplicated

**Data Pipeline:**
- **Modular design**: Each scraper component has single responsibility
- **Rate limiting**: Respectful web scraping with configurable delays
- **Database abstraction**: Centralized DB operations in `db_manager.py`
- **Async/await**: Use Playwright's async API for efficient scraping

**ML Development:**
- **Notebooks for exploration**: Use `ml/notebooks/` for EDA and experimentation
- **Scripts for production**: Use `ml/src/` for reusable, tested code
- **Separation of concerns**:
  - `features/` - Feature engineering pipelines
  - `models/` - Training, evaluation, prediction
  - `utils/` - Shared utilities

**API Design:**
- **RESTful principles**: Clear resource-based endpoints
- **Pydantic schemas**: Validate all inputs/outputs
- **Versioned API**: Use `/api/v1/` prefix for endpoints
- **Health checks**: Always include `/health` endpoint

### Testing Strategy

**Planned Approach (Phase 3+):**
- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **API tests**: Test endpoints with test client
- **Data validation tests**: Verify data quality and schema

**Testing Tools:**
- `pytest` for all tests
- `pytest-asyncio` for async code
- `httpx` for API testing
- Test fixtures in `conftest.py`

**Coverage Goals:**
- Core business logic: 80%+ coverage
- Critical paths: 100% coverage
- Exploratory notebooks: No coverage requirement

### Git Workflow

**Branching Strategy:**
- `main` - Production-ready code, always deployable
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `refactor/description` - Code improvements

**Commit Conventions:**
```
type: subject line (max 50 chars)

Detailed description (optional, max 72 chars per line)
- Bullet points for multiple changes
- Reference issues/PRs if applicable

Examples:
- feat: Add XGBoost model training pipeline
- fix: Correct price parsing in scraper
- refactor: Split main.py into modular components
- docs: Update API usage examples
- test: Add unit tests for feature engineering
```

**Commit Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code restructuring
- `docs` - Documentation changes
- `test` - Adding/updating tests
- `chore` - Maintenance tasks

## Domain Context

### Chilean Real Estate Market

**Currency:**
- Properties priced in **UF (Unidad de Fomento)** - inflation-adjusted unit
- 1 UF ≈ 30,000 CLP (Chilean Pesos), varies daily
- Maintenance fees typically in CLP

**Geographic Focus:**
- **Santiago, Chile** - Primary metropolitan area
- Key comunas (districts): Las Condes, Vitacura, Providencia, Ñuñoa
- Coordinates: Latitude -33.7 to -33.2, Longitude -71.0 to -70.3

**Property Features:**
- **Bedrooms (dormitorios)**: Typically 1-4 for apartments
- **Bathrooms (baños)**: 1-4 for apartments
- **Area**: Measured in m² (square meters)
  - Total area vs. built area (útil)
  - Typical range: 20-1000 m²
- **Parking (estacionamientos)**: 0-5 spots
- **Common amenities**: Pool (piscina), gym (gimnasio), security (seguridad), storage (bodega)

**Data Source:**
- **Portal Inmobiliario** (portalinmobiliario.com) - Chile's largest real estate platform
- Listings have MLC identifiers (e.g., MLC-1234567)

### Machine Learning Context

**Problem Type:**
- Regression task (predicting continuous price values)
- Target variable: `price_uf` (price in UF units)

**Features:**
- **Numerical**: bedrooms, bathrooms, area, parking, building_age, floor
- **Categorical**: comuna, amenities (one-hot encoded)
- **Derived**: price_per_m2, distance_to_metro (future)
- **Boolean**: has_pool, has_gym, has_security, has_elevator

**Model Evaluation:**
- Primary metric: RMSE (Root Mean Squared Error) in UF
- Secondary metrics: MAE, R² score
- Cross-validation: 5-fold CV recommended

## Important Constraints

### Web Scraping Ethics

**Rate Limiting (CRITICAL):**
- **Minimum delay**: 3-8 seconds between requests
- **Max requests per minute**: 10
- **Avoid peak hours**: No scraping 9 AM - 6 PM Santiago time
- **Respect robots.txt**: Check before expanding scraping scope

**Data Usage:**
- Educational and research purposes only
- No commercial redistribution of scraped data
- Respect data provider's terms of service

### Technical Constraints

**Development Environment:**
- Python 3.12+ required
- Playwright browsers must be installed (`playwright install chromium`)
- macOS development (primary), should be cross-platform compatible

**Data Storage:**
- SQLite for development (suitable for 100K+ properties)
- Consider PostgreSQL for production scale
- Keep raw data under version control if < 100MB

**API Performance:**
- Prediction latency target: < 200ms
- Support concurrent requests: 10+ simultaneous

### Learning Constraints

**Progressive Complexity:**
- Don't implement advanced features (DVC, Kubernetes) until core concepts are mastered
- Focus on understanding before optimizing
- Keep it simple: favor readability over cleverness

**Documentation:**
- Every major phase should update relevant documentation
- Notebooks should have markdown explanations
- Code comments for non-obvious logic only

## External Dependencies

### Primary Dependencies

**Portal Inmobiliario Website:**
- URL: `https://www.portalinmobiliario.com`
- Purpose: Source of property listing data
- Reliability: Stable, but selectors may change
- Contingency: Scraper has multiple fallback selectors

**UF Exchange Rate (Future):**
- May need API for UF to CLP conversion
- Options: Chilean Central Bank API, financial data providers

### Development Tools

**Playwright:**
- Browser automation for web scraping
- Requires installed Chromium browser
- Version: 1.54.0+

**FastAPI:**
- Auto-generates OpenAPI docs at `/docs`
- Requires uvicorn for serving

### Future Integrations (Planned)

**MLflow Tracking Server:**
- Local deployment initially
- Cloud deployment for team collaboration (future)

**Model Serving:**
- Start with FastAPI
- Consider MLflow model serving or Seldon Core (advanced)

**Cloud Storage (Optional):**
- AWS S3 or Google Cloud Storage for large datasets
- Integration with DVC when needed

## Project Status

**Current Phase:** Phase 1 - Data Pipeline ✅ Complete

**Next Steps:**
1. Collect more property data (expand scraping)
2. Begin Phase 2: ML Development (EDA in notebooks)
3. Feature engineering and model training
4. Complete API implementation for predictions

**Version:** 0.1.0
