# Database Directory Structure

This directory contains all database-related files for the FutureQuant Trader application.

## Structure

```
databases/
├── futurequant_trader.db    # Main SQLite database file
├── backups/                 # Database backup files
├── migrations/              # Database migration scripts
├── schemas/                 # Database schema definitions
└── README.md               # This file
```

## Files

- **futurequant_trader.db**: Main SQLite database containing trading data, models, and application state
- **backups/**: Directory for storing database backups (automated or manual)
- **migrations/**: Database schema migration scripts for version control
- **schemas/**: Database schema definitions and documentation

## Usage

- The main database file is automatically managed by the application
- Backups should be created regularly before major updates
- Migrations should be run when updating the database schema
- Schema files document the current database structure

## Backup Recommendations

- Create daily automated backups
- Store backups in the `backups/` directory with timestamp naming
- Consider external backup storage for critical data
