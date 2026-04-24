# APGI Framework Step-by-Step Tutorials

## 🎯 Overview

This guide provides detailed, step-by-step tutorials for common APGI Framework workflows. Each tutorial includes screenshots, code examples, and troubleshooting tips.

---

## 📚 Tutorial 1: Your First Parameter Estimation Experiment

### Objective: Parameter Estimation

Learn to run a basic parameter estimation experiment and interpret the results.

### Prerequisites

- APGI Framework deployed (see [Quick Start Guide](quick_start_guide.md))
- Basic understanding of Bayesian concepts

---

### Step 1: Launch the Web Interface

1. Open your web browser
2. Navigate to `http://localhost:8000`
3. You should see the APGI Framework dashboard

### Expected View

- Welcome screen with navigation menu
- "New Experiment" button prominently displayed

---

### Step 2: Create a New Experiment

1. Click **"New Experiment"** in the top navigation
2. Fill in the experiment details:
   - **Name**: "Tutorial 1 - Basic Parameter Estimation"
   - **Description**: "Learning basic parameter estimation"
   - **Type**: Select "Parameter Estimation"
   - **Data Source**: "Simulated Data"
3. Click **"Create Experiment"**

### Troubleshooting

- If button is disabled, ensure all required fields are filled
- If experiment type is not available, check framework is fully loaded

---

### Step 3: Configure Parameters

1. In the experiment setup page, you'll see parameter configuration

2. Set the following initial values:

| Parameter                      | Value | Description                          |
|--------------------------------|-------|--------------------------------------|
| theta_0 (Ignition Threshold)   | 0.5   | Threshold for conscious ignition     |
| Pi_i (Interoceptive Precision) | 1.0   | Precision of interoceptive signals   |
| beta (Somatic Bias)            | 0.0   | Baseline somatic bias                |

1. **Advanced Settings** (click to expand)
   - **Number of Trials**: 1000
   - **Burn-in Period**: 200
   - **Sampling Rate**: 10 Hz

2. Click **"Save Configuration"**

---

### Step 4: Run the Experiment

1. Review your configuration in the summary panel
2. Click **"Start Experiment"**
3. You'll see a progress bar and real-time updates

### What to Watch For

- Progress percentage updating
- Parameter estimates changing in real-time
- Convergence diagnostics

---

### Step 5: Monitor Progress

While the experiment runs:

1. **Watch the Parameter Plots**
   - Lines should stabilize over time
   - Credible intervals should narrow
   - R̂ values should approach 1.0
2. **Check Convergence Status**
   - Green checkmark = converged
   - Yellow warning = still converging
   - Red X = convergence issues
3. **Monitor Resource Usage**
   - CPU usage should be moderate
   - Memory usage should be stable

---

### Step 6: Analyze Results

Once the experiment completes:

1. **View Summary Statistics**
   - Final parameter estimates
   - 95% credible intervals
   - Convergence diagnostics
2. **Examine Trace Plots**
   - Look for stationarity
   - Check for good mixing
   - Identify any outliers
3. **Review Posterior Distributions**
   - Should be approximately normal
   - No multiple modes
   - Reasonable parameter ranges

---

### Step 7: Export Results

1. Click **"Export Results"**
2. Choose export format:
   - **CSV**: For spreadsheet analysis
   - **JSON**: For programmatic use
   - **PDF Report**: Complete analysis report
3. Select destination and save

---

## 📊 Tutorial 2: Real-time Monitoring Setup

### Objective: Real-time Monitoring

Set up and use real-time monitoring for live data streams.

---

### Step 1: Access Monitoring Dashboard

1. From main interface, click **"Monitoring"**
2. Or navigate directly to `http://localhost:8000/monitoring`

---

### Step 2: Start Real-time Streaming

1. In the monitoring dashboard, locate the control panel
2. Click **"Start Streaming"**
3. Wait for connection status to show "Connected"

### Expected Status Indicators

- 🟢 Streaming: Active
- 🔌 Connection: Connected
- 📊 Data Processing: Normal

### Step 3: Monitor EEG Data

1. Click the **"Monitoring"** tab
2. Observe the EEG monitor panel:
   - Signal quality indicator (green = good)
   - Artifact rate percentage
   - P3b and HEP amplitude displays
3. **Interpret Quality Metrics**
   - Quality > 0.8 = Excellent
   - Quality 0.6-0.8 = Good
   - Quality < 0.6 = Needs attention

---

### Step 4: View Real-time Plots

1. Click the **"Real-time Plots"** tab
2. You'll see four live plots:
   - EEG Signal Quality
   - Pupil Diameter
   - Heart Rate
   - Parameter Estimates
3. **Plot Features**
   - Auto-scaling Y-axes
   - 30-second rolling window
   - Color-coded data streams

---

### Step 5: Set Up Alerts

1. Click the **"Alerts"** tab
2. Configure alert thresholds:
   - EEG quality < 0.7
   - Pupil data loss > 20%
   - Heart rate outside 40-100 BPM
3. Click **"Enable Alerts"**

---

## 🔬 Tutorial 3: Advanced Parameter Configuration

### Objective: Advanced Parameters

Learn to configure advanced parameters for specific experimental paradigms.

---

### Step 1: Access Advanced Configuration

1. Create new experiment
2. In parameter setup, click **"Advanced Settings"**
3. Expand all configuration sections

---

### Step 2: Configure Priors

Set informative priors based on literature:

```python
# Example prior configurations
priors = {
    'theta0': {'dist': 'normal', 'mu': 0.5, 'sigma': 0.2},
    'pi_i': {'dist': 'lognormal', 'mu': 0.0, 'sigma': 0.5},
    'beta': {'dist': 'normal', 'mu': 0.0, 'sigma': 0.1}
}
```

---

### Step 3: Set Up Hierarchical Model

For multi-subject analysis:

1. Enable **"Hierarchical Modeling"**
2. Configure group-level parameters:
   - Group mean priors
   - Between-subject variance
   - Shrinkage parameters

---

### Step 4: Configure Sampling

Advanced sampling settings:

| Setting           | Recommended Value | When to Use                 |
|-------------------|-------------------|-----------------------------|
| Chains            | 4                 | Standard analysis           |
| Iterations        | 4000              | Complex models              |
| Thin              | 2                 | Large datasets              |
| Adapt Delta       | 0.95              | Difficult posteriors        |

---

## 📈 Tutorial 4: Batch Processing and Automation

### Objective: Batch Processing

Process multiple experiments automatically.

---

### Step 1: Prepare Batch Configuration

1. Create a batch configuration file:

```json
{
  "experiments": [
    {
      "name": "Subject_01",
      "parameters": {"theta0": 0.5, "pi_i": 1.0, "beta": 0.0},
      "trials": 1000
    },
    {
      "name": "Subject_02",
      "parameters": {"theta0": 0.6, "pi_i": 1.2, "beta": 0.1},
      "trials": 1000
    }
  ],
  "output_directory": "batch_results"
}
```

---

### Step 2: Run Batch Processing

1. Navigate to **"Batch Processing"** in the interface
2. Upload your configuration file
3. Click **"Start Batch"**

---

### Step 3: Monitor Progress

Batch processing dashboard shows:

- Individual experiment status
- Overall progress
- Resource utilization
- Error log

---

## 🔍 Tutorial 5: Model Comparison and Validation

### Objective: Model Comparison

Compare different models and validate results.

### Step 1: Set Up Model Comparison

1. Create multiple experiments with different models:
   - **Model A**: Basic APGI
   - **Model B**: APGI with learning
   - **Model C**: Hierarchical APGI
2. Use same data for all models

---

### Step 2: Run Model Comparison

1. Go to **"Model Comparison"** tab
2. Select experiments to compare
3. Choose comparison metrics:
   - WAIC (Widely Applicable Information Criterion)
   - LOO-CV (Leave-One-Out Cross-Validation)
   - Bayes Factors

---

### Step 3: Interpret Results

### Model Selection Criteria

- Lower WAIC = Better model
- Lower LOO-CV = Better predictive performance
- Bayes Factor > 3 = Strong evidence

---

### Step 4: Validate Results

1. Cross-validation:
   - K-fold validation
   - Leave-one-subject-out
   - Temporal validation
2. Sensitivity analysis:
   - Prior sensitivity
   - Parameter identifiability
   - Model robustness

---

## 🛠️ Tutorial 6: Custom Analysis Pipeline

### Objective: Analysis Pipeline

Create custom analysis workflows.

---

### Step 1: Access Analysis Pipeline Builder

1. Navigate to **"Analysis Pipelines"**
2. Click **"Create New Pipeline"**

---

### Step 2: Design Pipeline

Drag and drop analysis steps:

1. **Data Preprocessing**
   - Filter artifacts
   - Normalize signals
   - Segment epochs
2. **Parameter Estimation**
   - Configure sampler
   - Set priors
   - Define likelihood
3. **Post-processing**
   - Convergence checks
   - Posterior predictive checks
   - Effect size calculations

---

### Step 3: Execute Pipeline

1. Validate pipeline configuration
2. Click **"Run Pipeline"**
3. Monitor execution in real-time

---

## 📝 Tutorial 7: Report Generation

### Objective: Report Generation

Generate professional analysis reports.

---

### Step 1: Configure Report

1. Complete your analysis
2. Click **"Generate Report"**
3. Choose report template:
   - **Standard**: Basic results summary
   - **Detailed**: Full analysis report
   - **Publication**: Journal-ready format

### Step 2: Customize Report

Add sections:

- Executive summary
- Methods description
- Results tables
- Figures and plots
- Discussion points
- Supplementary materials

---

### Step 3: Export and Share

1. Preview report
2. Make final adjustments
3. Export in desired format:
   - PDF (for sharing)
   - LaTeX (for publication)
   - HTML (for web)

---

## 🔧 Common Workflow Patterns

### Pattern 1: Exploratory Analysis

1. Quick parameter sweep
2. Visualize results
3. Identify promising configurations
4. Refine and repeat

### Pattern 2: Confirmatory Analysis

1. Pre-register analysis plan
2. Collect data
3. Run pre-specified analysis
4. Report results transparently

### Pattern 3: Multi-site Study

1. Standardize protocols
2. Batch process sites
3. Meta-analysis
4. Cross-site validation

---

## 💡 Pro Tips

### Efficiency Tips

- Use keyboard shortcuts (Ctrl+S to save, Ctrl+R to run)
- Bookmark frequently used configurations
- Use templates for similar experiments

### Quality Assurance

- Always check convergence diagnostics
- Validate with simulated data first
- Document analysis decisions

### Collaboration

- Share experiment configurations
- Use version control for analysis scripts
- Document parameter choices

---

## 🆘 Getting Help

### Built-in Help

- **F1**: Context-sensitive help
- **Help Menu**: Complete documentation
- **Tool Tips**: Hover over elements

### Video Tutorials

- [Basic Setup](link-to-video)
- [Advanced Analysis](link-to-video)
- [Troubleshooting](link-to-video)

### Community Support

- [User Forum](link-to-forum)
- [Stack Overflow](link-to-so)
- [Office Hours](link-to-hours)

---

### 📚 Next Steps

After completing these tutorials:

1. **Explore Examples**: Check the `examples/` directory
2. **Read API Docs**: Learn programmatic interface
3. **Join Community**: Connect with other users
4. **Contribute**: Help improve the framework

---

### Happy Analyzing! 🧠✨

---
**Version**: 1.0
**Last Updated**: 2025-01-11
**See Also**: [Quick Start Guide](quick_start_guide.md), [Troubleshooting](troubleshooting.md)
