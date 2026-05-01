## Two-Step Harmonization Evaluation Procedure

### Requirements

You must have an active DataSHIELD session connected to multiple servers.

### Preliminary Steps

You can perform a preliminary evaluation by extracting the data dictionaries from tables of interest without assigning them to the DataSHIELD/R session.

**Compare the data dictionaries by checking consistency across:**
* Variable names
* Variable data types
* Variable categories

### Step 1 — Metadata Evaluation

**Goal:** Verify **structural and definitional consistency** across datasets without accessing data values.

**Why:** Catching incompatibilities at the metadata stage is faster and cheaper than discovering them later.

#### 1.1 Variable Inventory
**Extract and compare variable names across nodes:**
- Identify the **intersection**: variables present in all nodes
- Identify the **symmetric difference**: variables missing from one or more nodes
- Flag variables with different names representing the same concept (e.g., `bmi` vs `BMI` vs `body_mass_index`)

#### 1.2 Data Type Consistency
**For each variable in the intersection, compare its declared type across nodes:** `integer`, `double`, `factor`, `character`, `Date`, etc.

**Flag any type mismatch as a critical harmonization failure.** Type mismatches cause DataSHIELD server-side functions to silently fail or error (e.g., sex coded as `factor` at one node but `integer` at another).

#### 1.3 Factor Level Consistency
**For categorical variables (`factor` type), extract and compare the levels across nodes.**

Check for these issues:
- Missing levels at some nodes
- Extra levels at some nodes
- Different ordering (important for ordinal variables)
- Different labels for the same underlying code

**Example failure:** `smoking_status` has levels `{never, former, current}` at node A but `{0, 1, 2}` at node B

#### 1.4 Data Dictionary / Ontology Alignment
**Map each variable against the study's data dictionary or ontology** (e.g., OMOP, Maelstrom).

**Verify these aspects across all sites:**
- Unit of measurement is documented and consistent (e.g., weight always in kg)
- Reference period or definition matches (e.g., "hypertension at baseline" vs "ever diagnosed")

#### 1.5 Metadata Evaluation Output
**Create a metadata compatibility matrix with:**
- One row per variable
- One column per node
- Cells showing: ✓ (compatible), ⚠ (warnings), or ✗ (incompatible)

**Only variables passing this step proceed to Step 2.**

### Step 2 — Summary Statistics Evaluation

**Goal:** Verify **distributional and empirical consistency** — ensuring harmonized variables have comparable real-world signal across nodes.

**Note:** All statistics are computed in DataSHIELD without exposing individual records.

#### 2.1 Sample Size and Completeness
**Obtain sample size and missingness information:**
- Get total observations per node using `dimensions()`
- Compute **missing value rates** per variable per node using `summary()`
- Flag variables with substantial missingness differences across nodes (e.g., >20% at one site vs <2% at another)

**Note:** Large missingness differences may indicate structural data collection differences rather than harmonization issues.

#### 2.2 Continuous Variables — Distributional Checks
**For each continuous variable, retrieve these statistics across all nodes:**

| Statistic | Purpose |
|---|---|
| Mean, SD | Detect level shifts and scale differences |
| Median, IQR | Robust checks resistant to outliers |
| Min, Max | Detect unit errors (e.g., height in cm vs m) |
| Skewness | Detect systematic transformation differences |

**Interpret patterns:**
- **Large mean shift + similar SD:** Suggests unit or offset error
- **Large SD difference + similar means:** Suggests scale or coding error
- **Use standardized mean difference (SMD):** A scalar quality metric where SMD < 0.1 is acceptable comparability

#### 2.3 Categorical Variables — Frequency Checks
**For each categorical/factor variable, retrieve frequency tables using `frequencies()`.**

**Compare across nodes:**
- **Level proportions:** Check for unusual imbalances
- **Implausible distributions:** Flag anomalies like 95% of one category at one site
- **Binary variables:** Compare prevalence rates; large differences suggest coding inconsistency rather than population differences

#### 2.4 Cross-Variable Consistency Checks
**Verify relationships between variables:**
- Compute **bivariate relationships** known to be stable (e.g., age vs BMI correlation, sex vs disease prevalence) using `correlation()` or `glm()` for model-based approaches
- Disappearing or reversing associations at one node signal harmonization errors

**Check logical constraints:**
- Age should not be < 18 if the study is adults-only
- Pregnancy-related variables should only be non-missing for females

#### 2.5 Temporal / Batch Effects (if applicable)
**If nodes represent different recruitment waves or time periods:**
- Check for **temporal drift** in variable distributions
- Assess whether shifts reflect assay recalibration rather than true population change
- Correct significant drift before conducting pooled analysis

#### 2.6 Summary Statistics Evaluation Output
**Create a harmonization quality report with:**
- Per-variable SMD table across nodes
- Missingness heatmap
- Distribution plots (histograms/density curves) overlaid per node for key continuous variables
- Frequency bar charts per node for key categorical variables
- A list of **pass / warn / fail** decisions per variable with justification

## Combined Decision Framework

**After completing both steps, classify each variable using this triage:**

| Outcome | Criteria | Action |
|---|---|---|
| **Pass** | Metadata compatible + distributions comparable | Include in pooled analysis |
| **Warn** | Minor differences within expected population variation | Include with sensitivity analysis |
| **Harmonize** | Type or coding mismatch (correctable) | Apply transformation script and re-evaluate |
| **Exclude** | Irreconcilable structural or semantic difference | Exclude from that variable's analysis |

**Key benefit:** This two-step approach catches failures at the cheapest stage (metadata first), ensuring only structurally valid variables proceed to the more demanding distributional evaluation in Step 2.