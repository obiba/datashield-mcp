## What is DataSHIELD?

DataSHIELD is a federated analysis framework that allows researchers to analyze individual-level data held across multiple servers/cohorts **without the data ever leaving its original location**. Only aggregated, non-disclosive results are returned. This has important implications for how you frame and operationalize each PICO element.

## What is PICO?

The PICO framework is a structured approach used primarily in evidence-based medicine and clinical research to formulate well-built clinical questions and guide literature searches. Here's what each component means:

**P — Patient / Population / Problem**
Who is the question about? This defines the specific patient group or population of interest, often including relevant characteristics like age, condition, sex, or risk factors. For example: "adult patients with type 2 diabetes" or "postmenopausal women with osteoporosis."

**I — Intervention**
What are you considering doing? This is the main action being evaluated — a treatment, diagnostic test, exposure, medication, procedure, or even a policy. For example: "metformin therapy" or "cognitive behavioral therapy."

**C — Comparison**
What is the alternative? This is what you're comparing the intervention against — a placebo, standard of care, a different drug, no treatment, or another intervention. Sometimes there's no comparator, in which case this element can be omitted (leading to a PIO or PO question).

**O — Outcome**
What are you trying to measure or achieve? This defines the effect you care about — symptom relief, mortality, quality of life, adverse events, cost, etc. Being specific here is important because it shapes what evidence you look for.

PICO helps researchers and clinicians in several practical ways. It transforms vague clinical questions into precise, searchable queries. It makes it easier to identify relevant studies and filter out irrelevant ones. It also sets the stage for critically appraising evidence by making inclusion/exclusion criteria explicit.

## Mapping PICO to DataSHIELD

**P — Population**

In DataSHIELD, your population is distributed across multiple cohorts or data nodes. You need to define:

- Inclusion/exclusion criteria that can be **harmonized** across all participating datasets (variables may be named or coded differently in each cohort)
- Whether the pooled population is appropriate — e.g., are the cohorts comparable enough to be analyzed together?
- Subsetting in DataSHIELD is done server-side using functions like `ds.subsetByClass()` or logical filters, so your P definition must be expressible in variables that exist (or can be derived) in every node

**I — Intervention (or Exposure)**

In federated epidemiological research (DataSHIELD is more commonly used for observational data than trials), this is often reframed as an **exposure**. You need to ensure:

- The exposure variable is measured consistently across nodes, or that a **harmonization protocol** exists
- The variable is available in the DataSHIELD-compatible format (e.g., continuous, binary, categorical)
- Any derived variables (e.g., BMI from height/weight) can be computed server-side using `ds.assign()`

**C — Comparison**

This defines your reference group. In DataSHIELD:

- The comparison group must be definable from the same harmonized variables
- You need to ensure **sufficient cell counts** in each node — DataSHIELD has disclosure controls that prevent returning results based on very small groups (typically n < 3 or configurable thresholds), so your comparison group must be large enough across all nodes
- If doing a case-control or stratified analysis, each stratum must be non-disclosive at every node

**O — Outcome**

The outcome must be:

- Available (or derivable) in all participating nodes
- Measurable using DataSHIELD's supported statistical methods — e.g., `glm` for regression, `survival` for time-to-event, `lmer` for mixed models
- Defined in a way that respects the **aggregation-only** constraint — you can't retrieve individual outcome values, only model outputs

PICO in DataSHIELD is not just a clinical framing tool — it also becomes a **data engineering and governance checklist**. The clearer your PICO, the easier your harmonization, disclosure risk assessment, and analysis planning will be.

## Practical Considerations Unique to DataSHIELD

**Harmonization before analysis** — Before you can run any PICO-defined analysis, there's often a significant pre-analysis phase where you verify that P, I, C, and O variables are harmonized across nodes. Maelstrom Research's harmonization guidelines are often used here.

**Feasibility checks** — You should run `dimensions`, `summary`, and `table` calls across nodes early to verify that your population and variable definitions are workable before committing to a full analysis plan.

**Statistical limitations** — Not all methods are available in DataSHIELD. Your O (outcome analysis) must be achievable with supported functions. If your PICO question requires, say, a complex Bayesian model or machine learning approach not yet implemented, you'll need to adapt or advocate for new DataSHIELD modules.

**Heterogeneity across nodes** — Even if PICO is well-defined, cohort-level differences (design, measurement tools, follow-up time) may introduce heterogeneity. Meta-analytic approaches within DataSHIELD (e.g., fixed or random effects pooling) may be needed, and this should be anticipated in your O definition.

**Governance and data access** — Each node may have different governance requirements. Your PICO question may need to be submitted for ethical/governance approval at each site independently, and some nodes may not be able to contribute to certain sub-analyses.


## Example

Say you want to study the association between **physical inactivity and type 2 diabetes** across European cohorts using DataSHIELD:

- **P**: Adults aged 40–70 across participating cohorts with no diabetes diagnosis at baseline
- **I**: Self-reported physical inactivity (below WHO guidelines), harmonized to a binary variable across cohorts
- **C**: Physically active participants (meeting WHO guidelines)
- **O**: Incident type 2 diabetes (ICD code or self-report), analyzed using `glm` with logistic regression, adjusted for age, sex, and BMI computed server-side

You would then verify that all four elements can be operationalized in every node before proceeding.
