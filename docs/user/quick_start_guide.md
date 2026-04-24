# APGI Framework Quick Start Guide

## 🎯 Overview

This guide will help you get the APGI Framework running in minutes with minimal configuration. Perfect for new users who want to quickly experience the framework's capabilities.

## 📋 Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free disk space
- **Docker**: Docker Desktop installed and running

### Installing Docker Desktop

#### Windows

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Run the installer with administrator privileges
3. Restart your computer when prompted
4. Start Docker Desktop from the Start menu

#### macOS

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Open the downloaded .dmg file
3. Drag Docker to Applications folder
4. Launch Docker from Applications

#### Linux (Ubuntu/Debian)

```bash
# Update package index
sudo apt-get update

# Install dependencies
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER
```

## 🚀 One-Click Deployment

### Step 1: Download the Framework

```bash
# Clone the repository
git clone https://github.com/your-org/apgi-experiments.git
cd apgi-experiments
```

### Step 2: Run Quick Deploy

```bash
python quick_deploy.py
```

### Step 3: Follow the Interactive Setup

The script will guide you through:

1. **Environment Selection**
   - Choose `Development` for testing
   - Choose `Production` for real use

2. **Port Configuration**
   - Default port: 8000
   - Choose a different port if 8000 is in use

3. **Data Directory**
   - Default: `./data`
   - Choose where to store your experiment data

4. **Backup Settings**
   - Enable automatic backups (recommended)

### Step 4: Launch Complete

Once you see "✅ Deployment successful!", your APGI Framework is running!

## 🌐 Accessing Your Framework

### Web Interface

Open your web browser and navigate to:

```bash
http://localhost:8000
```

### Monitoring Dashboard

For real-time monitoring, access:

```bash
http://localhost:8000/monitoring
```

## 📊 First Experiment

### 1. Open the Web Interface

Navigate to `http://localhost:8000` in your browser.

### 2. Create New Experiment

1. Click "New Experiment" in the top menu
2. Enter experiment name: "My First APGI Test"
3. Select experiment type: "Parameter Estimation"
4. Click "Create"

### 3. Configure Parameters

1. **Ignition Threshold (θ₀)**: Start with 0.5
2. **Interoceptive Precision (Πᵢ)**: Start with 1.0
3. **Somatic Bias (β)**: Start with 0.0

### 4. Run Simulation

1. Click "Start Simulation"
2. Watch the real-time parameter estimates update
3. Monitor convergence in the plots

### 5. Analyze Results

```python
# Example analysis code
```

### 6. Export Data

```python
# Export to CSV
```

## 🔧 Common Commands

### Check Deployment Status

```bash
python quick_deploy.py status
```

### View Live Logs

```bash
python quick_deploy.py logs
```

### Stop the Framework

```bash
python quick_deploy.py stop
```

### Restart the Framework

```bash
python quick_deploy.py deploy
```

## 📁 Understanding the Directory Structure

```text
apgi-experiments/
├── data/                  # Your experiment data
├── apgi_outputs/          # Analysis results and outputs
├── session_state/         # Session save files
├── logs/                  # Application logs
├── backups/               # Automatic backups
├── docs/                  # Documentation
└── quick_deploy.py        # Deployment script
```

## 🎯 Next Steps

### Explore Features

- **Real-time Monitoring**: Access the monitoring dashboard
- **Parameter Estimation**: Try different parameter configurations
- **Data Analysis**: Explore the built-in analysis tools
- **Export Results**: Download and share your findings

### Advanced Configuration

For more advanced setup, see:

- [Deployment Guide](deployment.md)
- [Configuration Reference](configuration.md)
- [API Documentation](../api/index.md)

## ❓ Getting Help

### Built-in Help

```bash
python quick_deploy.py help
```

### Troubleshooting

```python
# Common issues
```

1. **Check Docker Status**: Ensure Docker Desktop is running
2. **Verify Port**: Make sure port 8000 is not in use
3. **Check Logs**: Run `python quick_deploy.py logs` for detailed error messages
4. **Restart**: Try stopping and restarting the deployment

### Support Resources

- **Troubleshooting Guide**: [troubleshooting.md](troubleshooting.md)
- **User Forum**: [Link to forum]
- **Documentation**: [docs/user/](index.md)

## 🎉 Congratulations

You've successfully deployed and started using the APGI Framework! You're now ready to:

- Run sophisticated parameter estimation experiments
- Monitor real-time data streams
- Analyze results with advanced Bayesian methods
- Export professional reports

Happy experimenting! 🧠✨
