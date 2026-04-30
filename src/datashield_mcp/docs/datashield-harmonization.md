## Two-Step Harmonization Evaluation Procedure

### Step 1 — Metadata Evaluation

The goal here is to verify **structural and definitional consistency** across datasets before touching any data values. This catches incompatibilities early and cheaply.

#### 1.1 Variable Inventory
- Extract the full list of variable names from each dataset/node
- Compute the **intersection** (variables present everywhere) and **symmetric difference** (variables missing from one or more nodes)
- Flag variables that exist under different names but represent the same concept (e.g., `bmi` vs `BMI` vs `body_mass_index`)

#### 1.2 Data Type Consistency
- For each variable in the intersection, compare its declared type across nodes: `integer`, `double`, `factor`, `character`, `Date`, etc.
- Any type mismatch (e.g., sex coded as `factor` in one node and `integer` in another) must be flagged as a **critical harmonization failure** — it will cause DataSHIELD server-side functions to silently fail or error

#### 1.3 Factor Level Consistency
- For categorical variables (`factor` type), extract and compare the **set of levels** across nodes
- Check for: missing levels at some nodes, extra levels, different ordering (relevant for ordinal variables), and different labels for the same underlying code
- Example failure: `smoking_status` has levels `{never, former, current}` at node A but `{0, 1, 2}` at node B

#### 1.4 Data Dictionary / Ontology Alignment
- Map each variable against the study's agreed data dictionary or ontology (e.g., OMOP, Maelstrom)
- Verify that unit of measurement is documented and consistent (e.g., weight always in kg)
- Verify that the reference period or definition (e.g., "hypertension at baseline" vs "ever diagnosed") matches across sites

#### 1.5 Metadata Evaluation Output
Produce a **metadata compatibility matrix**: one row per variable, columns per node, cells indicating ✓ (present and compatible), ⚠ (present with warnings), or ✗ (absent or incompatible). Only variables that pass this step should proceed to Step 2.

### Step 2 — Summary Statistics Evaluation

The goal here is to verify **distributional and empirical consistency** — that harmonized variables carry comparable real-world signal across nodes. In DataSHIELD, all of these statistics are computed without exposing individual records.

#### 2.1 Sample Size and Completeness
- Obtain `N` (total observations) per node using `ds.dim()` or equivalent
- Compute **missing value rates** per variable per node using `ds.summary()` or `ds.meanSdGp()`
- Flag variables where missingness differs substantially across nodes (e.g., >20% at one site, <2% at another), as this may indicate a structural data collection difference rather than a harmonization issue

#### 2.2 Continuous Variables — Distributional Checks
For each continuous variable, retrieve across all nodes:

| Statistic | Purpose |
|---|---|
| Mean, SD | Check for level shifts and scale differences |
| Median, IQR | Robust check robust to outliers |
| Min, Max | Detect unit errors (e.g., height in cm vs m) |
| Skewness | Check for systematic transformation differences |

- Compare statistics node-to-node, accounting for expected genuine population differences
- A large **mean shift** with similar SD suggests a unit or offset error
- A large **SD difference** with similar means suggests a scale or coding error
- Use **standardized mean difference (SMD)** across nodes as a scalar harmonization quality metric; SMD < 0.1 is a conventional threshold for acceptable comparability

#### 2.3 Categorical Variables — Frequency Checks
For each categorical/factor variable, retrieve frequency tables per node using `ds.table1D()`:

- Compare **level proportions** across nodes
- Flag implausible distributions (e.g., 95% of one category at one site)
- For binary variables (e.g., sex, disease status), compare prevalence rates — large unexplained differences suggest coding inconsistency rather than true population variation

#### 2.4 Cross-Variable Consistency Checks
- Compute key **bivariate relationships** known to be stable (e.g., age vs. BMI correlation, sex vs. disease prevalence) using `ds.cor()` or model-based approaches
- If a well-established association disappears or reverses at one node, this is a strong signal of a harmonization error at that node
- Check **logical constraints**: e.g., no individual should have age < 18 if the study is adults-only; pregnancy-related variables should only be non-missing for females

#### 2.5 Temporal / Batch Effects (if applicable)
- If nodes correspond to different recruitment waves or time periods, check for **temporal drift** in variable distributions
- A meaningful shift in a biomarker mean across recruitment years may reflect assay recalibration rather than population change, and should be corrected before pooled analysis

#### 2.6 Summary Statistics Evaluation Output
Produce a **harmonization quality report** containing:
- Per-variable SMD table across nodes
- Missingness heatmap
- Distribution plots (histograms or density curves overlaid per node) for key continuous variables
- Frequency bar charts per node for key categorical variables
- A list of **pass / warn / fail** decisions per variable with justification

## Combined Decision Framework

After both steps, apply the following triage:

| Outcome | Criteria | Action |
|---|---|---|
| **Pass** | Metadata compatible + distributions comparable | Include in pooled analysis |
| **Warn** | Minor distributional differences within expected population variation | Include with sensitivity analysis |
| **Harmonize** | Type or coding mismatch identified and correctable | Apply transformation script and re-evaluate |
| **Exclude** | Irreconcilable structural or semantic difference | Exclude variable or node from that variable's analysis |

This two-step procedure ensures that harmonization failures are caught at the cheapest possible stage (metadata first), and that only structurally valid variables are subjected to the more interpretively demanding distributional evaluation in Step 2.