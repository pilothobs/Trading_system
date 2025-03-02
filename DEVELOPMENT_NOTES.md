# Trading System Development Notes

This document tracks the development progress, key decisions, and structure of the trading system project. Use it as a reference when switching between development environments.

## Project Structure

```
trading_system/
├── agents/                 # Trading agents and strategies
│   ├── backtesting.py      # Backtesting framework
│   ├── ml_strategy_agent.py # ML-based trading strategy
│   ├── test_agent.py       # Test agent for resource usage simulation
│   ├── crew_agents.py      # Multi-agent trading system
│   └── prim_gpt.py         # GPT-based trading agent
├── tools/                  # Utility tools
│   ├── monitoring/         # Resource monitoring tools
│   │   ├── resource_monitor.py    # Monitors CPU and RAM usage
│   │   ├── analyze_resources.py   # Analyzes resource usage logs
│   │   ├── test_resource_usage.py # Tests resource usage of agents
│   │   └── README.md              # Documentation for monitoring tools
│   └── backup/             # Backup tools
│       ├── backup_to_s3.py        # Backs up to AWS S3
│       ├── schedule_s3_backup.py  # Schedules automatic S3 backups
│       ├── aws_config.py          # AWS configuration settings
│       ├── configure_aws_cli.py   # Configures AWS CLI with credentials
│       └── README.md              # Documentation for AWS S3 backup
├── logs/                   # Log files and analysis results
│   ├── resource_usage_*.log       # Resource monitoring logs
│   ├── resource_usage_*_plot.png  # Resource usage plots
│   └── resource_usage_*_summary.txt # Resource usage summaries
├── venv/                   # Python virtual environment (not tracked in Git)
├── DEVELOPMENT_NOTES.md    # Development notes and progress tracking
└── .gitignore              # Git ignore file
```

## Development Timeline

### Initial Setup
- Set up project structure and Git repository
- Created virtual environment for Python dependencies
- Configured `.gitignore` to exclude sensitive files and virtual environment

### Trading Agents Development
- Implemented basic trading agent framework
- Added backtesting capabilities
- Integrated machine learning strategy agent
- Created test agent for resource usage simulation

### Resource Monitoring System
- Developed resource monitoring tools to track CPU and memory usage
- Created analysis scripts to evaluate resource requirements
- Tested with high CPU intensity to evaluate performance
- Reorganized monitoring tools into dedicated directory structure

### Backup System
- Implemented AWS S3 backup functionality for cloud storage
- Created AWS CLI configuration tools for easier setup
- Implemented test backup feature for quick verification
- Documented backup procedures and configuration

## Key Decisions

### Project Organization
- Separated trading logic (agents) from utility tools
- Created dedicated monitoring tools in `tools/monitoring/`
- Added backup tools in `tools/backup/`
- Centralized logging in the `logs/` directory

### Git Management
- Excluded sensitive files and virtual environment from Git tracking
- Configured remote repository at GitHub: https://github.com/pilothobs/Trading_system

### Resource Management
- Implemented monitoring to track resource usage during trading
- Analysis showed current CPU and memory usage is acceptable
- Will continue monitoring as more agents are added to determine if GPU acceleration is needed

### Backup Strategy
- Primary backup to GitHub repository for code
- Secondary backup to AWS S3 for cloud-based redundancy
- Automated backups triggered by changes or on a schedule
- Retention policy to manage backup storage efficiently
- Sensitive files (like .env with API keys) are explicitly included in backups
- Test backup feature allows quick verification of backup functionality

## Usage Examples

### Running Resource Monitoring

```bash
# Run a test agent with high CPU usage
python agents/test_agent.py --cpu 100 --memory 1200 --duration 60 &

# Monitor Python processes
python tools/monitoring/resource_monitor.py --python-only --interval 2 --duration 60

# Analyze the results
python tools/monitoring/analyze_resources.py --latest
```

### Running Backtesting

```bash
# Run backtesting on a strategy
python agents/backtesting.py
```

### Backing Up the Project

```bash
# Manual backup to AWS S3
python tools/backup/backup_to_s3.py

# Create a smaller test backup to AWS S3
python tools/backup/backup_to_s3.py --test

# Set up automatic AWS S3 backups (runs in background)
python tools/backup/schedule_s3_backup.py --interval 60 --daemon

# Configure AWS CLI with credentials from aws_config.py
python tools/backup/configure_aws_cli.py
```

## Next Steps

- Refine backtesting agent for improved performance
- Implement additional trading strategies
- Enhance monitoring for multi-agent scenarios
- Evaluate GPU acceleration for machine learning models if needed
- Set up automated backup verification and reporting

## Notes on Development Environment

- Project is hosted on a VPS accessible via SSH
- Development occurs across multiple devices
- This document helps maintain continuity between development sessions
- Multiple backup strategies ensure project safety:
  - GitHub for code version control
  - AWS S3 for cloud-based redundancy 