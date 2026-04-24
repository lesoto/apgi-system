# APGI Framework Tutorials

## Tutorial 1: Getting Started with Your First Experiment

### Tutorial 1 Learning Objective

Learn to set up and run a basic detection task experiment from start to finish.

### Tutorial 1 Requirements

- APGI Framework installed
- Basic understanding of experimental psychology concepts
- 15 minutes of time

### Step 1: Launch the Application

1. __Start the APGI Framework__

   ```bash
   python GUI-Launcher.py
   ```

2. __Choose Your Experience Level__

   - Beginner: Recommended for first-time users
   - Intermediate: Some familiarity with similar software
   - Advanced: Skip basic tutorials

3. __Complete the Welcome Wizard__

   - Set your preferred data directory
   - Choose default experiment settings
   - Enable auto-save (recommended)

### Step 2: Create a New Experiment

1. __File → New Experiment__
2. __Select Experiment Type__: Detection Task
3. __Basic Configuration__:

   ```text
   Participant ID: P001
   Session ID: S001
   Number of Trials: 50
   Modality: Visual
   ```

4. __Advanced Settings__ (for now, keep defaults):

   - Stimulus intensity range: 0.01 - 1.0
   - Trial duration: 500ms
   - Response window: 2000ms

### Step 3: Run the Experiment

1. __Click "Start Experiment"__
2. __Read Instructions__ carefully
3. __Practice Trial__ (optional but recommended)
4. __Main Experiment__:
   - Focus on the center of the screen
   - Press SPACEBAR when you see a stimulus
   - Try to be as accurate as possible
   - Don't worry about speed

5. __Complete All Trials__ (approximately 5-10 minutes)

### Step 4: Review Results

1. __Automatic Analysis__: Results appear immediately
2. __Key Metrics to Understand__:
   - __Threshold__: ~0.25 (stimulus intensity at 50% detection)
   - __Confidence__: ±0.05 (statistical uncertainty)
   - __Hit Rate__: ~50% (expected for threshold task)
   - __Mean RT__: ~600ms (typical response time)

3. __Save Results__: File → Save As → "P001_Detection_001.json"

### What You Learned - Tutorial 1

- How to create and configure an experiment
- How to run a detection task
- How to interpret basic results
- How to save and organize data

---

## Tutorial 2: Data Analysis and Visualization

### Tutorial 2 Learning Objective

Learn to analyze experimental data and create meaningful visualizations.

### Tutorial 2 Requirements

- Completed Tutorial 1
- Have experimental data available
- 20 minutes of time

### Step 1: Import Your Data

1. __File → Open__ → Select your experiment file
2. __Switch to Analysis Tab__
3. __Data Import Options__:
   - Auto-detect columns (recommended)
   - Preview data before import
   - Handle missing values

### Step 2: Basic Statistical Analysis

1. __Descriptive Statistics__:
   - Click "Analyze → Descriptive Statistics"
   - Select variables: Response Time, Accuracy
   - View results: Mean, SD, Min, Max

2. __Response Time Analysis__:
   - __Analyze → Response Times__
   - __Distribution__: Histogram with normal curve overlay
   - __Outliers__: Box plot with outlier detection
   - __Summary__: Mean, median, IQR

3. __Accuracy Analysis__:
   - __Analyze → Accuracy__
   - __Hit Rate__: Percentage of correct detections
   - __Signal Detection__: d' and criterion calculations
   - __Confidence__: Metacognitive awareness

### Step 3: Create Visualizations

1. __Psychometric Curve__:
   - __Visualization → Psychometric Function__
   - X-axis: Stimulus intensity
   - Y-axis: Detection probability
   - __Fit__: Logistic function with confidence intervals

2. __Response Time Distribution__:
   - __Visualization → Response Times__
   - __Plot Type__: Histogram + density curve
   - __Color__: Blue for correct, red for incorrect
   - __Labels__: Add mean and median lines

3. __Learning Curve__:
   - __Visualization → Learning__
   - __X-axis__: Trial number
   - __Y-axis__: Response time or accuracy
   - __Smoothing__: Moving average (window=10)

### Step 4: Export Your Results

1. __Figures__:
   - Right-click any plot → Export
   - __Format__: PNG (600 DPI) for publications
   - __Naming__: Auto-generated with timestamp

2. __Data Tables__:
   - __File → Export Results__
   - __Format__: CSV for Excel/SPSS
   - __Content__: All analysis results

### What You Learned - Tutorial 2

- How to import and validate experimental data
- How to perform basic statistical analyses
- How to create publication-ready visualizations
- How to export results for further analysis

---

## Tutorial 3: Heartbeat Detection Task

### Tutorial 3 Learning Objective

Learn to set up and run an interoceptive awareness experiment.

### Tutorial 3 Requirements

- Completed Tutorials 1-2
- Heart rate sensor (optional, can use simulation)
- 25 minutes of time

### Step 1: Equipment Setup

1. __Heartbeat Sensor__ (if available):
   - Connect sensor to USB port
   - Test signal quality
   - Verify R-peak detection

2. __Simulation Mode__ (if no sensor):
   - __Settings → Simulation Mode__
   - __Heart Rate__: 70 BPM (default)
   - __Variability__: 10% (realistic)

### Step 2: Configure Heartbeat Detection

1. __File → New Experiment__
2. __Select__: Heartbeat Detection Task
3. __Basic Settings__:

   ```text
   Participant ID: P001
   Number of Trials: 60
   Asynchrony Window: 300ms
   Confidence Rating: 1-5 scale
   ```

4. __Advanced Settings__:
   - __Synchronous Trials__: 50%
   - __Asynchronous Range__: 200-400ms
   - __Tone Parameters__: 1000Hz, 50ms duration
   - __Response Window__: 3000ms

### Step 3: Calibration

1. __Run Calibration__ (automatic):
   - Detect resting heart rate
   - Test tone synchronization
   - Adjust volume levels

2. __Practice Trials__:
   - 5 synchronous trials
   - 5 asynchronous trials
   - Get familiar with the task

### Step 4: Main Experiment

1. __Task Instructions__:
   - "Listen for tones and judge if they occur with your heartbeat"
   - "Rate your confidence in each judgment"
   - "Respond as quickly and accurately as possible"

2. __Trial Structure__:

   ```text
   1. Wait for tone (2-5 seconds)
   2. Hear tone (synchronous or asynchronous)
   3. Make judgment (Sync/Async)
   4. Rate confidence (1-5)
   5. Inter-trial interval (1-2 seconds)
   ```

3. __Monitoring__:
   - Real-time heartbeat display
   - Response accuracy tracking
   - Confidence rating distribution

### Step 5: Analyze Results

1. __Signal Detection Analysis__:
   - __d' (d-prime)__: Sensitivity to heartbeat synchrony
   - __Criterion__: Response bias
   - __Hit Rate__: Correct synchronous detection
   - __False Alarm Rate__: Incorrect synchronous responses

2. __Metacognitive Analysis__:
   - __Confidence-Accuracy Correlation__: Metacognitive awareness
   - __Type 2 ROC__: Metacognitive sensitivity
   - __Calibration__: Confidence accuracy

3. __Physiological Correlates__:
   - __Heart Rate Variability__: During task performance
   - __Pupil Dilation__: Cognitive load indicators
   - __Response Times__: Decision processes

### Expected Results

- __d' Range__: 0.5 - 2.0 (individual differences)
- __Criterion__: Slightly conservative (negative values)
- __Confidence-Accuracy Correlation__: 0.2 - 0.6
- __Mean Response Time__: 800-1200ms

### What You Learned - Tutorial 3

- How to set up physiological monitoring
- How to design interoceptive awareness experiments
- How to analyze signal detection data
- How to assess metacognitive awareness

---

## Tutorial 4: Advanced Analysis with Bayesian Methods

### Tutorial 4 Learning Objective

Learn to use Bayesian parameter estimation for more sophisticated analysis.

### Tutorial 4 Requirements

- Completed Tutorials 1-3
- Basic understanding of Bayesian statistics
- 30 minutes of time

### Step 1: Bayesian Parameter Estimation

1. __Load Multiple Sessions__:
   - __File → Import Multiple__
   - Select 3-5 sessions from same participant
   - __Merge__: Combine data for hierarchical analysis

2. __Configure Bayesian Analysis__:
   - __Analysis → Bayesian Methods__
   - __Model__: Hierarchical psychometric function
   - __Priors__: Weakly informative (default)
   - __Sampling__: MCMC with 10,000 samples

3. __Run Analysis__:
   - __Convergence Check__: Gelman-Rubin statistic
   - __Effective Sample Size__: >1000 per parameter
   - __Trace Plots__: Visual inspection

### Step 2: Model Comparison

1. __Alternative Models__:
   - __Model 1__: Standard psychometric function
   - __Model 2__: Lapse rate included
   - __Model 3__: Individual differences

2. __Model Evidence__:
   - __WAIC__: Watanabe-Akaike Information Criterion
   - __LOO__: Leave-one-out cross-validation
   - __Bayes Factors__: Model comparison

3. __Model Averaging__:
   - __Weighted Average__: Based on model evidence
   - __Parameter Estimates__: Model-averaged posteriors
   - __Uncertainty__: Incorporates model uncertainty

### Step 3: Predictive Analysis

1. __Posterior Predictive Checks__:
   - __Simulate Data__: From posterior distributions
   - __Compare__: Simulated vs. observed data
   - __Assess__: Model fit and adequacy

2. __Cross-Validation__:
   - __Leave-One-Out__: Predict held-out sessions
   - __Performance Metrics__: Predictive accuracy
   - __Generalization__: To new conditions

### Step 4: Advanced Visualizations

1. __Posterior Distributions__:
   - __Density Plots__: Parameter posteriors
   - __Credible Intervals__: 95% highest density
   - __Trace Plots__: MCMC convergence

2. __Model Comparison Plots__:
   - __WAIC Comparison__: Model ranking
   - __Bayes Factors__: Evidence strength
   - __Posterior Predictives__: Model fits

3. __Hierarchical Results__:
   - __Individual Parameters__: Participant-level
   - __Group Parameters__: Population-level
   - __Shrinkage__: Individual to group

### What You Learned - Tutorial 4

- How to implement Bayesian parameter estimation
- How to compare competing models
- How to assess model fit and predictive validity
- How to visualize Bayesian analysis results

---

## Tutorial 5: Real-time Monitoring and Live Experiments

### Tutorial 5 Learning Objective

Learn to set up real-time monitoring for live experiment tracking.

### Tutorial 5 Requirements

- Completed previous tutorials
- Multiple monitors (recommended)
- 20 minutes of time

### Step 1: Set Up Monitoring Dashboard

1. __Tools → Real-time Monitoring__
2. __Configure Dashboard Layout__:
   - __Panel 1__: Live EEG signal
   - __Panel 2__: Response times
   - __Panel 3__: Accuracy tracking
   - __Panel 4__: System resources

3. __Update Settings__:
   - __Refresh Rate__: 10 Hz (default)
   - __Buffer Size__: 1000 samples
   - __Alerts__: Enable threshold alerts

### Step 2: Configure Live Data Streams

1. __EEG Monitoring__:
   - __Device Selection__: Choose EEG device
   - __Channel Configuration__: 8-channel setup
   - __Filter Settings__: 1-40 Hz bandpass
   - __Artifact Detection__: Automatic rejection

2. __Behavioral Tracking__:
   - __Response Collection__: Real-time logging
   - __Performance Metrics__: Online calculation
   - __Adaptive Parameters__: Dynamic adjustment

3. __System Monitoring__:
   - __CPU Usage__: Resource tracking
   - __Memory Usage__: RAM monitoring
   - __Disk Space__: Storage availability
   - __Network Status__: Connection health

### Step 3: Run Live Experiment

1. __Start Monitoring__:
   - __Begin Recording__: All data streams
   - __Check Signals__: Verify data quality
   - __Test Alerts__: Confirm notification system

2. __Launch Experiment__:
   - __File → New Experiment__
   - __Enable Live Mode__: Real-time analysis
   - __Start Task__: Begin data collection

3. __Monitor Progress__:
   - __Signal Quality__: EEG amplitude and noise
   - __Performance__: Online accuracy and RT
   - __System Health__: Resource utilization
   - __Alerts__: Automatic notifications

### Step 4: Real-time Analysis

1. __Online Processing__:
   - __Feature Extraction__: Real-time EEG features
   - __Classification__: Online pattern detection
   - __Adaptive Staircase__: Dynamic parameter adjustment

2. __Quality Control__:
   - __Artifact Detection__: Automatic bad trial detection
   - __Signal Quality__: Online quality metrics
   - __Data Integrity__: Continuous validation

3. __Intervention Rules__:
   - __Threshold Alerts__: Performance degradation
   - __System Alerts__: Resource exhaustion
   - __Data Alerts__: Quality issues

### Step 5: Export and Analysis

1. __Live Data Export__:
   - __Continuous Export__: Real-time data saving
   - __Backup System__: Automatic redundancy
   - __Compression__: Efficient storage

2. __Post-Experiment Analysis__:
   - __Quality Metrics__: Data quality assessment
   - __Performance Summary__: Live vs. offline analysis
   - __System Optimization__: Resource usage analysis

### What You Learned - Tutorial 5

- How to set up real-time monitoring
- How to configure live data streams
- How to run experiments with live feedback
- How to implement quality control systems

---

## Tutorial 6: Batch Processing and Automation

### Tutorial 6 Learning Objective

Learn to automate experiment processing for large datasets.

### Tutorial 6 Requirements

- Completed previous tutorials
- Multiple experiment files
- 25 minutes of time

### Step 1: Set Up Batch Processing

1. __Tools → Batch Processing__
2. __Select Files__:
   - __Directory__: Choose experiment folder
   - __File Pattern__: *.json (experiment files)
   - __Recursive__: Include subdirectories

3. __Configure Pipeline__:
   - __Step 1__: Data validation
   - __Step 2__: Preprocessing
   - __Step 3__: Analysis
   - __Step 4__: Visualization
   - __Step 5__: Export

### Step 2: Define Processing Rules

1. __Data Validation__:
   - __Required Fields__: Participant ID, session, responses
   - __Data Types__: Numeric, categorical, temporal
   - __Quality Checks__: Missing values, outliers

2. __Preprocessing Rules__:
   - __Response Time Filtering__: 200-3000ms
   - __Accuracy Thresholds__: Minimum performance
   - __Artifact Rejection__: EEG quality criteria

3. __Analysis Parameters__:
   - __Statistical Tests__: Pre-specified analyses
   - __Model Selection__: Automatic model comparison
   - __Correction Methods__: Multiple comparison correction

### Step 3: Execute Batch Processing

1. __Start Processing__:
   - __Parallel Processing__: Use multiple cores
   - __Progress Tracking__: Real-time updates
   - __Error Handling__: Continue on errors

2. __Monitor Progress__:
   - __Current File__: Processing status
   - __Completion Rate__: Percentage done
   - __Time Estimate__: Remaining time
   - __Error Log__: Processing issues

### Step 4: Review Batch Results

1. __Summary Report__:
   - __Files Processed__: Total and successful
   - __Error Summary__: Types and frequencies
   - __Quality Metrics__: Data quality assessment

2. __Aggregate Analysis__:
   - __Group Statistics__: Across all participants
   - __Individual Results__: Participant-level summaries
   - __Comparative Analysis__: Between-group comparisons

3. __Export Options__:
   - __CSV Files__: Spreadsheet format
   - __JSON Data__: Structured format
   - __PDF Reports__: Summary documents
   - __Database__: Direct database import

### Step 5: Automation Scripting

1. __Create Script__:

   ```python
   # Example batch processing script
   from apgi_framework import BatchProcessor
   
   processor = BatchProcessor()
   processor.add_directory('experiments/')
   processor.set_analysis_pipeline(['validation', 'analysis', 'export'])
   processor.run_parallel(cores=4)
   ```

2. __Schedule Automation__:
   - __Daily Processing__: Automatic data processing
   - __Weekly Reports__: Summary generation
   - __Monthly Backup__: Data archiving

### What You Learned - Tutorial 6

- How to set up batch processing pipelines
- How to define processing rules and validation
- How to monitor and manage large-scale processing
- How to automate repetitive analysis tasks

---

## Quick Reference Cheat Sheet

### Keyboard Shortcuts

- __Ctrl+N__: New experiment
- __Ctrl+O__: Open file
- __Ctrl+S__: Save
- __Ctrl+Shift+S__: Save As
- __Ctrl+Z__: Undo
- __Ctrl+Y__: Redo
- __Ctrl+F__: Find
- __Ctrl+H__: Replace
- __F5__: Run experiment
- __F1__: Help
- __Esc__: Stop current operation

### Common Workflows

#### Quick Experiment Setup

1. File → New → Detection Task
2. Enter Participant ID
3. Set Trials = 50
4. Click Start

#### Data Analysis

1. File → Open → Select data
2. Analysis Tab → Descriptive Statistics
3. Visualization → Psychometric Curve
4. File → Export Results

#### Batch Processing

1. Tools → Batch Processing
2. Select directory
3. Configure pipeline
4. Click Run

### Troubleshooting Quick Fixes

|Problem|Solution|
|-------|---------|
|GUI not responding|Check memory usage, close other apps|
|Can't import data|Verify file format and permissions|
|Experiment crashes|Reduce trial count, check sensors|
|Slow analysis|Enable parallel processing|

### Default Settings

|Parameter|Default|Recommended Range|
|---------|-------|-----------------|
|Trials|100|50-200|
|Response Window|2000ms|1000-3000ms|
|Stimulus Duration|500ms|100-1000ms|
|Inter-trial Interval|1000ms|500-2000ms|

---

__Congratulations!__ You've completed the APGI Framework tutorial series.

You now have the skills to:

- Design and run sophisticated experiments
- Analyze data using advanced statistical methods
- Create professional visualizations
- Automate large-scale data processing
- Monitor experiments in real-time

For additional help and resources:

- __Documentation__: `docs/` directory
- __Community Forum__: <https://forum.apgi-framework.org>
- __Video Tutorials__: <https://youtube.com/apgi-framework>
- __Support__: <support@apgi-framework.org>
