        CREATE TABLE IF NOT EXISTS change_rates (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            rate_date DATE NOT NULL,

            currency TEXT NOT NULL,

            rate_time TEXT,

            job_date DATE NOT NULL,

            rate_buy REAL,
            rate_sell REAL,
            variance REAL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(rate_date, currency)
        ) ;