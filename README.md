# Newsvendor Inventory Optimization

## Overview
Implementation of the classic Newsvendor (newsboy) model for daily/weekly optimal ordering (`Q`) in a print distribution network.  
The goal is to minimise expected **overage + underage costs** given uncertain demand.

## The Newsvendor Model
- Overage cost (`c_o`) and Underage cost (`c_u`)
- Critical ratio = `c_u / (c_o + c_u)`
- Optimal `Q` = smallest value where CDF(demand) ≥ critical ratio

See `docs/Theoretical_Notes_Newsvendor.md` for full derivation.

## Project Structure
- `scripts/` — core calculation scripts (single shop, per Grosso, full network, test evaluation)
- `docs/` — theory + project explanation
- `extensions'

## Key Scripts
- `Newsvendor_model_calculation.py` — full OGR + per-Grosso versions
- `First_Test_45501.py` — worst-shop identification + newsvendor
- `Auswertung_Bezugstest.py` — before/after analysis of the real supply test


## Data & Running the Code
Real data lives in an internal SQL Server (`Regulierungsstatistik`).  
For public use the scripts expect either:
- CSV exports, or
- You to adapt the data loading layer.

**Important:** Connection strings have been removed for security. Use environment variables or a local `config.yaml` (gitignored).

## Bayesian Extension (optional)
A small PyMC example on price/demand modeling is included in `extensions/bayes_test.py` (uses the public `renfe.csv` sample). It is not core to the newsvendor work.

## References
- Theoretical notes (internal)
- Explanation_Marktoptimierung
## newsvendor-inventory-optimization
├── README.md
├── docs/
│   ├── Theoretical_Notes_Newsvendor.md          
│   └── Marktoptimierung_Explanation.md   
│   └── DSE_inventory_optimization.pptx
├── scripts/
│   ├── newsvendor_core.py                       
│   ├── Newsvendor_model_calculation.py          
│   ├── First_Test_45501.py                     
│   └── Auswertung_Bezugstest.py                
├── extensions/ 
│   ├── bayes_test.py
│   └── renfe_sample.csv                        
└── .gitignore
