#!/bin/bash

# APGI System Automated Setup Script
# This script sets up the entire APGI system environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    print_status "Checking Python version..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
    else
        print_error "Python $PYTHON_VERSION found but >= $REQUIRED_VERSION required"
        exit 1
    fi
}

# Function to create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing it..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
}

# Function to activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Function to upgrade pip
upgrade_pip() {
    print_status "Upgrading pip..."
    pip install --upgrade pip
    print_success "pip upgraded"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed from requirements.txt"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Function to check and install Homebrew (macOS)
install_homebrew() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command_exists brew; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            print_success "Homebrew installed"
        else
            print_success "Homebrew already installed"
        fi
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            print_status "Installing Redis and PostgreSQL via Homebrew..."
            brew install redis postgresql 2>/dev/null || {
                print_warning "Some system dependencies may already be installed"
            }
            print_success "System dependencies checked/installed"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            print_status "Installing Redis and PostgreSQL via apt..."
            sudo apt-get update
            sudo apt-get install -y redis-server postgresql postgresql-contrib
        elif command_exists yum; then
            print_status "Installing Redis and PostgreSQL via yum..."
            sudo yum install -y redis postgresql-server postgresql-contrib
        else
            print_warning "Unsupported package manager. Please install Redis and PostgreSQL manually."
        fi
    else
        print_warning "Unsupported OS. Please install Redis and PostgreSQL manually."
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up PostgreSQL database..."
    
    # Start PostgreSQL service
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql@14 2>/dev/null || brew services start postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start
    fi
    
    # Create database
    if command_exists psql; then
        createdb apgi_api 2>/dev/null && print_success "Database 'apgi_api' created" || \
            print_warning "Database 'apgi_api' may already exist"
    else
        print_warning "psql not found. Please create database manually."
    fi
}

# Function to setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    # Start Redis service
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis 2>/dev/null || sudo service redis-server start
    fi
    
    # Test Redis
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is running"
        else
            print_warning "Redis may not be running properly"
        fi
    else
        print_warning "redis-cli not found. Please verify Redis installation."
    fi
}

# Function to setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created from .env.example"
            
            # Update database URL for local installation
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' 's|postgresql://user:password@localhost:5432/apgi_api|postgresql://localhost:5432/apgi_api|' .env
            else
                sed -i 's|postgresql://user:password@localhost:5432/apgi_api|postgresql://localhost:5432/apgi_api|' .env
            fi
            print_success "Database URL updated for local installation"
        else
            print_warning ".env.example not found. Creating basic .env file..."
            cat > .env << EOF
# APGI REST API Configuration
API_TITLE="APGI System API"
API_VERSION="1.0.0"
HOST="0.0.0.0"
PORT=8000
RELOAD=true
DATABASE_URL="postgresql://localhost:5432/apgi_api"
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"
JWT_SECRET_KEY="your-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
LOG_LEVEL="INFO"
EOF
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Function to validate installation
validate_installation() {
    print_status "Validating installation..."
    
    # Check Python modules
    python3 -c "import numpy, scipy, matplotlib, fastapi, redis, sqlalchemy" 2>/dev/null && \
        print_success "Core Python modules imported successfully" || \
        print_error "Some Python modules failed to import"
    
    # Check services
    if command_exists redis-cli; then
        redis-cli ping >/dev/null 2>&1 && \
            print_success "Redis is responding" || \
            print_warning "Redis is not responding"
    fi
    
    if command_exists psql; then
        psql -d apgi_api -c "SELECT 1;" >/dev/null 2>&1 && \
            print_success "PostgreSQL database is accessible" || \
            print_warning "PostgreSQL database is not accessible"
    fi
    
    # Check if GUI can be imported
    python3 -c "import tkinter" 2>/dev/null && \
        print_success "GUI library (tkinter) is available" || \
        print_warning "GUI library (tkinter) is not available"
}

# Function to show next steps
show_next_steps() {
    print_success "Setup completed successfully!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo
    echo "2. Run the GUI application:"
    echo "   python apgi_gui.py"
    echo
    echo "3. Or start the API server:"
    echo "   python api/main.py"
    echo
    echo "4. For more information, see the documentation:"
    echo "   - QUICKSTART_GUI.txt"
    echo "   - docs/api/API_SETUP_GUIDE.md"
    echo
    echo -e "${YELLOW}Note:${NC} Make sure Redis and PostgreSQL services are running before starting the application."
}

# Main setup function
main() {
    echo -e "${BLUE}APGI System Automated Setup${NC}"
    echo "==============================="
    echo
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found. Please run this script from the APGI system root directory."
        exit 1
    fi
    
    # Run setup steps
    check_python
    create_venv
    activate_venv
    upgrade_pip
    install_dependencies
    install_homebrew
    install_system_deps
    setup_database
    setup_redis
    setup_env
    validate_installation
    show_next_steps
}

# Run main function
main "$@"
