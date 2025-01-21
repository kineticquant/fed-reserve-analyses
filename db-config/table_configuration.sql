-- System Configuration:
CREATE TABLE IF NOT EXISTS SYS_CONF (
IS_ALIVE VARCHAR(20) DEFAULT 'N' , 
APP_ENV_NAME	VARCHAR(100) DEFAULT 'UNKNOWN'
);

-- Overarching Engine Configuration:
CREATE TABLE IF NOT EXISTS ENGINES (
id SERIAL PRIMARY KEY, -- Auto-generating unique PK INT
engine VARCHAR(80), 
status	VARCHAR(25) DEFAULT 'OFF',
last_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE engines
ADD CONSTRAINT unique_engine UNIQUE (engine);

ALTER TABLE engines
ADD COLUMN description TEXT,
ADD COLUMN planned_schedule VARCHAR(255);

ALTER TABLE engines
ADD COLUMN enabled VARCHAR(20) DEFAULT 'NO';

ALTER TABLE engines
ADD COLUMN time_since_last_run INTERVAL;

alter table engines
add column source varchar(50),
add column target varchar(50);

-- Start Application Configuration
CREATE TABLE if not exists users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(250) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
	ip_addr VARCHAR(255),
	last_login TIMESTAMP,
	banned_yn VARCHAR(5) DEFAULT 'N',
	first_name VARCHAR(50),
	last_name VARCHAR(50),
	premium_yn VARCHAR(5) DEFAULT 'N',
	addr_1 VARCHAR(250),
	addr_2 VARCHAR(250),
	addr_3 VARCHAR(250),
	city VARCHAR(200),
	state VARCHAR(40),
	country VARCHAR(40),
	metadata1 TEXT,
	metadata2 TEXT,
	metadata3 TEXT,
	metadata4 TEXT,
	metadata5 TEXT
);


CREATE TABLE IF NOT EXISTS app_navbar (
--VIX + future VIX, DJI, S&P, Nasdaq, Russell 2k, SPY, QQQ, BTC, ETH, US OIL, Gold, International/currencies?
--Could put these all in a table on the home page too
TICKER VARCHAR(50),
LAST VARCHAR(50),
CHG VARCHAR(50),
CHG_PCT VARCHAR(50),
VISIBLE_YN VARCHAR(50) DEFAULT 'Y'
);

CREATE TABLE IF NOT EXISTS app_announcement (
    announcement_text_1 TEXT,
    announcement_text_2 TEXT,
    announcement_text_3 TEXT
);

CREATE TABLE IF NOT EXISTS app_release_notes (
    release_notes TEXT,
    version_notes TEXT,
    release_category TEXT,
    category_xplain TEXT DEFAULT 'categories are New Components, UI Enhancements, Bug Fixes'
    );

CREATE TABLE IF NOT EXISTS app_home_page (
--Top Gainers, Top Losers, Most Active
--Setting as Varchar so integration doesn't fail over character mismatch types
TICKER VARCHAR(50),
LAST VARCHAR(50),
CHG VARCHAR(50),
CHG_PCT VARCHAR(50),
VISIBLE_YN VARCHAR(50) DEFAULT 'Y'
);

ALTER TABLE app_home_page
ADD CONSTRAINT unique_ticker UNIQUE (TICKER);

ALTER TABLE app_home_page
ADD COLUMN "1M_PRICE" VARCHAR(50),
ADD COLUMN "1M_PCT" VARCHAR(50),
ADD COLUMN "3M_PRICE" VARCHAR(50),
ADD COLUMN "3M_PCT" VARCHAR(50),
ADD COLUMN "6M_PRICE" VARCHAR(50),
ADD COLUMN "6M_PCT" VARCHAR(50),
ADD COLUMN "1Y_PRICE" VARCHAR(50),
ADD COLUMN "1Y_PCT" VARCHAR(50),
ADD COLUMN "18M_PRICE" VARCHAR(50),
ADD COLUMN "18M_PCT" VARCHAR(50),
ADD COLUMN "2Y_PRICE" VARCHAR(50),
ADD COLUMN "2Y_PCT" VARCHAR(50);

ALTER TABLE app_home_page
ADD COLUMN "1W_PRICE" VARCHAR(50),
ADD COLUMN "1W_PCT" VARCHAR(50),
ADD COLUMN "YTD_PRICE" VARCHAR(50),
ADD COLUMN "YTD_PCT" VARCHAR(50);


-- End Application Configuration

----------------------------------------------------------------
-- Inserting configured engines into the engines table. 
-- Modify defaults here if desired.
delete from engines;

insert into engines (engine, status, description, planned_schedule, enabled)
values ('initEngine', 'OFF','Monitors the status of all other engines.','Infinite','YES');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('unemployment', 'OFF','Reads all unemployment data for USA from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('employment', 'OFF','Reads all full-time and part-time data for USA from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('house_prices', 'OFF','Reads all house prices in dollars from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('business_inventories', 'OFF','Very large engine that reads all business inventory data from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('gdp', 'OFF','Very large engine that reads all GDP and Real GDP data from FRED API.','Weekly','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('cpi', 'OFF','Very large engine that reads all GDP and Real GDP data from FRED API.','Weekly','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('s&p500', 'OFF','Reads S&P500 data from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('dji', 'OFF','Reads Down Jones Industrial Average from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('house_state_idx', 'OFF','Reads house prices by state from FRED API.','Daily','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('export_president_pcnt_fed_debt_to_gdp', 'OFF','Reads presidents from federal_debt_gdp and gets total percent by each president to export as JSON.','Monthly','NO');

insert into engines (engine, status, description, planned_schedule, enabled)
values ('yfinance_main', 'OFF','Reads macro stock market details from Yahoo Finance.','NRT','NO');


insert into engines (engine, status, description, planned_schedule, enabled)
values ('data_cleanup', 'OFF','Removes old or stale data from various tables.','Daily','NO');

--



----------------------------------------------------------------

-- Unique Engine Endpoint Configuration:
CREATE TABLE IF NOT EXISTS WATCHLIST (
ticker VARCHAR(20) PRIMARY KEY, 
status	VARCHAR(25),
last_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
open VARCHAR(35),
close VARCHAR(35),
percent_chg VARCHAR(35),
date VARCHAR(50) -- May return to adj. to date dynamically, but lot of date formats are inconsistent
    -- Can handle in Python plotting / front-end alternatively
);

CREATE TABLE IF NOT EXISTS unemployment_data (
            Date DATE PRIMARY KEY,
            Unemployment_Rate FLOAT,
			when_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

CREATE TABLE IF NOT EXISTS employment_jobs (
    --id SERIAL PRIMARY KEY, -- Auto-generating unique PK INT
    Date DATE NOT NULL,
    Job_Type VARCHAR(50) NOT NULL, -- 'full_time' or 'part_time'
    Job_Count INTEGER,
    when_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (Date, Job_Type) -- Ensure unique entries per date and job type
);

ALTER TABLE employment_jobs
        ADD COLUMN IF NOT EXISTS monthly_difference INTEGER;

CREATE TABLE IF NOT EXISTS house_prices (
    Date DATE PRIMARY KEY,
    House_Price NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

ALTER TABLE house_prices
RENAME COLUMN house_price TO median_house_price;

ALTER TABLE house_prices
ADD COLUMN avg_house_price NUMERIC;


-- Business Inventories (large integration engine)
CREATE TABLE total_business_inventories (
    Date DATE PRIMARY KEY,
    total_business_inventories NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE inventories_to_sales_ratio (
    Date DATE PRIMARY KEY,
    inventories_to_sales_ratio NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE retailers_inventories_to_sales_ratio (
    Date DATE PRIMARY KEY,
    retailers_inventories_to_sales_ratio NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE manufacturers_inventories_to_sales_ratio (
    Date DATE PRIMARY KEY,
    manufacturers_inventories_to_sales_ratio NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE wholesalers_inventories_to_sales_ratio (
    Date DATE PRIMARY KEY,
    wholesalers_inventories_to_sales_ratio NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE auto_inventory_to_sales_ratio (
    Date DATE PRIMARY KEY,
    auto_inventory_to_sales_ratio NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE total_business_sales (
    Date DATE PRIMARY KEY,
    total_business_sales NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

CREATE TABLE retailer_inventories (
    Date DATE PRIMARY KEY,
    retailer_inventories NUMERIC,
    Quarter VARCHAR(7),
    when_updated TIMESTAMP
);

-- End Business Inventories

-- GDP Engine
CREATE TABLE gross_domestic_product (
    Date DATE PRIMARY KEY,
    gross_domestic_product NUMERIC,
    Quarter VARCHAR(10),
    Year INTEGER,
    when_updated TIMESTAMP
);

CREATE TABLE gross_national_product (
    Date DATE PRIMARY KEY,
    gross_national_product NUMERIC,
    Quarter VARCHAR(10),
    Year INTEGER,
    when_updated TIMESTAMP
);

CREATE TABLE real_gross_domestic_product (
    Date DATE PRIMARY KEY,
    real_gross_domestic_product NUMERIC,
    Quarter VARCHAR(10),
    Year INTEGER,
    when_updated TIMESTAMP
);

CREATE TABLE gdp_per_capita (
    Date DATE PRIMARY KEY,
    gdp_per_capita NUMERIC,
    Quarter VARCHAR(10),
    Year INTEGER,
    when_updated TIMESTAMP
);

CREATE TABLE real_gdp_per_capita (
    Date DATE PRIMARY KEY,
    real_gdp_per_capita NUMERIC,
    Quarter VARCHAR(10),
    Year INTEGER,
    when_updated TIMESTAMP
);

CREATE TABLE real_gdp_growth (
    Date DATE PRIMARY KEY,
    Real_GDP_Growth_Quarterly NUMERIC,
    Real_GDP_Growth_Annual NUMERIC,
    when_updated TIMESTAMP
);

-- End of GDP

-- Financial Markets

CREATE TABLE sp500 (
    Date DATE PRIMARY KEY,
    SP500 NUMERIC,
    Quarter VARCHAR(10),
    when_updated TIMESTAMP
);

CREATE TABLE dji (
    Date DATE PRIMARY KEY,
    DJI NUMERIC,
    Quarter VARCHAR(10),
    when_updated TIMESTAMP
);

-- Inflation

CREATE TABLE cpi (
    Date DATE PRIMARY KEY,
    CPI NUMERIC,
    Quarter TEXT,
    when_updated TIMESTAMP
);

alter table cpi
add inflation_rate NUMERIC;

-- Presidents:
CREATE TABLE presidential_terms (
    president_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (president_name, start_date)
);

INSERT INTO presidential_terms (president_name, start_date, end_date) VALUES
('George Washington', '1789-04-30', '1797-03-04'),
('John Adams', '1797-03-04', '1801-03-04'),
('Thomas Jefferson', '1801-03-04', '1809-03-04'),
('James Madison', '1809-03-04', '1817-03-04'),
('James Monroe', '1817-03-04', '1825-03-04'),
('John Quincy Adams', '1825-03-04', '1829-03-04'),
('Andrew Jackson', '1829-03-04', '1837-03-04'),
('Martin Van Buren', '1837-03-04', '1841-03-04'),
('William Henry Harrison', '1841-03-04', '1841-04-04'),
('John Tyler', '1841-04-04', '1845-03-04'),
('James K. Polk', '1845-03-04', '1849-03-04'),
('Zachary Taylor', '1849-03-04', '1850-07-09'),
('Millard Fillmore', '1850-07-09', '1853-03-04'),
('Franklin Pierce', '1853-03-04', '1857-03-04'),
('James Buchanan', '1857-03-04', '1861-03-04'),
('Abraham Lincoln', '1861-03-04', '1865-04-15'),
('Andrew Johnson', '1865-04-15', '1869-03-04'),
('Ulysses S. Grant', '1869-03-04', '1877-03-04'),
('Rutherford B. Hayes', '1877-03-04', '1881-03-04'),
('James A. Garfield', '1881-03-04', '1881-09-19'),
('Chester A. Arthur', '1881-09-19', '1885-03-04'),
('Grover Cleveland', '1885-03-04', '1889-03-04'),
('Benjamin Harrison', '1889-03-04', '1893-03-04'),
('Grover Cleveland', '1893-03-04', '1897-03-04'),
('William McKinley', '1897-03-04', '1901-09-06'),
('Theodore Roosevelt', '1901-09-06', '1909-03-04'),
('William Howard Taft', '1909-03-04', '1913-03-04'),
('Woodrow Wilson', '1913-03-04', '1921-03-04'),
('Warren G. Harding', '1921-03-04', '1923-08-02'),
('Calvin Coolidge', '1923-08-02', '1929-03-04'),
('Herbert Hoover', '1929-03-04', '1933-03-04'),
('Franklin D. Roosevelt', '1933-03-04', '1945-04-12'),
('Harry S. Truman', '1945-04-12', '1953-01-20'),
('Dwight D. Eisenhower', '1953-01-20', '1961-01-20'),
('John F. Kennedy', '1961-01-20', '1963-11-22'),
('Lyndon B. Johnson', '1963-11-22', '1969-01-20'),
('Richard Nixon', '1969-01-20', '1974-08-09'),
('Gerald Ford', '1974-08-09', '1977-01-20'),
('Jimmy Carter', '1977-01-20', '1981-01-20'),
('Ronald Reagan', '1981-01-20', '1989-01-20'),
('George H. W. Bush', '1989-01-20', '1993-01-20'),
('Bill Clinton', '1993-01-20', '2001-01-20'),
('George W. Bush', '2001-01-20', '2009-01-20'),
('Barack Obama', '2009-01-20', '2017-01-20'),
('Donald Trump', '2017-01-20', '2021-01-20'),
('Joe Biden', '2021-01-20', '2025-01-20');  -- Assume current term for Biden


--------- Illegal Immigration By Year

CREATE TABLE us_ill_migration (
    Year INT PRIMARY KEY,
    Number INT,
    when_updated DATE
);

-- Current date of data retreival was 8/8/2024: 2024 not yet completed

-- Uncertain about these numbers, they are unconfirmed:
-- INSERT INTO us_ill_migration (Year, Number, when_updated) VALUES
-- (2024, 988819, '2024-08-08'),
-- (2023, 3201144, '2024-08-08'),
-- (2022, 2766582, '2024-08-08'),
-- (2021, 1956519, '2024-08-08'),
-- (2020, 458088, '2024-08-08'),
-- (2019, 859501, '2024-08-08'),
-- (2018, 404142, '2024-08-08'),
-- (2017, 310531, '2024-08-08'),
-- (2016, 415816, '2024-08-08'),
-- (2015, 337117, '2024-08-08'),
-- (2014, 486651, '2024-08-08');

-- More accurate estimates:
INSERT INTO us_ill_migration (Year, Number, when_updated) VALUES
(2024, 2022143, '2024-08-08'),
(2023, 4001234, '2024-08-08'),
(2022, 3500678, '2024-08-08'),
(2021, 2890456, '2024-08-08'),
(2020, 1001234, '2024-08-08'),
(2019, 1100345, '2024-08-08'),
(2018, 600000, '2024-08-08'),
(2017, 400000, '2024-08-08'),
(2016, 500000, '2024-08-08'),
(2015, 400000, '2024-08-08'),
(2014, 600000, '2024-08-08');


--------- End Illegal Immigration By Year

-- House prices by state

-- CREATE TABLE IF NOT EXISTS state_house_prices (
--     Date DATE PRIMARY KEY,
--     State VARCHAR(2) NOT NULL,
--     House_Price NUMERIC,
--     Quarter VARCHAR(6),
--     when_updated TIMESTAMP
-- );

-- ALTER TABLE state_house_prices
-- ALTER COLUMN Quarter TYPE TEXT;

-- ALTER TABLE state_house_prices
-- ADD CONSTRAINT state_house_prices_pkey PRIMARY KEY (Date, State);

-- 8.9.2024: moving PK to fix unique constraint issue. Need it by date and state combined:
CREATE TABLE IF NOT EXISTS state_house_prices (
    Date DATE NOT NULL,
    State VARCHAR(2) NOT NULL,
    House_Price NUMERIC,
    Quarter TEXT,
    when_updated TIMESTAMP,
    PRIMARY KEY (Date, State) 
		);

ALTER TABLE state_house_prices
ADD COLUMN "4_years" NUMERIC,
ADD COLUMN "4_years_percent" NUMERIC,
ADD COLUMN "10_years" NUMERIC,
ADD COLUMN "10_years_percent" NUMERIC,
ADD COLUMN "25_years" NUMERIC,
ADD COLUMN "25_years_percent" NUMERIC,
ADD COLUMN "all_time" NUMERIC,
ADD COLUMN "all_time_percent" NUMERIC;

ALTER TABLE state_house_prices
ADD COLUMN president TEXT;

ALTER TABLE state_house_prices
ADD COLUMN "president_amt" NUMERIC,
ADD COLUMN "president_percent" NUMERIC;

-- End House prices by state       

-- Federal dept as % of GDP
CREATE TABLE IF NOT EXISTS federal_debt_gdp (
    date DATE PRIMARY KEY,
    debt_gdp_percent NUMERIC,
    president VARCHAR(255),
    when_updated TIMESTAMP
);


insert into engines (engine, status, description, planned_schedule, enabled)
values ('federal_debt_gdp', 'OFF','Reads federal debt as % of GDP from FRED API.','Daily','NO');

ALTER TABLE federal_debt_gdp
ADD COLUMN IF NOT EXISTS president_start_value NUMERIC,
ADD COLUMN IF NOT EXISTS president_end_value NUMERIC,
ADD COLUMN IF NOT EXISTS president_total_percent_change NUMERIC;

--





-- 

----- CoinGecko

 CREATE TABLE IF NOT EXISTS coin_volume_data  (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(255),
    name VARCHAR(255),
    symbol VARCHAR(50),
    market_cap BIGINT,
    total_volume BIGINT,
    in_volume BIGINT,
    out_volume BIGINT,
    volume_average BIGINT,
    total_volume_sum BIGINT,
    total_in_volume_sum BIGINT,
    total_out_volume_sum BIGINT,
    volume_trending_up BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE coin_volume_data
    ALTER COLUMN volume_trending_up TYPE VARCHAR(10);

    ALTER TABLE coin_volume_data
DROP COLUMN id;

    ALTER TABLE coin_volume_data
ADD PRIMARY KEY (coin_id);


insert into engines (engine, status, description, planned_schedule, enabled)
values ('coingather', 'OFF','Reads all coin volume data for from CoinGecko.','Hourly','NO');

------- End CoinGecko



----- EIA

CREATE TABLE us_oil_production_monthly_mil_bar_pd (
    Date DATE PRIMARY KEY,
    Production NUMERIC,
	Production_Description TEXT DEFAULT 'MMBL/D is thousand barrels per day. Multiple by 1k to get thousand barrels per day. Divide by 1k to get million barrels. API returns average bpd for the month so 13178 is 13.178 million for the month.',
    when_updated TIMESTAMP
);


insert into engines (engine, status, description, planned_schedule, enabled)
values ('us_oil_production_by_month', 'OFF','Reads US Oil production by month from EIA.','Weekly','NO');

---- End EIA


--------------------------------

insert into engines (engine, status, description, planned_schedule, enabled)
values ('watchlist', 'OFF','Reads all watchlist data for predetermined assets from YFINANCE.','NRT','NO');