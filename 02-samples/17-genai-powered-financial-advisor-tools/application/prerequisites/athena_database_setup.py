"""
Amazon Athena Database Setup Script

This script creates an S3 bucket, Athena database, tables, and inserts data
based on configuration from prereqs_config.yaml
"""

import boto3
import yaml
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import re

# Configure logging - save log file in the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, 'athena_setup.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AthenaSetupError(Exception):
    """Custom exception for setup errors"""
    pass

class AthenaDatabaseSetup:
    def __init__(self, config_path: str = None):
        """Initialize the setup with configuration"""
        if config_path is None:
            # Try to find config file in the same directory as this script
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "prereqs_config.yaml")
        
        self.config_path = config_path
        self.config = self._load_config()
        self.created_resources = []
        self.s3_client = None
        self.athena_client = None
        self.bucket_name = None
        self.database_name = None
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            # Check if file exists and provide helpful error message
            if not os.path.exists(self.config_path):
                current_dir = os.getcwd()
                script_dir = os.path.dirname(os.path.abspath(__file__))
                raise AthenaSetupError(
                    f"Configuration file not found: {self.config_path}\n"
                    f"Current working directory: {current_dir}\n"
                    f"Script directory: {script_dir}\n"
                    f"Looking for config file at: {os.path.abspath(self.config_path)}"
                )
            
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"✅ Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            raise AthenaSetupError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise AthenaSetupError(f"Error parsing YAML configuration: {e}")
    
    def _update_config_file(self):
        """Update the YAML configuration file with generated S3 bucket and database names"""
        try:
            # Read current config
            with open(self.config_path, 'r') as file:
                config_data = yaml.safe_load(file)
            
            # Update with generated names
            config_data['s3_bucket_name_for_athena'] = self.bucket_name
            config_data['database_name'] = self.database_name
            
            # Write back to file
            with open(self.config_path, 'w') as file:
                yaml.dump(config_data, file, default_flow_style=False, sort_keys=False)
            
            logger.info(f"✅ Configuration file updated with generated names")
            logger.info(f"  • S3 Bucket: {self.bucket_name}")
            logger.info(f"  • Database: {self.database_name}")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to update configuration file: {e}")
            # Don't fail the entire setup if config update fails
    
    def _initialize_aws_clients(self):
        """Initialize AWS clients with proper error handling"""
        try:
            region = self.config.get('region_name', 'us-west-2')
            self.s3_client = boto3.client('s3', region_name=region)
            self.athena_client = boto3.client('athena', region_name=region)
            
            # Test credentials by making a simple call
            self.s3_client.list_buckets()
            logger.info(f"✅ AWS clients initialized for region: {region}")
            
        except NoCredentialsError:
            raise AthenaSetupError(
                "AWS credentials not found. Please configure your credentials using:\n"
                "- AWS CLI: aws configure\n"
                "- Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY\n"
                "- IAM roles (if running on EC2)"
            )
        except ClientError as e:
            raise AthenaSetupError(f"AWS client initialization failed: {e}")
    
    def _generate_bucket_name(self) -> str:
        """Generate unique bucket name with timestamp using project_name"""
        project_name = self.config.get('project_name', 'financial-advisor')
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        bucket_name = f"{project_name}-athena-{timestamp}".lower()
        
        # Ensure bucket name follows S3 naming rules
        bucket_name = re.sub(r'[^a-z0-9\-]', '-', bucket_name)
        bucket_name = re.sub(r'-+', '-', bucket_name)  # Remove multiple consecutive hyphens
        bucket_name = bucket_name.strip('-')  # Remove leading/trailing hyphens
        
        # Ensure bucket name is between 3-63 characters
        if len(bucket_name) > 63:
            # Truncate but keep timestamp
            max_prefix_len = 63 - len(f"-athena-{timestamp}")
            project_part = project_name[:max_prefix_len]
            bucket_name = f"{project_part}-athena-{timestamp}".lower()
            bucket_name = re.sub(r'[^a-z0-9\-]', '-', bucket_name)
            bucket_name = re.sub(r'-+', '-', bucket_name)
            bucket_name = bucket_name.strip('-')
        
        return bucket_name
    
    def _generate_database_name(self) -> str:
        """Generate unique database name with timestamp using project_name"""
        project_name = self.config.get('project_name', 'financial_advisor')
        # Convert hyphens to underscores for database name
        project_name = project_name.replace('-', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        database_name = f"{project_name}_{timestamp}".lower()
        
        # Ensure database name follows Athena naming rules (alphanumeric and underscores only)
        database_name = re.sub(r'[^a-z0-9_]', '_', database_name)
        database_name = re.sub(r'_+', '_', database_name)  # Remove multiple consecutive underscores
        database_name = database_name.strip('_')  # Remove leading/trailing underscores
        
        # Ensure database name starts with a letter
        if database_name and not database_name[0].isalpha():
            database_name = f"db_{database_name}"
        
        return database_name
    
    def create_s3_bucket(self) -> str:
        """Create S3 bucket for Athena data storage"""
        try:
            self.bucket_name = self._generate_bucket_name()
            region = self.config.get('region_name', 'us-west-2')
            
            logger.info(f"🚀 Creating S3 bucket: {self.bucket_name}")
            
            # Create bucket with region-specific configuration
            if region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Create folder structure for tables
            folders = [
                'advisors/', 'clients/', 'portfolios/', 'securities/',
                'portfolio_holdings/', 'performance_data/', 'client_daily_portfolio_performance/'
            ]
            
            for folder in folders:
                self.s3_client.put_object(Bucket=self.bucket_name, Key=folder)
            
            self.created_resources.append(('s3_bucket', self.bucket_name))
            logger.info(f"✅ S3 bucket created successfully: {self.bucket_name}")
            return self.bucket_name
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                raise AthenaSetupError(f"Bucket name {self.bucket_name} already exists globally")
            elif error_code == 'BucketAlreadyOwnedByYou':
                logger.warning(f"⚠️  Bucket {self.bucket_name} already exists and is owned by you")
                return self.bucket_name
            else:
                raise AthenaSetupError(f"Failed to create S3 bucket: {e}")
    
    def create_athena_database(self) -> str:
        """Create Athena database"""
        try:
            self.database_name = self._generate_database_name()
            project_name = self.config.get('project_name', 'financial-advisor')
            
            logger.info(f"🚀 Creating Athena database for project '{project_name}': {self.database_name}")
            
            query = f"CREATE DATABASE IF NOT EXISTS {self.database_name}"
            
            response = self.athena_client.start_query_execution(
                QueryString=query,
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )
            
            query_execution_id = response['QueryExecutionId']
            self._wait_for_query_completion(query_execution_id)
            
            self.created_resources.append(('athena_database', self.database_name))
            logger.info(f"✅ Athena database created successfully: {self.database_name}")
            return self.database_name
            
        except ClientError as e:
            raise AthenaSetupError(f"Failed to create Athena database: {e}")
    
    def _wait_for_query_completion(self, query_execution_id: str, timeout: int = 60):
        """Wait for Athena query to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            status = response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                return
            elif status in ['FAILED', 'CANCELLED']:
                reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                raise AthenaSetupError(f"Query failed: {reason}")
            
            time.sleep(2)
        
        raise AthenaSetupError(f"Query timeout after {timeout} seconds")
    
    def _get_embedded_sql(self) -> Tuple[List[str], List[str]]:
        """Get embedded SQL statements for CREATE and INSERT operations"""
        
        # CREATE TABLE statements
        create_statements = [
            f"""CREATE EXTERNAL TABLE advisors (
                advisor_id INT COMMENT 'Unique identifier for each advisor (Primary Key)',
                first_name VARCHAR(50) COMMENT 'Advisor first name (Required field)',   
                last_name VARCHAR(50) COMMENT 'Advisor last name (Required field)',
                credentials VARCHAR(100) COMMENT 'Professional credentials (e.g., CFP, CFA, ChFC)',
                phone VARCHAR(20) COMMENT 'Primary contact phone number',
                email VARCHAR(100) COMMENT 'Business email address',
                office_location VARCHAR(100) COMMENT 'Physical office location or branch',
                created_date TIMESTAMP COMMENT 'Record creation timestamp (Auto-generated)'
            )
            COMMENT 'Financial advisor profile information'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/advisors/'""",
            
            f"""CREATE EXTERNAL TABLE clients (
                client_id INT COMMENT 'Unique identifier for each client (Primary Key)',
                first_name VARCHAR(50) COMMENT 'Client first name (Required field)',
                last_name VARCHAR(50) COMMENT 'Clients last name (Required field)',
                email VARCHAR(100) COMMENT 'Client email address',
                phone VARCHAR(20) COMMENT 'Client primary phone number',
                address VARCHAR(200) COMMENT 'Client mailing address',
                date_of_birth DATE COMMENT 'Client birth date',
                advisor_id INT COMMENT 'Foreign key linking to assigned advisor',
                account_open_date DATE COMMENT 'Date when client first opened account',
                risk_tolerance VARCHAR(20) COMMENT 'investment risk preference',
                investment_objectives STRING COMMENT 'Free-text description of client investment goals',
                created_date TIMESTAMP COMMENT 'Record creation timestamp (Auto-generated)'
            )
            COMMENT 'Client profile information'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/clients/'""",
            
            f"""CREATE EXTERNAL TABLE portfolios (
                portfolio_id INT COMMENT 'Unique identifier for each portfolio (Primary Key)',
                client_id INT COMMENT 'Foreign key linking to portfolio owner (Required)',
                portfolio_name VARCHAR(100) COMMENT 'Descriptive name for the portfolio (Required)',
                total_value DECIMAL(15,2) COMMENT 'Current total market value of all holdings',
                portfolio_beta DECIMAL(6,3) COMMENT 'Portfolio beta coefficient (systematic risk measure)',
                sharpe_ratio DECIMAL(6,3) COMMENT 'Risk-adjusted return metric (return per unit of risk)',
                inception_date DATE COMMENT 'Date when portfolio was first created',
                last_rebalance_date DATE COMMENT 'Most recent date when portfolio allocation was adjusted',
                status VARCHAR(20) COMMENT 'Current portfolio status',
                created_date TIMESTAMP COMMENT 'Record creation timestamp (Auto-generated)'
            )
            COMMENT 'Investment portfolios belonging to clients, containing multiple securities'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/portfolios/'""",
            
            f"""CREATE EXTERNAL TABLE securities (
                security_id INT COMMENT 'Unique identifier for each security (Primary Key)',
                symbol VARCHAR(10) COMMENT 'Trading symbol (e.g., MSFT, AMZN) - must be unique',
                company_name VARCHAR(200) COMMENT 'Full company or fund name (Required)',
                security_type VARCHAR(50) COMMENT 'Type of security (Common Stock, ETF, Bond, etc.)',
                sector VARCHAR(100) COMMENT 'Industry sector classification',
                exchange_name VARCHAR(50) COMMENT 'Stock exchange where security trades (NYSE, NASDAQ, etc.)',
                dividend_yield DECIMAL(5,2) COMMENT 'Current annual dividend yield percentage',
                created_date TIMESTAMP COMMENT 'Record creation timestamp (Auto-generated)'
            )
            COMMENT 'Stocks, ETFs, bonds, and other securities that can be held in portfolios'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/securities/'""",
            
            f"""CREATE EXTERNAL TABLE portfolio_holdings (
                holding_id INT COMMENT 'Unique identifier for each holding record (Primary Key)',
                portfolio_id INT COMMENT 'Foreign key to parent portfolio (Required)',
                security_id INT COMMENT 'Foreign key to the security being held (Required)',
                shares_held DECIMAL(15,4) COMMENT 'Number of shares/units owned (supports fractional shares)',
                current_allocation_percent DECIMAL(5,2) COMMENT 'Current percentage of total portfolio value',
                cost_basis DECIMAL(10,2) COMMENT 'Average cost per share (for tax and performance calculations)',
                current_market_value DECIMAL(15,2) COMMENT 'Current total market value of this holding',
                purchase_date DATE COMMENT 'Date when position was first established',
                last_updated TIMESTAMP COMMENT 'Last time holding data was updated'
            )
            COMMENT 'Stores individual security positions within each portfolio'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/portfolio_holdings/'""",
            
            f"""CREATE EXTERNAL TABLE performance_data (
                performance_id INT,
                portfolio_id INT,
                security_id INT,
                performance_type VARCHAR(20) COMMENT 'portfolio, security, benchmark',
                period_type VARCHAR(20) COMMENT 'daily,monthly,quarterly,annual',
                period_start_date DATE,
                period_end_date DATE,
                return_percentage DECIMAL(8,4) COMMENT 'Performance return as percentage',
                absolute_return DECIMAL(15,2) COMMENT 'Absolute dollar return amount',
                benchmark_return DECIMAL(8,4) COMMENT 'Corresponding benchmark return',
                excess_return DECIMAL(8,4) COMMENT 'Return above/below benchmark',
                volatility DECIMAL(8,4) COMMENT 'Risk measure (standard deviation)',
                created_date TIMESTAMP
            )
            COMMENT 'Stores historical performance metrics for portfolios and individual securities'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/performance_data/'""",
            
            f"""CREATE EXTERNAL TABLE client_daily_portfolio_performance (
                client_id INT COMMENT 'client id',
                portfolio_id INT COMMENT 'portfolio id',
                client_name VARCHAR(50) COMMENT 'client name',
                portfolio_value DECIMAL(15,2) COMMENT 'client portfolio value',
                transaction_date TIMESTAMP 
            )
            COMMENT 'client daily portfolio performance pricing data'
            STORED AS PARQUET
            LOCATION 's3://{self.bucket_name}/client_daily_portfolio_performance/'"""
        ]
        
        # INSERT statements
        insert_statements = [
            """INSERT INTO advisors (advisor_id, first_name, last_name, credentials, phone, email, office_location) VALUES
            (1, 'Sarah', 'Johnson', 'CFP, CPA', '555-0125', 's.johnson@advisor.com', 'West Side Office'),
            (2, 'Jennifer', 'Martinez', 'CFP, CFA', '555-0123', 'j.martinez@advisor.com', 'Main Office Downtown'),
            (3, 'David', 'Chen', 'CFA, ChFC', '555-0124', 'd.chen@advisor.com', 'North Branch Office')""",
            
            """INSERT INTO clients (client_id, first_name, last_name, email, phone, date_of_birth, advisor_id, account_open_date, risk_tolerance, investment_objectives) VALUES
            (1, 'Michael', 'Chen', 'robert.tanaka@email.com', '555-1001', CAST('1970-03-15' AS DATE), 1, CAST('2025-01-01' AS DATE), 'Moderate', 'Growth with some income, preparing for retirement in 10-15 years'),
            (2, 'Maria', 'Rodriguez', 'maria.rodriguez@email.com', '555-1002', CAST('1985-07-22' AS DATE), 3, CAST('2024-07-01' AS DATE), 'Aggressive', 'Long-term capital appreciation'),
            (3, 'James', 'Wilson', 'james.wilson@email.com', '555-1003', CAST('1965-11-08' AS DATE), 2, CAST('2024-01-01' AS DATE), 'Conservative', 'Capital preservation with moderate growth')""",
            
            """INSERT INTO securities (security_id, symbol, company_name, security_type, sector, exchange_name, dividend_yield) VALUES
            (1, 'AMZN', 'Amazon.com Inc.', 'Common Stock', 'Consumer Discretionary', 'NASDAQ', 0.00),
            (2, 'MSFT', 'Microsoft Corporation', 'Common Stock', 'Technology', 'NASDAQ', 0.64),
            (3, 'NVDA', 'NVIDIA Corporation', 'Common Stock', 'Technology', 'NASDAQ', 0.03),
            (4, 'SPY', 'SPDR S&P 500 ETF Trust', 'ETF', 'Broad Market', 'NYSE Arca', 1.20),
            (5, 'VHT', 'Vanguard Health Care ETF', 'ETF', 'Healthcare', 'NYSE Arca', 1.40),
            (6, 'IEF', 'iShares 7-10 Year Treasury Bond ETF', 'ETF', 'Fixed Income', 'NYSE Arca', 3.20)""",
            
            """INSERT INTO portfolios (portfolio_id, client_id, portfolio_name, total_value, portfolio_beta, sharpe_ratio, inception_date, last_rebalance_date) VALUES
            (1, 1, 'Michael Chen Growth Portfolio', 2500000.00, 1.28, 1.30, CAST('2020-01-15' AS DATE), CAST('2025-01-15' AS DATE)),
            (2, 2, 'Maria Rodriguez Aggressive Growth', 850000.00, 1.45, 1.25, CAST('2021-06-10' AS DATE), CAST('2025-02-01' AS DATE)),
            (3, 3, 'James Wilson Conservative Portfolio', 1200000.00, 0.85, 1.15, CAST('2019-09-20' AS DATE), CAST('2025-03-01' AS DATE))""",
            
            """INSERT INTO portfolio_holdings (holding_id, portfolio_id, security_id, shares_held, current_allocation_percent, cost_basis, current_market_value, purchase_date) VALUES
            (1, 1, 1, 2000.00, 18.00, 180.00, 450000.00, CAST('2020-02-01' AS DATE)),
            (2, 1, 2, 1095.00, 22.00, 420.00, 550000.00, CAST('2020-02-15' AS DATE)),
            (3, 1, 3, 2273.00, 15.00, 120.00, 375000.00, CAST('2020-03-01' AS DATE)),
            (4, 1, 4, 1345.00, 30.00, 400.00, 750000.00, CAST('2020-01-20' AS DATE)),
            (5, 1, 5, 1250.00, 15.00, 220.00, 375000.00, CAST('2020-04-01' AS DATE)),
            (6, 2, 2, 425.00, 25.00, 380.00, 212500.00, CAST('2021-06-15' AS DATE)),
            (7, 2, 3, 773.00, 35.00, 95.00, 297500.00, CAST('2021-07-01' AS DATE)),
            (8, 2, 4, 425.00, 20.00, 420.00, 170000.00, CAST('2021-06-20' AS DATE)),
            (9, 2, 5, 550.00, 20.00, 200.00, 170000.00, CAST('2021-08-01' AS DATE)),
            (10, 3, 4, 1200.00, 50.00, 350.00, 600000.00, CAST('2019-10-01' AS DATE)),
            (11, 3, 5, 1000.00, 25.00, 180.00, 300000.00, CAST('2019-10-15' AS DATE)),
            (12, 3, 6, 2500.00, 25.00, 120.00, 300000.00, CAST('2019-11-01' AS DATE))""",
            
            """INSERT INTO performance_data (performance_id, portfolio_id, security_id, performance_type, period_type, period_start_date, period_end_date, return_percentage, benchmark_return, excess_return, volatility) VALUES
            (1, 1, NULL, 'Portfolio', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 8.30, 6.10, 2.20, 18.5),
            (2, 1, NULL, 'Portfolio', 'YTD', CAST('2025-01-01' AS DATE), CAST('2025-04-20' AS DATE), 12.40, 9.20, 3.20, 19.2),
            (3, 1, NULL, 'Portfolio', '1_Year', CAST('2024-04-20' AS DATE), CAST('2025-04-20' AS DATE), 18.50, 15.20, 3.30, 20.1),
            (4, 1, NULL, 'Portfolio', 'Since_Inception', CAST('2020-01-15' AS DATE), CAST('2025-04-20' AS DATE), 156.30, 142.80, 13.50, 22.8),
            (5, NULL, 1, 'Security', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 7.20, 6.10, 1.10, 25.4),
            (6, NULL, 2, 'Security', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 9.80, 6.10, 3.70, 22.1),
            (7, NULL, 3, 'Security', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 17.60, 6.10, 11.50, 35.8),
            (8, NULL, 4, 'Security', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 6.10, 6.10, 0.00, 16.2),
            (9, NULL, 5, 'Security', 'Quarterly', CAST('2025-01-01' AS DATE), CAST('2025-03-31' AS DATE), 4.50, 6.10, -1.60, 19.8),
            (10, NULL, 1, 'Security', 'YTD', CAST('2025-01-01' AS DATE), CAST('2025-07-13' AS DATE), 2.57, 9.20, -6.63, 28.2)""",
            
            """INSERT INTO client_daily_portfolio_performance (client_id, portfolio_id, client_name, portfolio_value, transaction_date) VALUES
            (1, 1, 'Michael Chen', 409536.62, CAST('2020-01-21' AS DATE)),
            (1, 1, 'Michael Chen', 409586.20, CAST('2020-01-22' AS DATE)),
            (1, 1, 'Michael Chen', 410055.93, CAST('2020-01-23' AS DATE)),
            (1, 1, 'Michael Chen', 406409.31, CAST('2020-01-24' AS DATE)),
            (1, 1, 'Michael Chen', 399894.75, CAST('2020-01-27' AS DATE)),
            (1, 1, 'Michael Chen', 404085.36, CAST('2020-01-28' AS DATE)),
            (1, 1, 'Michael Chen', 403751.49, CAST('2020-01-29' AS DATE)),
            (1, 1, 'Michael Chen', 405061.93, CAST('2020-01-30' AS DATE)),
            (1, 1, 'Michael Chen', 397706.79, CAST('2020-01-31' AS DATE)),
            (1, 1, 'Michael Chen', 601081.12, CAST('2020-02-03' AS DATE)),
            (1, 1, 'Michael Chen', 611734.80, CAST('2020-02-04' AS DATE)),
            (1, 1, 'Michael Chen', 615452.13, CAST('2020-02-05' AS DATE)),
            (1, 1, 'Michael Chen', 617872.69, CAST('2020-02-06' AS DATE)),
            (1, 1, 'Michael Chen', 618577.33, CAST('2020-02-07' AS DATE)),
            (1, 1, 'Michael Chen', 627105.95, CAST('2020-02-10' AS DATE)),
            (1, 1, 'Michael Chen', 629511.86, CAST('2020-02-11' AS DATE)),
            (1, 1, 'Michael Chen', 633102.08, CAST('2020-02-12' AS DATE)),
            (1, 1, 'Michael Chen', 631643.89, CAST('2020-02-13' AS DATE)),
            (1, 1, 'Michael Chen', 630811.50, CAST('2020-02-14' AS DATE)),
            (1, 1, 'Michael Chen', 826840.12, CAST('2020-02-18' AS DATE)),
            (1, 1, 'Michael Chen', 830870.17, CAST('2020-02-19' AS DATE)),
            (1, 1, 'Michael Chen', 824452.76, CAST('2020-02-20' AS DATE)),
            (1, 1, 'Michael Chen', 808361.02, CAST('2020-02-21' AS DATE)),
            (1, 1, 'Michael Chen', 777978.81, CAST('2020-02-24' AS DATE)),
            (1, 1, 'Michael Chen', 759301.11, CAST('2020-02-25' AS DATE)),
            (1, 1, 'Michael Chen', 760757.89, CAST('2020-02-26' AS DATE)),
            (1, 1, 'Michael Chen', 721411.95, CAST('2020-02-27' AS DATE)),
            (1, 1, 'Michael Chen', 723812.18, CAST('2020-02-28' AS DATE)),
            (1, 1, 'Michael Chen', 773599.78, CAST('2020-03-02' AS DATE)),
            (1, 1, 'Michael Chen', 748919.10, CAST('2020-03-03' AS DATE)),
            (1, 1, 'Michael Chen', 778565.93, CAST('2020-03-04' AS DATE)),
            (1, 1, 'Michael Chen', 755424.52, CAST('2020-03-05' AS DATE)),
            (1, 1, 'Michael Chen', 741630.22, CAST('2020-03-06' AS DATE)),
            (1, 1, 'Michael Chen', 690263.38, CAST('2020-03-09' AS DATE)),
            (1, 1, 'Michael Chen', 728568.80, CAST('2020-03-10' AS DATE)),
            (1, 1, 'Michael Chen', 695651.24, CAST('2020-03-11' AS DATE)),
            (1, 1, 'Michael Chen', 631851.91, CAST('2020-03-12' AS DATE)),
            (1, 1, 'Michael Chen', 690947.57, CAST('2020-03-13' AS DATE)),
            (1, 1, 'Michael Chen', 617966.39, CAST('2020-03-16' AS DATE)),
            (1, 1, 'Michael Chen', 658670.82, CAST('2020-03-17' AS DATE)),
            (1, 1, 'Michael Chen', 637801.66, CAST('2020-03-18' AS DATE)),
            (1, 1, 'Michael Chen', 646512.49, CAST('2020-03-19' AS DATE)),
            (1, 1, 'Michael Chen', 624209.16, CAST('2020-03-20' AS DATE)),
            (1, 1, 'Michael Chen', 621571.03, CAST('2020-03-23' AS DATE)),
            (1, 1, 'Michael Chen', 665390.48, CAST('2020-03-24' AS DATE)),
            (1, 1, 'Michael Chen', 662805.90, CAST('2020-03-25' AS DATE)),
            (1, 1, 'Michael Chen', 697945.13, CAST('2020-03-26' AS DATE)),
            (1, 1, 'Michael Chen', 675781.82, CAST('2020-03-27' AS DATE)),
            (1, 1, 'Michael Chen', 704126.55, CAST('2020-03-30' AS DATE)),
            (1, 1, 'Michael Chen', 695109.54, CAST('2020-03-31' AS DATE)),
            (1, 1, 'Michael Chen', 854854.28, CAST('2020-04-01' AS DATE)),
            (1, 1, 'Michael Chen', 872109.92, CAST('2020-04-02' AS DATE)),
            (1, 1, 'Michael Chen', 862074.54, CAST('2020-04-03' AS DATE)),
            (1, 1, 'Michael Chen', 915366.67, CAST('2020-04-06' AS DATE)),
            (1, 1, 'Michael Chen', 913110.69, CAST('2020-04-07' AS DATE)),
            (1, 1, 'Michael Chen', 937226.63, CAST('2020-04-08' AS DATE)),
            (1, 1, 'Michael Chen', 944030.22, CAST('2020-04-09' AS DATE)),
            (1, 1, 'Michael Chen', 952563.80, CAST('2020-04-13' AS DATE)),
            (1, 1, 'Michael Chen', 990370.19, CAST('2020-04-14' AS DATE)),
            (1, 1, 'Michael Chen', 981523.98, CAST('2020-04-15' AS DATE)),
            (1, 1, 'Michael Chen', 1004189.45, CAST('2020-04-16' AS DATE)),
            (1, 1, 'Michael Chen', 1016909.70, CAST('2020-04-17' AS DATE)),
            (1, 1, 'Michael Chen', 1007415.25, CAST('2020-04-20' AS DATE)),
            (1, 1, 'Michael Chen', 974791.80, CAST('2020-04-21' AS DATE)),
            (1, 1, 'Michael Chen', 996162.94, CAST('2020-04-22' AS DATE)),
            (1, 1, 'Michael Chen', 998825.09, CAST('2020-04-23' AS DATE)),
            (1, 1, 'Michael Chen', 1011681.09, CAST('2020-04-24' AS DATE)),
            (1, 1, 'Michael Chen', 1016312.30, CAST('2020-04-27' AS DATE)),
            (1, 1, 'Michael Chen', 998952.40, CAST('2020-04-28' AS DATE)),
            (1, 1, 'Michael Chen', 1024649.30, CAST('2020-04-29' AS DATE)),
            (1, 1, 'Michael Chen', 1031185.48, CAST('2020-04-30' AS DATE)),
            (1, 1, 'Michael Chen', 993029.33, CAST('2020-05-01' AS DATE)),
            (1, 1, 'Michael Chen', 1002598.00, CAST('2020-05-04' AS DATE)),
            (1, 1, 'Michael Chen', 1012710.98, CAST('2020-05-05' AS DATE)),
            (1, 1, 'Michael Chen', 1014257.99, CAST('2020-05-06' AS DATE)),
            (1, 1, 'Michael Chen', 1021991.10, CAST('2020-05-07' AS DATE)),
            (1, 1, 'Michael Chen', 1032017.09, CAST('2020-05-08' AS DATE)),
            (1, 1, 'Michael Chen', 1042169.45, CAST('2020-05-11' AS DATE)),
            (1, 1, 'Michael Chen', 1021147.22, CAST('2020-05-12' AS DATE)),
            (1, 1, 'Michael Chen', 1010137.07, CAST('2020-05-13' AS DATE)),
            (1, 1, 'Michael Chen', 1019672.51, CAST('2020-05-14' AS DATE)),
            (1, 1, 'Michael Chen', 1029692.61, CAST('2020-05-15' AS DATE)),
            (1, 1, 'Michael Chen', 1047003.18, CAST('2020-05-18' AS DATE)),
            (1, 1, 'Michael Chen', 1041484.87, CAST('2020-05-19' AS DATE)),
            (1, 1, 'Michael Chen', 1056266.24, CAST('2020-05-20' AS DATE)),
            (1, 1, 'Michael Chen', 1044508.02, CAST('2020-05-21' AS DATE)),
            (1, 1, 'Michael Chen', 1045579.09, CAST('2020-05-22' AS DATE)),
            (1, 1, 'Michael Chen', 1045326.70, CAST('2020-05-26' AS DATE)),
            (1, 1, 'Michael Chen', 1051375.39, CAST('2020-05-27' AS DATE)),
            (1, 1, 'Michael Chen', 1051754.71, CAST('2020-05-28' AS DATE)),
            (1, 1, 'Michael Chen', 1063061.04, CAST('2020-05-29' AS DATE)),
            (1, 1, 'Michael Chen', 1065048.55, CAST('2020-06-01' AS DATE)),
            (1, 1, 'Michael Chen', 1072039.85, CAST('2020-06-02' AS DATE)),
            (1, 1, 'Michael Chen', 1077129.43, CAST('2020-06-03' AS DATE)),
            (1, 1, 'Michael Chen', 1069534.52, CAST('2020-06-04' AS DATE)),
            (1, 1, 'Michael Chen', 1090070.52, CAST('2020-06-05' AS DATE)),
            (1, 1, 'Michael Chen', 1101684.59, CAST('2020-06-08' AS DATE)),
            (1, 1, 'Michael Chen', 1106191.86, CAST('2020-06-09' AS DATE)),
            (1, 1, 'Michael Chen', 1116516.20, CAST('2020-06-10' AS DATE)),
            (1, 1, 'Michael Chen', 1059733.94, CAST('2020-06-11' AS DATE)),
            (1, 1, 'Michael Chen', 1066112.08, CAST('2020-06-12' AS DATE)),
            (1, 1, 'Michael Chen', 1075780.89, CAST('2020-06-15' AS DATE)),
            (1, 1, 'Michael Chen', 1096889.85, CAST('2020-06-16' AS DATE)),
            (1, 1, 'Michael Chen', 1098809.61, CAST('2020-06-17' AS DATE)),
            (1, 1, 'Michael Chen', 1102117.77, CAST('2020-06-18' AS DATE)),
            (1, 1, 'Michael Chen', 1103073.22, CAST('2020-06-19' AS DATE)),
            (1, 1, 'Michael Chen', 1115770.72, CAST('2020-06-22' AS DATE)),
            (1, 1, 'Michael Chen', 1124859.62, CAST('2020-06-23' AS DATE)),
            (1, 1, 'Michael Chen', 1101221.24, CAST('2020-06-24' AS DATE)),
            (1, 1, 'Michael Chen', 1112966.30, CAST('2020-06-25' AS DATE)),
            (1, 1, 'Michael Chen', 1089652.40, CAST('2020-06-26' AS DATE)),
            (1, 1, 'Michael Chen', 1097773.96, CAST('2020-06-29' AS DATE)),
            (1, 1, 'Michael Chen', 1120321.69, CAST('2020-06-30' AS DATE)),
            (1, 1, 'Michael Chen', 1138017.72, CAST('2020-07-01' AS DATE)),
            (1, 1, 'Michael Chen', 1144941.25, CAST('2020-07-02' AS DATE)),
            (1, 1, 'Michael Chen', 1174816.89, CAST('2020-07-06' AS DATE)),
            (1, 1, 'Michael Chen', 1161219.17, CAST('2020-07-07' AS DATE)),
            (1, 1, 'Michael Chen', 1178417.13, CAST('2020-07-08' AS DATE)),
            (1, 1, 'Michael Chen', 1186772.95, CAST('2020-07-09' AS DATE)),
            (1, 1, 'Michael Chen', 1191222.45, CAST('2020-07-10' AS DATE)),
            (1, 1, 'Michael Chen', 1170331.32, CAST('2020-07-13' AS DATE)),
            (1, 1, 'Michael Chen', 1180074.61, CAST('2020-07-14' AS DATE)),
            (1, 1, 'Michael Chen', 1179335.29, CAST('2020-07-15' AS DATE)),
            (1, 1, 'Michael Chen', 1172088.23, CAST('2020-07-16' AS DATE)),
            (1, 1, 'Michael Chen', 1171772.22, CAST('2020-07-17' AS DATE)),
            (1, 1, 'Michael Chen', 1208736.59, CAST('2020-07-20' AS DATE)),
            (1, 1, 'Michael Chen', 1199797.32, CAST('2020-07-21' AS DATE)),
            (1, 1, 'Michael Chen', 1203329.20, CAST('2020-07-22' AS DATE)),
            (1, 1, 'Michael Chen', 1175563.32, CAST('2020-07-23' AS DATE)),
            (1, 1, 'Michael Chen', 1170912.55, CAST('2020-07-24' AS DATE)),
            (1, 1, 'Michael Chen', 1183830.90, CAST('2020-07-27' AS DATE)),
            (1, 1, 'Michael Chen', 1172699.64, CAST('2020-07-28' AS DATE)),
            (1, 1, 'Michael Chen', 1185883.10, CAST('2020-07-29' AS DATE)),
            (1, 1, 'Michael Chen', 1185446.96, CAST('2020-07-30' AS DATE)),
            (1, 1, 'Michael Chen', 1199397.42, CAST('2020-07-31' AS DATE)),
            (1, 1, 'Michael Chen', 1212981.04, CAST('2020-08-03' AS DATE)),
            (1, 1, 'Michael Chen', 1213370.36, CAST('2020-08-04' AS DATE)),
            (1, 1, 'Michael Chen', 1223728.68, CAST('2020-08-05' AS DATE)),
            (1, 1, 'Michael Chen', 1230862.41, CAST('2020-08-06' AS DATE)),
            (1, 1, 'Michael Chen', 1221769.79, CAST('2020-08-07' AS DATE)),
            (1, 1, 'Michael Chen', 1215449.07, CAST('2020-08-10' AS DATE)),
            (1, 1, 'Michael Chen', 1197082.13, CAST('2020-08-11' AS DATE)),
            (1, 1, 'Michael Chen', 1222328.05, CAST('2020-08-12' AS DATE)),
            (1, 1, 'Michael Chen', 1220925.52, CAST('2020-08-13' AS DATE)),
            (1, 1, 'Michael Chen', 1219363.63, CAST('2020-08-14' AS DATE)),
            (1, 1, 'Michael Chen', 1229411.41, CAST('2020-08-17' AS DATE)),
            (1, 1, 'Michael Chen', 1244157.49, CAST('2020-08-18' AS DATE)),
            (1, 1, 'Michael Chen', 1234560.10, CAST('2020-08-19' AS DATE)),
            (1, 1, 'Michael Chen', 1244094.91, CAST('2020-08-20' AS DATE)),
            (1, 1, 'Michael Chen', 1243709.86, CAST('2020-08-21' AS DATE)),
            (1, 1, 'Michael Chen', 1249678.95, CAST('2020-08-24' AS DATE)),
            (1, 1, 'Michael Chen', 1259711.07, CAST('2020-08-25' AS DATE)),
            (1, 1, 'Michael Chen', 1278089.93, CAST('2020-08-26' AS DATE)),
            (1, 1, 'Michael Chen', 1281836.58, CAST('2020-08-27' AS DATE)),
            (1, 1, 'Michael Chen', 1289126.01, CAST('2020-08-28' AS DATE)),
            (1, 1, 'Michael Chen', 1290377.34, CAST('2020-08-31' AS DATE)),
            (1, 1, 'Michael Chen', 1300085.65, CAST('2020-09-01' AS DATE)),
            (1, 1, 'Michael Chen', 1320212.15, CAST('2020-09-02' AS DATE)),
            (1, 1, 'Michael Chen', 1263355.58, CAST('2020-09-03' AS DATE)),
            (1, 1, 'Michael Chen', 1246187.18, CAST('2020-09-04' AS DATE)),
            (1, 1, 'Michael Chen', 1202383.15, CAST('2020-09-08' AS DATE)),
            (1, 1, 'Michael Chen', 1237904.18, CAST('2020-09-09' AS DATE)),
            (1, 1, 'Michael Chen', 1210289.69, CAST('2020-09-10' AS DATE)),
            (1, 1, 'Michael Chen', 1203856.35, CAST('2020-09-11' AS DATE)),
            (1, 1, 'Michael Chen', 1215606.45, CAST('2020-09-14' AS DATE)),
            (1, 1, 'Michael Chen', 1227520.48, CAST('2020-09-15' AS DATE)),
            (1, 1, 'Michael Chen', 1213070.70, CAST('2020-09-16' AS DATE)),
            (1, 1, 'Michael Chen', 1199289.09, CAST('2020-09-17' AS DATE)),
            (1, 1, 'Michael Chen', 1185811.17, CAST('2020-09-18' AS DATE)),
            (1, 1, 'Michael Chen', 1180155.81, CAST('2020-09-21' AS DATE)),
            (1, 1, 'Michael Chen', 1206474.66, CAST('2020-09-22' AS DATE)),
            (1, 1, 'Michael Chen', 1172766.60, CAST('2020-09-23' AS DATE)),
            (1, 1, 'Michael Chen', 1177461.49, CAST('2020-09-24' AS DATE)),
            (1, 1, 'Michael Chen', 1202145.04, CAST('2020-09-25' AS DATE)),
            (1, 1, 'Michael Chen', 1221008.60, CAST('2020-09-28' AS DATE)),
            (1, 1, 'Michael Chen', 1213871.03, CAST('2020-09-29' AS DATE)),
            (1, 1, 'Michael Chen', 1224932.84, CAST('2020-09-30' AS DATE)),
            (1, 1, 'Michael Chen', 1236664.93, CAST('2020-10-01' AS DATE)),
            (1, 1, 'Michael Chen', 1213121.22, CAST('2020-10-02' AS DATE)),
            (1, 1, 'Michael Chen', 1239141.88, CAST('2020-10-05' AS DATE)),
            (1, 1, 'Michael Chen', 1215955.49, CAST('2020-10-06' AS DATE)),
            (1, 1, 'Michael Chen', 1242418.65, CAST('2020-10-07' AS DATE)),
            (1, 1, 'Michael Chen', 1247399.82, CAST('2020-10-08' AS DATE)),
            (1, 1, 'Michael Chen', 1268237.12, CAST('2020-10-09' AS DATE)),
            (1, 1, 'Michael Chen', 1299523.81, CAST('2020-10-12' AS DATE)),
            (1, 1, 'Michael Chen', 1297099.84, CAST('2020-10-13' AS DATE)),
            (1, 1, 'Michael Chen', 1281960.65, CAST('2020-10-14' AS DATE)),
            (1, 1, 'Michael Chen', 1276143.35, CAST('2020-10-15' AS DATE)),
            (1, 1, 'Michael Chen', 1271021.07, CAST('2020-10-16' AS DATE)),
            (1, 1, 'Michael Chen', 1247333.37, CAST('2020-10-19' AS DATE)),
            (1, 1, 'Michael Chen', 1250934.43, CAST('2020-10-20' AS DATE)),
            (1, 1, 'Michael Chen', 1244994.74, CAST('2020-10-21' AS DATE)),
            (1, 1, 'Michael Chen', 1250011.85, CAST('2020-10-22' AS DATE)),
            (1, 1, 'Michael Chen', 1257328.27, CAST('2020-10-23' AS DATE)),
            (1, 1, 'Michael Chen', 1239332.90, CAST('2020-10-26' AS DATE)),
            (1, 1, 'Michael Chen', 1248649.20, CAST('2020-10-27' AS DATE)),
            (1, 1, 'Michael Chen', 1201423.35, CAST('2020-10-28' AS DATE)),
            (1, 1, 'Michael Chen', 1212105.40, CAST('2020-10-29' AS DATE)),
            (1, 1, 'Michael Chen', 1185850.55, CAST('2020-10-30' AS DATE)),
            (1, 1, 'Michael Chen', 1190659.49, CAST('2020-11-02' AS DATE)),
            (1, 1, 'Michael Chen', 1211685.85, CAST('2020-11-03' AS DATE)),
            (1, 1, 'Michael Chen', 1263131.08, CAST('2020-11-04' AS DATE)),
            (1, 1, 'Michael Chen', 1288730.50, CAST('2020-11-05' AS DATE)),
            (1, 1, 'Michael Chen', 1288122.44, CAST('2020-11-06' AS DATE)),
            (1, 1, 'Michael Chen', 1271217.44, CAST('2020-11-09' AS DATE)),
            (1, 1, 'Michael Chen', 1250673.12, CAST('2020-11-10' AS DATE)),
            (1, 1, 'Michael Chen', 1271539.60, CAST('2020-11-11' AS DATE)),
            (1, 1, 'Michael Chen', 1262500.04, CAST('2020-11-12' AS DATE)),
            (1, 1, 'Michael Chen', 1274650.32, CAST('2020-11-13' AS DATE)),
            (1, 1, 'Michael Chen', 1281344.62, CAST('2020-11-16' AS DATE)),
            (1, 1, 'Michael Chen', 1274731.39, CAST('2020-11-17' AS DATE)),
            (1, 1, 'Michael Chen', 1258425.54, CAST('2020-11-18' AS DATE)),
            (1, 1, 'Michael Chen', 1263121.34, CAST('2020-11-19' AS DATE)),
            (1, 1, 'Michael Chen', 1255597.34, CAST('2020-11-20' AS DATE)),
            (1, 1, 'Michael Chen', 1257429.21, CAST('2020-11-23' AS DATE)),
            (1, 1, 'Michael Chen', 1270410.52, CAST('2020-11-24' AS DATE)),
            (1, 1, 'Michael Chen', 1276521.11, CAST('2020-11-25' AS DATE)),
            (1, 1, 'Michael Chen', 1283675.47, CAST('2020-11-27' AS DATE)),
            (1, 1, 'Michael Chen', 1278795.56, CAST('2020-11-30' AS DATE)),
            (1, 1, 'Michael Chen', 1293016.58, CAST('2020-12-01' AS DATE)),
            (1, 1, 'Michael Chen', 1293033.02, CAST('2020-12-02' AS DATE)),
            (1, 1, 'Michael Chen', 1289698.87, CAST('2020-12-03' AS DATE)),
            (1, 1, 'Michael Chen', 1295039.42, CAST('2020-12-04' AS DATE)),
            (1, 1, 'Michael Chen', 1292295.78, CAST('2020-12-07' AS DATE)),
            (1, 1, 'Michael Chen', 1299381.36, CAST('2020-12-08' AS DATE)),
            (1, 1, 'Michael Chen', 1281006.69, CAST('2020-12-09' AS DATE)),
            (1, 1, 'Michael Chen', 1279788.00, CAST('2020-12-10' AS DATE)),
            (1, 1, 'Michael Chen', 1282911.82, CAST('2020-12-11' AS DATE)),
            (1, 1, 'Michael Chen', 1285458.49, CAST('2020-12-14' AS DATE)),
            (1, 1, 'Michael Chen', 1295060.74, CAST('2020-12-15' AS DATE)),
            (1, 1, 'Michael Chen', 1307601.55, CAST('2020-12-16' AS DATE)),
            (1, 1, 'Michael Chen', 1313242.13, CAST('2020-12-17' AS DATE)),
            (1, 1, 'Michael Chen', 1307316.06, CAST('2020-12-18' AS DATE)),
            (1, 1, 'Michael Chen', 1308598.25, CAST('2020-12-21' AS DATE)),
            (1, 1, 'Michael Chen', 1309161.98, CAST('2020-12-22' AS DATE)),
            (1, 1, 'Michael Chen', 1304109.62, CAST('2020-12-23' AS DATE)),
            (1, 1, 'Michael Chen', 1306802.39, CAST('2020-12-24' AS DATE)),
            (1, 1, 'Michael Chen', 1323259.80, CAST('2020-12-28' AS DATE)),
            (1, 1, 'Michael Chen', 1325814.52, CAST('2020-12-29' AS DATE)),
            (1, 1, 'Michael Chen', 1321101.80, CAST('2020-12-30' AS DATE)),
            (1, 1, 'Michael Chen', 1323006.98, CAST('2020-12-31' AS DATE)),
            (1, 1, 'Michael Chen', 1303370.23, CAST('2021-01-04' AS DATE)),
            (1, 1, 'Michael Chen', 1312247.06, CAST('2021-01-05' AS DATE)),
            (1, 1, 'Michael Chen', 1303460.44, CAST('2021-01-06' AS DATE)),
            (1, 1, 'Michael Chen', 1325032.07, CAST('2021-01-07' AS DATE)),
            (1, 1, 'Michael Chen', 1332169.42, CAST('2021-01-08' AS DATE)),
            (1, 1, 'Michael Chen', 1322021.26, CAST('2021-01-11' AS DATE)),
            (1, 1, 'Michael Chen', 1317758.99, CAST('2021-01-12' AS DATE)),
            (1, 1, 'Michael Chen', 1325809.65, CAST('2021-01-13' AS DATE)),
            (1, 1, 'Michael Chen', 1316269.76, CAST('2021-01-14' AS DATE)),
            (1, 1, 'Michael Chen', 1309369.10, CAST('2021-01-15' AS DATE)),
            (1, 1, 'Michael Chen', 1321883.91, CAST('2021-01-19' AS DATE)),
            (1, 1, 'Michael Chen', 1353018.48, CAST('2021-01-20' AS DATE)),
            (1, 1, 'Michael Chen', 1358410.93, CAST('2021-01-21' AS DATE)),
            (1, 1, 'Michael Chen', 1355491.42, CAST('2021-01-22' AS DATE)),
            (1, 1, 'Michael Chen', 1363423.96, CAST('2021-01-25' AS DATE)),
            (1, 1, 'Michael Chen', 1366185.56, CAST('2021-01-26' AS DATE)),
            (1, 1, 'Michael Chen', 1336129.83, CAST('2021-01-27' AS DATE)),
            (1, 1, 'Michael Chen', 1350991.05, CAST('2021-01-28' AS DATE)),
            (1, 1, 'Michael Chen', 1329255.93, CAST('2021-01-29' AS DATE)),
            (1, 1, 'Michael Chen', 1360839.71, CAST('2021-02-01' AS DATE)),
            (1, 1, 'Michael Chen', 1373578.45, CAST('2021-02-02' AS DATE)),
            (1, 1, 'Michael Chen', 1369085.09, CAST('2021-02-03' AS DATE)),
            (1, 1, 'Michael Chen', 1377525.80, CAST('2021-02-04' AS DATE)),
            (1, 1, 'Michael Chen', 1382892.60, CAST('2021-02-05' AS DATE)),
            (1, 1, 'Michael Chen', 1387347.74, CAST('2021-02-08' AS DATE)),
            (1, 1, 'Michael Chen', 1386384.87, CAST('2021-02-09' AS DATE)),
            (1, 1, 'Michael Chen', 1384734.60, CAST('2021-02-10' AS DATE)),
            (1, 1, 'Michael Chen', 1386425.15, CAST('2021-02-11' AS DATE)),
            (1, 1, 'Michael Chen', 1392127.56, CAST('2021-02-12' AS DATE)),
            (1, 1, 'Michael Chen', 1386754.71, CAST('2021-02-16' AS DATE)),
            (1, 1, 'Michael Chen', 1391252.24, CAST('2021-02-17' AS DATE)),
            (1, 1, 'Michael Chen', 1388175.57, CAST('2021-02-18' AS DATE)),
            (1, 1, 'Michael Chen', 1375121.94, CAST('2021-02-19' AS DATE)),
            (1, 1, 'Michael Chen', 1353828.60, CAST('2021-02-22' AS DATE)),
            (1, 1, 'Michael Chen', 1353040.47, CAST('2021-02-23' AS DATE)),
            (1, 1, 'Michael Chen', 1359229.50, CAST('2021-02-24' AS DATE)),
            (1, 1, 'Michael Chen', 1324497.79, CAST('2021-02-25' AS DATE)),
            (1, 1, 'Michael Chen', 1328355.00, CAST('2021-02-26' AS DATE)),
            (1, 1, 'Michael Chen', 1354473.33, CAST('2021-03-01' AS DATE)),
            (1, 1, 'Michael Chen', 1339625.36, CAST('2021-03-02' AS DATE)),
            (1, 1, 'Michael Chen', 1311024.19, CAST('2021-03-03' AS DATE)),
            (1, 1, 'Michael Chen', 1295672.92, CAST('2021-03-04' AS DATE)),
            (1, 1, 'Michael Chen', 1316849.27, CAST('2021-03-05' AS DATE)),
            (1, 1, 'Michael Chen', 1301362.56, CAST('2021-03-08' AS DATE)),
            (1, 1, 'Michael Chen', 1331515.95, CAST('2021-03-09' AS DATE)),
            (1, 1, 'Michael Chen', 1333040.68, CAST('2021-03-10' AS DATE)),
            (1, 1, 'Michael Chen', 1352941.57, CAST('2021-03-11' AS DATE)),
            (1, 1, 'Michael Chen', 1349889.17, CAST('2021-03-12' AS DATE)),
            (1, 1, 'Michael Chen', 1353644.43, CAST('2021-03-15' AS DATE)),
            (1, 1, 'Michael Chen', 1356661.63, CAST('2021-03-16' AS DATE)),
            (1, 1, 'Michael Chen', 1361591.19, CAST('2021-03-17' AS DATE)),
            (1, 1, 'Michael Chen', 1333388.85, CAST('2021-03-18' AS DATE)),
            (1, 1, 'Michael Chen', 1338836.50, CAST('2021-03-19' AS DATE)),
            (1, 1, 'Michael Chen', 1355334.40, CAST('2021-03-22' AS DATE)),
            (1, 1, 'Michael Chen', 1351715.45, CAST('2021-03-23' AS DATE)),
            (1, 1, 'Michael Chen', 1339155.35, CAST('2021-03-24' AS DATE)),
            (1, 1, 'Michael Chen', 1335196.71, CAST('2021-03-25' AS DATE)),
            (1, 1, 'Michael Chen', 1352987.71, CAST('2021-03-26' AS DATE)),
            (1, 1, 'Michael Chen', 1354091.08, CAST('2021-03-29' AS DATE)),
            (1, 1, 'Michael Chen', 1345109.22, CAST('2021-03-30' AS DATE)),
            (1, 1, 'Michael Chen', 1358581.85, CAST('2021-03-31' AS DATE)),
            (1, 1, 'Michael Chen', 1378533.12, CAST('2021-04-01' AS DATE)),
            (1, 1, 'Michael Chen', 1401355.08, CAST('2021-04-05' AS DATE)),
            (1, 1, 'Michael Chen', 1398468.24, CAST('2021-04-06' AS DATE)),
            (1, 1, 'Michael Chen', 1405844.14, CAST('2021-04-07' AS DATE)),
            (1, 1, 'Michael Chen', 1415214.42, CAST('2021-04-08' AS DATE)),
            (1, 1, 'Michael Chen', 1431119.83, CAST('2021-04-09' AS DATE)),
            (1, 1, 'Michael Chen', 1433878.90, CAST('2021-04-12' AS DATE)),
            (1, 1, 'Michael Chen', 1443449.33, CAST('2021-04-13' AS DATE)),
            (1, 1, 'Michael Chen', 1431183.96, CAST('2021-04-14' AS DATE)),
            (1, 1, 'Michael Chen', 1452517.96, CAST('2021-04-15' AS DATE)),
            (1, 1, 'Michael Chen', 1458368.13, CAST('2021-04-16' AS DATE)),
            (1, 1, 'Michael Chen', 1448615.98, CAST('2021-04-19' AS DATE)),
            (1, 1, 'Michael Chen', 1440882.43, CAST('2021-04-20' AS DATE)),
            (1, 1, 'Michael Chen', 1455377.22, CAST('2021-04-21' AS DATE)),
            (1, 1, 'Michael Chen', 1439416.30, CAST('2021-04-22' AS DATE)),
            (1, 1, 'Michael Chen', 1455566.94, CAST('2021-04-23' AS DATE)),
            (1, 1, 'Michael Chen', 1464794.71, CAST('2021-04-26' AS DATE)),
            (1, 1, 'Michael Chen', 1464194.03, CAST('2021-04-27' AS DATE)),
            (1, 1, 'Michael Chen', 1459516.03, CAST('2021-04-28' AS DATE)),
            (1, 1, 'Michael Chen', 1460324.88, CAST('2021-04-29' AS DATE)),
            (1, 1, 'Michael Chen', 1454655.73, CAST('2021-04-30' AS DATE)),
            (1, 1, 'Michael Chen', 1448890.42, CAST('2021-05-03' AS DATE)),
            (1, 1, 'Michael Chen', 1431407.41, CAST('2021-05-04' AS DATE)),
            (1, 1, 'Michael Chen', 1425912.21, CAST('2021-05-05' AS DATE)),
            (1, 1, 'Michael Chen', 1436969.19, CAST('2021-05-06' AS DATE)),
            (1, 1, 'Michael Chen', 1445273.86, CAST('2021-05-07' AS DATE)),
            (1, 1, 'Michael Chen', 1421304.03, CAST('2021-05-10' AS DATE)),
            (1, 1, 'Michael Chen', 1417232.83, CAST('2021-05-11' AS DATE)),
            (1, 1, 'Michael Chen', 1386773.45, CAST('2021-05-12' AS DATE)),
            (1, 1, 'Michael Chen', 1399839.60, CAST('2021-05-13' AS DATE)),
            (1, 1, 'Michael Chen', 1422868.19, CAST('2021-05-14' AS DATE)),
            (1, 1, 'Michael Chen', 1422415.08, CAST('2021-05-17' AS DATE)),
            (1, 1, 'Michael Chen', 1411973.54, CAST('2021-05-18' AS DATE)),
            (1, 1, 'Michael Chen', 1410602.40, CAST('2021-05-19' AS DATE)),
            (1, 1, 'Michael Chen', 1426065.87, CAST('2021-05-20' AS DATE)),
            (1, 1, 'Michael Chen', 1420485.84, CAST('2021-05-21' AS DATE)),
            (1, 1, 'Michael Chen', 1437795.93, CAST('2021-05-24' AS DATE)),
            (1, 1, 'Michael Chen', 1438383.62, CAST('2021-05-25' AS DATE)),
            (1, 1, 'Michael Chen', 1439117.51, CAST('2021-05-26' AS DATE)),
            (1, 1, 'Michael Chen', 1432774.49, CAST('2021-05-27' AS DATE)),
            (1, 1, 'Michael Chen', 1436514.64, CAST('2021-05-28' AS DATE)),
            (1, 1, 'Michael Chen', 1428999.02, CAST('2021-06-01' AS DATE)),
            (1, 1, 'Michael Chen', 1431825.28, CAST('2021-06-02' AS DATE)),
            (1, 1, 'Michael Chen', 1424745.50, CAST('2021-06-03' AS DATE)),
            (1, 1, 'Michael Chen', 1439352.64, CAST('2021-06-04' AS DATE)),
            (1, 1, 'Michael Chen', 1443573.09, CAST('2021-06-07' AS DATE)),
            (1, 1, 'Michael Chen', 1448241.21, CAST('2021-06-08' AS DATE)),
            (1, 1, 'Michael Chen', 1452392.23, CAST('2021-06-09' AS DATE)),
            (1, 1, 'Michael Chen', 1470582.82, CAST('2021-06-10' AS DATE)),
            (1, 1, 'Michael Chen', 1471343.41, CAST('2021-06-11' AS DATE)),
            (1, 1, 'Michael Chen', 1479119.58, CAST('2021-06-14' AS DATE)),
            (1, 1, 'Michael Chen', 1474918.64, CAST('2021-06-15' AS DATE)),
            (1, 1, 'Michael Chen', 1473277.71, CAST('2021-06-16' AS DATE)),
            (1, 1, 'Michael Chen', 1488558.10, CAST('2021-06-17' AS DATE)),
            (1, 1, 'Michael Chen', 1476426.22, CAST('2021-06-18' AS DATE)),
            (1, 1, 'Michael Chen', 1487052.00, CAST('2021-06-21' AS DATE)),
            (1, 1, 'Michael Chen', 1500082.02, CAST('2021-06-22' AS DATE)),
            (1, 1, 'Michael Chen', 1498264.04, CAST('2021-06-23' AS DATE)),
            (1, 1, 'Michael Chen', 1499437.43, CAST('2021-06-24' AS DATE)),
            (1, 1, 'Michael Chen', 1496187.55, CAST('2021-06-25' AS DATE)),
            (1, 1, 'Michael Chen', 1508152.31, CAST('2021-06-28' AS DATE)),
            (1, 1, 'Michael Chen', 1511703.20, CAST('2021-06-29' AS DATE)),
            (1, 1, 'Michael Chen', 1510352.51, CAST('2021-06-30' AS DATE)),
            (1, 1, 'Michael Chen', 1516522.53, CAST('2021-07-01' AS DATE)),
            (1, 1, 'Michael Chen', 1537334.38, CAST('2021-07-02' AS DATE)),
            (1, 1, 'Michael Chen', 1552566.88, CAST('2021-07-06' AS DATE)),
            (1, 1, 'Michael Chen', 1559029.45, CAST('2021-07-07' AS DATE)),
            (1, 1, 'Michael Chen', 1553480.49, CAST('2021-07-08' AS DATE)),
            (1, 1, 'Michael Chen', 1559956.88, CAST('2021-07-09' AS DATE)),
            (1, 1, 'Michael Chen', 1562779.51, CAST('2021-07-12' AS DATE)),
            (1, 1, 'Michael Chen', 1558747.83, CAST('2021-07-13' AS DATE)),
            (1, 1, 'Michael Chen', 1559041.42, CAST('2021-07-14' AS DATE)),
            (1, 1, 'Michael Chen', 1548058.57, CAST('2021-07-15' AS DATE)),
            (1, 1, 'Michael Chen', 1536813.76, CAST('2021-07-16' AS DATE)),
            (1, 1, 'Michael Chen', 1521799.43, CAST('2021-07-19' AS DATE)),
            (1, 1, 'Michael Chen', 1537827.27, CAST('2021-07-20' AS DATE)),
            (1, 1, 'Michael Chen', 1548311.86, CAST('2021-07-21' AS DATE)),
            (1, 1, 'Michael Chen', 1561595.91, CAST('2021-07-22' AS DATE)),
            (1, 1, 'Michael Chen', 1575727.88, CAST('2021-07-23' AS DATE)),
            (1, 1, 'Michael Chen', 1577833.30, CAST('2021-07-26' AS DATE)),
            (1, 1, 'Michael Chen', 1565920.04, CAST('2021-07-27' AS DATE)),
            (1, 1, 'Michael Chen', 1568565.42, CAST('2021-07-28' AS DATE)),
            (1, 1, 'Michael Chen', 1568725.30, CAST('2021-07-29' AS DATE)),
            (1, 1, 'Michael Chen', 1536988.64, CAST('2021-07-30' AS DATE)),
            (1, 1, 'Michael Chen', 1536969.18, CAST('2021-08-02' AS DATE)),
            (1, 1, 'Michael Chen', 1551175.29, CAST('2021-08-03' AS DATE)),
            (1, 1, 'Michael Chen', 1546971.81, CAST('2021-08-04' AS DATE)),
            (1, 1, 'Michael Chen', 1556250.83, CAST('2021-08-05' AS DATE)),
            (1, 1, 'Michael Chen', 1552341.82, CAST('2021-08-06' AS DATE)),
            (1, 1, 'Michael Chen', 1550919.54, CAST('2021-08-09' AS DATE)),
            (1, 1, 'Michael Chen', 1545148.96, CAST('2021-08-10' AS DATE)),
            (1, 1, 'Michael Chen', 1540770.37, CAST('2021-08-11' AS DATE)),
            (1, 1, 'Michael Chen', 1549461.12, CAST('2021-08-12' AS DATE)),
            (1, 1, 'Michael Chen', 1554513.73, CAST('2021-08-13' AS DATE)),
            (1, 1, 'Michael Chen', 1560067.24, CAST('2021-08-16' AS DATE)),
            (1, 1, 'Michael Chen', 1551305.56, CAST('2021-08-17' AS DATE)),
            (1, 1, 'Michael Chen', 1533903.43, CAST('2021-08-18' AS DATE)),
            (1, 1, 'Michael Chen', 1542092.47, CAST('2021-08-19' AS DATE)),
            (1, 1, 'Michael Chen', 1560379.35, CAST('2021-08-20' AS DATE)),
            (1, 1, 'Michael Chen', 1576158.51, CAST('2021-08-23' AS DATE)),
            (1, 1, 'Michael Chen', 1578016.52, CAST('2021-08-24' AS DATE)),
            (1, 1, 'Michael Chen', 1578476.21, CAST('2021-08-25' AS DATE)),
            (1, 1, 'Michael Chen', 1571911.75, CAST('2021-08-26' AS DATE)),
            (1, 1, 'Michael Chen', 1582819.45, CAST('2021-08-27' AS DATE)),
            (1, 1, 'Michael Chen', 1598525.19, CAST('2021-08-30' AS DATE)),
            (1, 1, 'Michael Chen', 1600131.55, CAST('2021-08-31' AS DATE)),
            (1, 1, 'Michael Chen', 1601980.36, CAST('2021-09-01' AS DATE)),
            (1, 1, 'Michael Chen', 1604639.18, CAST('2021-09-02' AS DATE)),
            (1, 1, 'Michael Chen', 1606996.16, CAST('2021-09-03' AS DATE)),
            (1, 1, 'Michael Chen', 1604819.83, CAST('2021-09-07' AS DATE)),
            (1, 1, 'Michael Chen', 1604428.62, CAST('2021-09-08' AS DATE)),
            (1, 1, 'Michael Chen', 1591438.55, CAST('2021-09-09' AS DATE)),
            (1, 1, 'Michael Chen', 1581737.87, CAST('2021-09-10' AS DATE)),
            (1, 1, 'Michael Chen', 1580309.68, CAST('2021-09-13' AS DATE)),
            (1, 1, 'Michael Chen', 1579165.66, CAST('2021-09-14' AS DATE)),
            (1, 1, 'Michael Chen', 1594174.67, CAST('2021-09-15' AS DATE)),
            (1, 1, 'Michael Chen', 1594116.59, CAST('2021-09-16' AS DATE)),
            (1, 1, 'Michael Chen', 1580618.58, CAST('2021-09-17' AS DATE)),
            (1, 1, 'Michael Chen', 1549137.63, CAST('2021-09-20' AS DATE)),
            (1, 1, 'Michael Chen', 1548922.86, CAST('2021-09-21' AS DATE)),
            (1, 1, 'Michael Chen', 1564245.66, CAST('2021-09-22' AS DATE)),
            (1, 1, 'Michael Chen', 1579292.54, CAST('2021-09-23' AS DATE)),
            (1, 1, 'Michael Chen', 1578292.40, CAST('2021-09-24' AS DATE)),
            (1, 1, 'Michael Chen', 1564623.76, CAST('2021-09-27' AS DATE)),
            (1, 1, 'Michael Chen', 1524844.42, CAST('2021-09-28' AS DATE)),
            (1, 1, 'Michael Chen', 1526023.82, CAST('2021-09-29' AS DATE)),
            (1, 1, 'Michael Chen', 1512888.53, CAST('2021-09-30' AS DATE)),
            (1, 1, 'Michael Chen', 1527490.23, CAST('2021-10-01' AS DATE)),
            (1, 1, 'Michael Chen', 1497807.68, CAST('2021-10-04' AS DATE)),
            (1, 1, 'Michael Chen', 1515534.15, CAST('2021-10-05' AS DATE)),
            (1, 1, 'Michael Chen', 1526659.19, CAST('2021-10-06' AS DATE)),
            (1, 1, 'Michael Chen', 1541685.71, CAST('2021-10-07' AS DATE)),
            (1, 1, 'Michael Chen', 1537074.18, CAST('2021-10-08' AS DATE)),
            (1, 1, 'Michael Chen', 1525806.88, CAST('2021-10-11' AS DATE)),
            (1, 1, 'Michael Chen', 1522234.55, CAST('2021-10-12' AS DATE)),
            (1, 1, 'Michael Chen', 1532451.91, CAST('2021-10-13' AS DATE)),
            (1, 1, 'Michael Chen', 1556168.36, CAST('2021-10-14' AS DATE)),
            (1, 1, 'Michael Chen', 1574294.09, CAST('2021-10-15' AS DATE)),
            (1, 1, 'Michael Chen', 1581524.65, CAST('2021-10-18' AS DATE)),
            (1, 1, 'Michael Chen', 1590572.65, CAST('2021-10-19' AS DATE)),
            (1, 1, 'Michael Chen', 1592284.47, CAST('2021-10-20' AS DATE)),
            (1, 1, 'Michael Chen', 1602325.19, CAST('2021-10-21' AS DATE)),
            (1, 1, 'Michael Chen', 1590779.93, CAST('2021-10-22' AS DATE)),
            (1, 1, 'Michael Chen', 1592566.78, CAST('2021-10-25' AS DATE)),
            (1, 1, 'Michael Chen', 1605732.51, CAST('2021-10-26' AS DATE)),
            (1, 1, 'Michael Chen', 1615159.47, CAST('2021-10-27' AS DATE)),
            (1, 1, 'Michael Chen', 1631640.44, CAST('2021-10-28' AS DATE)),
            (1, 1, 'Michael Chen', 1636962.12, CAST('2021-10-29' AS DATE)),
            (1, 1, 'Michael Chen', 1631285.76, CAST('2021-11-01' AS DATE)),
            (1, 1, 'Michael Chen', 1640262.04, CAST('2021-11-02' AS DATE)),
            (1, 1, 'Michael Chen', 1654641.28, CAST('2021-11-03' AS DATE)),
            (1, 1, 'Michael Chen', 1674727.92, CAST('2021-11-04' AS DATE)),
            (1, 1, 'Michael Chen', 1677663.26, CAST('2021-11-05' AS DATE)),
            (1, 1, 'Michael Chen', 1680001.04, CAST('2021-11-08' AS DATE)),
            (1, 1, 'Michael Chen', 1683719.13, CAST('2021-11-09' AS DATE)),
            (1, 1, 'Michael Chen', 1661061.31, CAST('2021-11-10' AS DATE)),
            (1, 1, 'Michael Chen', 1663495.86, CAST('2021-11-11' AS DATE)),
            (1, 1, 'Michael Chen', 1678883.17, CAST('2021-11-12' AS DATE)),
            (1, 1, 'Michael Chen', 1677666.67, CAST('2021-11-15' AS DATE)),
            (1, 1, 'Michael Chen', 1684885.63, CAST('2021-11-16' AS DATE)),
            (1, 1, 'Michael Chen', 1682325.95, CAST('2021-11-17' AS DATE)),
            (1, 1, 'Michael Chen', 1706088.94, CAST('2021-11-18' AS DATE)),
            (1, 1, 'Michael Chen', 1706111.68, CAST('2021-11-19' AS DATE)),
            (1, 1, 'Michael Chen', 1686498.25, CAST('2021-11-22' AS DATE)),
            (1, 1, 'Michael Chen', 1685049.78, CAST('2021-11-23' AS DATE)),
            (1, 1, 'Michael Chen', 1689250.60, CAST('2021-11-24' AS DATE)),
            (1, 1, 'Michael Chen', 1655004.06, CAST('2021-11-26' AS DATE)),
            (1, 1, 'Michael Chen', 1679478.21, CAST('2021-11-29' AS DATE)),
            (1, 1, 'Michael Chen', 1649234.94, CAST('2021-11-30' AS DATE)),
            (1, 1, 'Michael Chen', 1631624.33, CAST('2021-12-01' AS DATE)),
            (1, 1, 'Michael Chen', 1642114.13, CAST('2021-12-02' AS DATE)),
            (1, 1, 'Michael Chen', 1621230.34, CAST('2021-12-03' AS DATE)),
            (1, 1, 'Michael Chen', 1635482.11, CAST('2021-12-06' AS DATE)),
            (1, 1, 'Michael Chen', 1676833.09, CAST('2021-12-07' AS DATE)),
            (1, 1, 'Michael Chen', 1679611.45, CAST('2021-12-08' AS DATE)),
            (1, 1, 'Michael Chen', 1665523.60, CAST('2021-12-09' AS DATE)),
            (1, 1, 'Michael Chen', 1676960.65, CAST('2021-12-10' AS DATE)),
            (1, 1, 'Michael Chen', 1661105.87, CAST('2021-12-13' AS DATE)),
            (1, 1, 'Michael Chen', 1643261.61, CAST('2021-12-14' AS DATE)),
            (1, 1, 'Michael Chen', 1679172.31, CAST('2021-12-15' AS DATE)),
            (1, 1, 'Michael Chen', 1650014.04, CAST('2021-12-16' AS DATE)),
            (1, 1, 'Michael Chen', 1643580.72, CAST('2021-12-17' AS DATE)),
            (1, 1, 'Michael Chen', 1625234.09, CAST('2021-12-20' AS DATE)),
            (1, 1, 'Michael Chen', 1655259.40, CAST('2021-12-21' AS DATE)),
            (1, 1, 'Michael Chen', 1672747.69, CAST('2021-12-22' AS DATE)),
            (1, 1, 'Michael Chen', 1680077.25, CAST('2021-12-23' AS DATE)),
            (1, 1, 'Michael Chen', 1699187.26, CAST('2021-12-27' AS DATE)),
            (1, 1, 'Michael Chen', 1696712.94, CAST('2021-12-28' AS DATE)),
            (1, 1, 'Michael Chen', 1695775.38, CAST('2021-12-29' AS DATE)),
            (1, 1, 'Michael Chen', 1690314.93, CAST('2021-12-30' AS DATE)),
            (1, 1, 'Michael Chen', 1680051.06, CAST('2021-12-31' AS DATE)),
            (1, 1, 'Michael Chen', 1688845.80, CAST('2022-01-03' AS DATE)),
            (1, 1, 'Michael Chen', 1669844.16, CAST('2022-01-04' AS DATE)),
            (1, 1, 'Michael Chen', 1630799.70, CAST('2022-01-05' AS DATE)),
            (1, 1, 'Michael Chen', 1622827.71, CAST('2022-01-06' AS DATE)),
            (1, 1, 'Michael Chen', 1615269.54, CAST('2022-01-07' AS DATE)),
            (1, 1, 'Michael Chen', 1616207.45, CAST('2022-01-10' AS DATE)),
            (1, 1, 'Michael Chen', 1633566.98, CAST('2022-01-11' AS DATE)),
            (1, 1, 'Michael Chen', 1637046.34, CAST('2022-01-12' AS DATE)),
            (1, 1, 'Michael Chen', 1597981.79, CAST('2022-01-13' AS DATE)),
            (1, 1, 'Michael Chen', 1606422.88, CAST('2022-01-14' AS DATE)),
            (1, 1, 'Michael Chen', 1573459.94, CAST('2022-01-18' AS DATE)),
            (1, 1, 'Michael Chen', 1559751.00, CAST('2022-01-19' AS DATE)),
            (1, 1, 'Michael Chen', 1538466.89, CAST('2022-01-20' AS DATE)),
            (1, 1, 'Michael Chen', 1498485.93, CAST('2022-01-21' AS DATE)),
            (1, 1, 'Michael Chen', 1504684.59, CAST('2022-01-24' AS DATE)),
            (1, 1, 'Michael Chen', 1475286.52, CAST('2022-01-25' AS DATE)),
            (1, 1, 'Michael Chen', 1479876.38, CAST('2022-01-26' AS DATE)),
            (1, 1, 'Michael Chen', 1479275.41, CAST('2022-01-27' AS DATE)),
            (1, 1, 'Michael Chen', 1519050.57, CAST('2022-01-28' AS DATE)),
            (1, 1, 'Michael Chen', 1550659.38, CAST('2022-01-31' AS DATE)),
            (1, 1, 'Michael Chen', 1556884.63, CAST('2022-02-01' AS DATE)),
            (1, 1, 'Michael Chen', 1570419.83, CAST('2022-02-02' AS DATE)),
            (1, 1, 'Michael Chen', 1515274.03, CAST('2022-02-03' AS DATE)),
            (1, 1, 'Michael Chen', 1560826.71, CAST('2022-02-04' AS DATE)),
            (1, 1, 'Michael Chen', 1555022.08, CAST('2022-02-07' AS DATE)),
            (1, 1, 'Michael Chen', 1573782.07, CAST('2022-02-08' AS DATE)),
            (1, 1, 'Michael Chen', 1595993.57, CAST('2022-02-09' AS DATE)),
            (1, 1, 'Michael Chen', 1565087.27, CAST('2022-02-10' AS DATE)),
            (1, 1, 'Michael Chen', 1526047.33, CAST('2022-02-11' AS DATE)),
            (1, 1, 'Michael Chen', 1525722.17, CAST('2022-02-14' AS DATE)),
            (1, 1, 'Michael Chen', 1552252.75, CAST('2022-02-15' AS DATE)),
            (1, 1, 'Michael Chen', 1555580.13, CAST('2022-02-16' AS DATE)),
            (1, 1, 'Michael Chen', 1517201.11, CAST('2022-02-17' AS DATE)),
            (1, 1, 'Michael Chen', 1502287.62, CAST('2022-02-18' AS DATE)),
            (1, 1, 'Michael Chen', 1489620.46, CAST('2022-02-22' AS DATE)),
            (1, 1, 'Michael Chen', 1456768.08, CAST('2022-02-23' AS DATE)),
            (1, 1, 'Michael Chen', 1498963.96, CAST('2022-02-24' AS DATE)),
            (1, 1, 'Michael Chen', 1527933.79, CAST('2022-02-25' AS DATE)),
            (1, 1, 'Michael Chen', 1526325.78, CAST('2022-02-28' AS DATE)),
            (1, 1, 'Michael Chen', 1505295.87, CAST('2022-03-01' AS DATE)),
            (1, 1, 'Michael Chen', 1528867.18, CAST('2022-03-02' AS DATE)),
            (1, 1, 'Michael Chen', 1512455.93, CAST('2022-03-03' AS DATE)),
            (1, 1, 'Michael Chen', 1495712.07, CAST('2022-03-04' AS DATE)),
            (1, 1, 'Michael Chen', 1442878.85, CAST('2022-03-07' AS DATE)),
            (1, 1, 'Michael Chen', 1427514.95, CAST('2022-03-08' AS DATE)),
            (1, 1, 'Michael Chen', 1471054.19, CAST('2022-03-09' AS DATE)),
            (1, 1, 'Michael Chen', 1479503.75, CAST('2022-03-10' AS DATE)),
            (1, 1, 'Michael Chen', 1459558.71, CAST('2022-03-11' AS DATE)),
            (1, 1, 'Michael Chen', 1443272.60, CAST('2022-03-14' AS DATE)),
            (1, 1, 'Michael Chen', 1486698.50, CAST('2022-03-15' AS DATE)),
            (1, 1, 'Michael Chen', 1526121.91, CAST('2022-03-16' AS DATE)),
            (1, 1, 'Michael Chen', 1548383.50, CAST('2022-03-17' AS DATE)),
            (1, 1, 'Michael Chen', 1574223.96, CAST('2022-03-18' AS DATE)),
            (1, 1, 'Michael Chen', 1573065.22, CAST('2022-03-21' AS DATE)),
            (1, 1, 'Michael Chen', 1591858.14, CAST('2022-03-22' AS DATE)),
            (1, 1, 'Michael Chen', 1568563.25, CAST('2022-03-23' AS DATE)),
            (1, 1, 'Michael Chen', 1592255.74, CAST('2022-03-24' AS DATE)),
            (1, 1, 'Michael Chen', 1596513.44, CAST('2022-03-25' AS DATE)),
            (1, 1, 'Michael Chen', 1620057.62, CAST('2022-03-28' AS DATE)),
            (1, 1, 'Michael Chen', 1636551.22, CAST('2022-03-29' AS DATE)),
            (1, 1, 'Michael Chen', 1623165.55, CAST('2022-03-30' AS DATE)),
            (1, 1, 'Michael Chen', 1597338.46, CAST('2022-03-31' AS DATE)),
            (1, 1, 'Michael Chen', 1603868.16, CAST('2022-04-01' AS DATE)),
            (1, 1, 'Michael Chen', 1623801.49, CAST('2022-04-04' AS DATE)),
            (1, 1, 'Michael Chen', 1600025.19, CAST('2022-04-05' AS DATE)),
            (1, 1, 'Michael Chen', 1572003.69, CAST('2022-04-06' AS DATE)),
            (1, 1, 'Michael Chen', 1579737.83, CAST('2022-04-07' AS DATE)),
            (1, 1, 'Michael Chen', 1565571.48, CAST('2022-04-08' AS DATE)),
            (1, 1, 'Michael Chen', 1527347.81, CAST('2022-04-11' AS DATE)),
            (1, 1, 'Michael Chen', 1517651.50, CAST('2022-04-12' AS DATE)),
            (1, 1, 'Michael Chen', 1543326.29, CAST('2022-04-13' AS DATE)),
            (1, 1, 'Michael Chen', 1516312.77, CAST('2022-04-14' AS DATE)),
            (1, 1, 'Michael Chen', 1516415.30, CAST('2022-04-18' AS DATE)),
            (1, 1, 'Michael Chen', 1545360.11, CAST('2022-04-19' AS DATE)),
            (1, 1, 'Michael Chen', 1539879.06, CAST('2022-04-20' AS DATE)),
            (1, 1, 'Michael Chen', 1506949.66, CAST('2022-04-21' AS DATE)),
            (1, 1, 'Michael Chen', 1464139.23, CAST('2022-04-22' AS DATE)),
            (1, 1, 'Michael Chen', 1480865.78, CAST('2022-04-25' AS DATE)),
            (1, 1, 'Michael Chen', 1431514.08, CAST('2022-04-26' AS DATE)),
            (1, 1, 'Michael Chen', 1442996.52, CAST('2022-04-27' AS DATE)),
            (1, 1, 'Michael Chen', 1482486.87, CAST('2022-04-28' AS DATE)),
            (1, 1, 'Michael Chen', 1398816.49, CAST('2022-04-29' AS DATE)),
            (1, 1, 'Michael Chen', 1411210.96, CAST('2022-05-02' AS DATE)),
            (1, 1, 'Michael Chen', 1411172.74, CAST('2022-05-03' AS DATE)),
            (1, 1, 'Michael Chen', 1447290.33, CAST('2022-05-04' AS DATE)),
            (1, 1, 'Michael Chen', 1385304.88, CAST('2022-05-05' AS DATE)),
            (1, 1, 'Michael Chen', 1373724.09, CAST('2022-05-06' AS DATE)),
            (1, 1, 'Michael Chen', 1321482.67, CAST('2022-05-09' AS DATE)),
            (1, 1, 'Michael Chen', 1331333.88, CAST('2022-05-10' AS DATE)),
            (1, 1, 'Michael Chen', 1301565.28, CAST('2022-05-11' AS DATE)),
            (1, 1, 'Michael Chen', 1300539.77, CAST('2022-05-12' AS DATE)),
            (1, 1, 'Michael Chen', 1338604.77, CAST('2022-05-13' AS DATE)),
            (1, 1, 'Michael Chen', 1333195.78, CAST('2022-05-16' AS DATE)),
            (1, 1, 'Michael Chen', 1365216.10, CAST('2022-05-17' AS DATE)),
            (1, 1, 'Michael Chen', 1304090.17, CAST('2022-05-18' AS DATE)),
            (1, 1, 'Michael Chen', 1301733.77, CAST('2022-05-19' AS DATE)),
            (1, 1, 'Michael Chen', 1304276.56, CAST('2022-05-20' AS DATE)),
            (1, 1, 'Michael Chen', 1324857.86, CAST('2022-05-23' AS DATE)),
            (1, 1, 'Michael Chen', 1311255.46, CAST('2022-05-24' AS DATE)),
            (1, 1, 'Michael Chen', 1326276.85, CAST('2022-05-25' AS DATE)),
            (1, 1, 'Michael Chen', 1352234.58, CAST('2022-05-26' AS DATE)),
            (1, 1, 'Michael Chen', 1388372.10, CAST('2022-05-27' AS DATE)),
            (1, 1, 'Michael Chen', 1389553.41, CAST('2022-05-31' AS DATE)),
            (1, 1, 'Michael Chen', 1383506.54, CAST('2022-06-01' AS DATE)),
            (1, 1, 'Michael Chen', 1409613.45, CAST('2022-06-02' AS DATE)),
            (1, 1, 'Michael Chen', 1384725.48, CAST('2022-06-03' AS DATE)),
            (1, 1, 'Michael Chen', 1389643.42, CAST('2022-06-06' AS DATE)),
            (1, 1, 'Michael Chen', 1399430.65, CAST('2022-06-07' AS DATE)),
            (1, 1, 'Michael Chen', 1385127.31, CAST('2022-06-08' AS DATE)),
            (1, 1, 'Michael Chen', 1348433.04, CAST('2022-06-09' AS DATE)),
            (1, 1, 'Michael Chen', 1300721.28, CAST('2022-06-10' AS DATE)),
            (1, 1, 'Michael Chen', 1246599.79, CAST('2022-06-13' AS DATE)),
            (1, 1, 'Michael Chen', 1242985.70, CAST('2022-06-14' AS DATE)),
            (1, 1, 'Michael Chen', 1272781.27, CAST('2022-06-15' AS DATE)),
            (1, 1, 'Michael Chen', 1235015.18, CAST('2022-06-16' AS DATE)),
            (1, 1, 'Michael Chen', 1245472.22, CAST('2022-06-17' AS DATE)),
            (1, 1, 'Michael Chen', 1277079.98, CAST('2022-06-21' AS DATE)),
            (1, 1, 'Michael Chen', 1279563.79, CAST('2022-06-22' AS DATE)),
            (1, 1, 'Michael Chen', 1303972.89, CAST('2022-06-23' AS DATE)),
            (1, 1, 'Michael Chen', 1343697.56, CAST('2022-06-24' AS DATE)),
            (1, 1, 'Michael Chen', 1332632.28, CAST('2022-06-27' AS DATE)),
            (1, 1, 'Michael Chen', 1294648.03, CAST('2022-06-28' AS DATE)),
            (1, 1, 'Michael Chen', 1302510.90, CAST('2022-06-29' AS DATE)),
            (1, 1, 'Michael Chen', 1287431.69, CAST('2022-06-30' AS DATE)),
            (1, 1, 'Michael Chen', 1304339.55, CAST('2022-07-01' AS DATE)),
            (1, 1, 'Michael Chen', 1317213.46, CAST('2022-07-05' AS DATE)),
            (1, 1, 'Michael Chen', 1326010.63, CAST('2022-07-06' AS DATE)),
            (1, 1, 'Michael Chen', 1343518.75, CAST('2022-07-07' AS DATE)),
            (1, 1, 'Michael Chen', 1341638.41, CAST('2022-07-08' AS DATE)),
            (1, 1, 'Michael Chen', 1321688.31, CAST('2022-07-11' AS DATE)),
            (1, 1, 'Michael Chen', 1297082.83, CAST('2022-07-12' AS DATE)),
            (1, 1, 'Michael Chen', 1293855.15, CAST('2022-07-13' AS DATE)),
            (1, 1, 'Michael Chen', 1293977.52, CAST('2022-07-14' AS DATE)),
            (1, 1, 'Michael Chen', 1319237.12, CAST('2022-07-15' AS DATE)),
            (1, 1, 'Michael Chen', 1307685.66, CAST('2022-07-18' AS DATE)),
            (1, 1, 'Michael Chen', 1342685.41, CAST('2022-07-19' AS DATE)),
            (1, 1, 'Michael Chen', 1357947.20, CAST('2022-07-20' AS DATE)),
            (1, 1, 'Michael Chen', 1374386.85, CAST('2022-07-21' AS DATE)),
            (1, 1, 'Michael Chen', 1357015.82, CAST('2022-07-22' AS DATE)),
            (1, 1, 'Michael Chen', 1354100.52, CAST('2022-07-25' AS DATE)),
            (1, 1, 'Michael Chen', 1328201.85, CAST('2022-07-26' AS DATE)),
            (1, 1, 'Michael Chen', 1376842.12, CAST('2022-07-27' AS DATE)),
            (1, 1, 'Michael Chen', 1396101.78, CAST('2022-07-28' AS DATE)),
            (1, 1, 'Michael Chen', 1432997.65, CAST('2022-07-29' AS DATE)),
            (1, 1, 'Michael Chen', 1427672.10, CAST('2022-08-01' AS DATE)),
            (1, 1, 'Michael Chen', 1418292.83, CAST('2022-08-02' AS DATE)),
            (1, 1, 'Michael Chen', 1449124.38, CAST('2022-08-03' AS DATE)),
            (1, 1, 'Michael Chen', 1456195.02, CAST('2022-08-04' AS DATE)),
            (1, 1, 'Michael Chen', 1450848.17, CAST('2022-08-05' AS DATE)),
            (1, 1, 'Michael Chen', 1443267.83, CAST('2022-08-08' AS DATE)),
            (1, 1, 'Michael Chen', 1436710.95, CAST('2022-08-09' AS DATE)),
            (1, 1, 'Michael Chen', 1470987.72, CAST('2022-08-10' AS DATE)),
            (1, 1, 'Michael Chen', 1462196.01, CAST('2022-08-11' AS DATE)),
            (1, 1, 'Michael Chen', 1487867.93, CAST('2022-08-12' AS DATE)),
            (1, 1, 'Michael Chen', 1493450.05, CAST('2022-08-15' AS DATE)),
            (1, 1, 'Michael Chen', 1495112.50, CAST('2022-08-16' AS DATE)),
            (1, 1, 'Michael Chen', 1481452.62, CAST('2022-08-17' AS DATE)),
            (1, 1, 'Michael Chen', 1481907.67, CAST('2022-08-18' AS DATE)),
            (1, 1, 'Michael Chen', 1460067.70, CAST('2022-08-19' AS DATE)),
            (1, 1, 'Michael Chen', 1423974.32, CAST('2022-08-22' AS DATE)),
            (1, 1, 'Michael Chen', 1418988.26, CAST('2022-08-23' AS DATE)),
            (1, 1, 'Michael Chen', 1421425.07, CAST('2022-08-24' AS DATE)),
            (1, 1, 'Michael Chen', 1443985.02, CAST('2022-08-25' AS DATE)),
            (1, 1, 'Michael Chen', 1388758.70, CAST('2022-08-26' AS DATE)),
            (1, 1, 'Michael Chen', 1377154.12, CAST('2022-08-29' AS DATE)),
            (1, 1, 'Michael Chen', 1363967.65, CAST('2022-08-30' AS DATE)),
            (1, 1, 'Michael Chen', 1352277.11, CAST('2022-08-31' AS DATE)),
            (1, 1, 'Michael Chen', 1356067.37, CAST('2022-09-01' AS DATE)),
            (1, 1, 'Michael Chen', 1340757.74, CAST('2022-09-02' AS DATE)),
            (1, 1, 'Michael Chen', 1332424.68, CAST('2022-09-06' AS DATE)),
            (1, 1, 'Michael Chen', 1359008.38, CAST('2022-09-07' AS DATE)),
            (1, 1, 'Michael Chen', 1369466.09, CAST('2022-09-08' AS DATE)),
            (1, 1, 'Michael Chen', 1394278.27, CAST('2022-09-09' AS DATE)),
            (1, 1, 'Michael Chen', 1410682.79, CAST('2022-09-12' AS DATE)),
            (1, 1, 'Michael Chen', 1339986.87, CAST('2022-09-13' AS DATE)),
            (1, 1, 'Michael Chen', 1345901.29, CAST('2022-09-14' AS DATE)),
            (1, 1, 'Michael Chen', 1329122.86, CAST('2022-09-15' AS DATE)),
            (1, 1, 'Michael Chen', 1318371.63, CAST('2022-09-16' AS DATE)),
            (1, 1, 'Michael Chen', 1322986.38, CAST('2022-09-19' AS DATE)),
            (1, 1, 'Michael Chen', 1306594.32, CAST('2022-09-20' AS DATE)),
            (1, 1, 'Michael Chen', 1282133.26, CAST('2022-09-21' AS DATE)),
            (1, 1, 'Michael Chen', 1276376.58, CAST('2022-09-22' AS DATE)),
            (1, 1, 'Michael Chen', 1256427.60, CAST('2022-09-23' AS DATE)),
            (1, 1, 'Michael Chen', 1250476.96, CAST('2022-09-26' AS DATE)),
            (1, 1, 'Michael Chen', 1246877.89, CAST('2022-09-27' AS DATE)),
            (1, 1, 'Michael Chen', 1275290.24, CAST('2022-09-28' AS DATE)),
            (1, 1, 'Michael Chen', 1251239.37, CAST('2022-09-29' AS DATE)),
            (1, 1, 'Michael Chen', 1232128.42, CAST('2022-09-30' AS DATE)),
            (1, 1, 'Michael Chen', 1264304.51, CAST('2022-10-03' AS DATE)),
            (1, 1, 'Michael Chen', 1306358.14, CAST('2022-10-04' AS DATE)),
            (1, 1, 'Michael Chen', 1305980.00, CAST('2022-10-05' AS DATE)),
            (1, 1, 'Michael Chen', 1293649.59, CAST('2022-10-06' AS DATE)),
            (1, 1, 'Michael Chen', 1246589.08, CAST('2022-10-07' AS DATE)),
            (1, 1, 'Michael Chen', 1232710.20, CAST('2022-10-10' AS DATE)),
            (1, 1, 'Michael Chen', 1224043.12, CAST('2022-10-11' AS DATE)),
            (1, 1, 'Michael Chen', 1222638.69, CAST('2022-10-12' AS DATE)),
            (1, 1, 'Michael Chen', 1250322.14, CAST('2022-10-13' AS DATE)),
            (1, 1, 'Michael Chen', 1217789.55, CAST('2022-10-14' AS DATE)),
            (1, 1, 'Michael Chen', 1259681.07, CAST('2022-10-17' AS DATE)),
            (1, 1, 'Michael Chen', 1273149.66, CAST('2022-10-18' AS DATE)),
            (1, 1, 'Michael Chen', 1260679.13, CAST('2022-10-19' AS DATE)),
            (1, 1, 'Michael Chen', 1254704.52, CAST('2022-10-20' AS DATE)),
            (1, 1, 'Michael Chen', 1287188.20, CAST('2022-10-21' AS DATE)),
            (1, 1, 'Michael Chen', 1304387.03, CAST('2022-10-24' AS DATE)),
            (1, 1, 'Michael Chen', 1321869.42, CAST('2022-10-25' AS DATE)),
            (1, 1, 'Michael Chen', 1290177.27, CAST('2022-10-26' AS DATE)),
            (1, 1, 'Michael Chen', 1272011.32, CAST('2022-10-27' AS DATE)),
            (1, 1, 'Michael Chen', 1284550.32, CAST('2022-10-28' AS DATE)),
            (1, 1, 'Michael Chen', 1273957.88, CAST('2022-10-31' AS DATE)),
            (1, 1, 'Michael Chen', 1256578.14, CAST('2022-11-01' AS DATE)),
            (1, 1, 'Michael Chen', 1220475.77, CAST('2022-11-02' AS DATE)),
            (1, 1, 'Michael Chen', 1202848.46, CAST('2022-11-03' AS DATE)),
            (1, 1, 'Michael Chen', 1223599.61, CAST('2022-11-04' AS DATE)),
            (1, 1, 'Michael Chen', 1237373.65, CAST('2022-11-07' AS DATE)),
            (1, 1, 'Michael Chen', 1241740.50, CAST('2022-11-08' AS DATE)),
            (1, 1, 'Michael Chen', 1213993.28, CAST('2022-11-09' AS DATE)),
            (1, 1, 'Michael Chen', 1294195.11, CAST('2022-11-10' AS DATE)),
            (1, 1, 'Michael Chen', 1310610.05, CAST('2022-11-11' AS DATE)),
            (1, 1, 'Michael Chen', 1295212.84, CAST('2022-11-14' AS DATE)),
            (1, 1, 'Michael Chen', 1301981.94, CAST('2022-11-15' AS DATE)),
            (1, 1, 'Michael Chen', 1292212.23, CAST('2022-11-16' AS DATE)),
            (1, 1, 'Michael Chen', 1284963.25, CAST('2022-11-17' AS DATE)),
            (1, 1, 'Michael Chen', 1288187.74, CAST('2022-11-18' AS DATE)),
            (1, 1, 'Michael Chen', 1283529.28, CAST('2022-11-21' AS DATE)),
            (1, 1, 'Michael Chen', 1299311.57, CAST('2022-11-22' AS DATE)),
            (1, 1, 'Michael Chen', 1309545.77, CAST('2022-11-23' AS DATE)),
            (1, 1, 'Michael Chen', 1309093.42, CAST('2022-11-25' AS DATE)),
            (1, 1, 'Michael Chen', 1292195.05, CAST('2022-11-28' AS DATE)),
            (1, 1, 'Michael Chen', 1285589.78, CAST('2022-11-29' AS DATE)),
            (1, 1, 'Michael Chen', 1336608.36, CAST('2022-11-30' AS DATE)),
            (1, 1, 'Michael Chen', 1335209.37, CAST('2022-12-01' AS DATE)),
            (1, 1, 'Michael Chen', 1332492.85, CAST('2022-12-02' AS DATE)),
            (1, 1, 'Michael Chen', 1307468.55, CAST('2022-12-05' AS DATE)),
            (1, 1, 'Michael Chen', 1284713.19, CAST('2022-12-06' AS DATE)),
            (1, 1, 'Michael Chen', 1286000.95, CAST('2022-12-07' AS DATE)),
            (1, 1, 'Michael Chen', 1302399.98, CAST('2022-12-08' AS DATE)),
            (1, 1, 'Michael Chen', 1289280.27, CAST('2022-12-09' AS DATE)),
            (1, 1, 'Michael Chen', 1311775.36, CAST('2022-12-12' AS DATE)),
            (1, 1, 'Michael Chen', 1326903.31, CAST('2022-12-13' AS DATE)),
            (1, 1, 'Michael Chen', 1321688.09, CAST('2022-12-14' AS DATE)),
            (1, 1, 'Michael Chen', 1286400.51, CAST('2022-12-15' AS DATE)),
            (1, 1, 'Michael Chen', 1269870.48, CAST('2022-12-16' AS DATE)),
            (1, 1, 'Michael Chen', 1253090.62, CAST('2022-12-19' AS DATE)),
            (1, 1, 'Michael Chen', 1255729.34, CAST('2022-12-20' AS DATE)),
            (1, 1, 'Michael Chen', 1273828.25, CAST('2022-12-21' AS DATE)),
            (1, 1, 'Michael Chen', 1251109.51, CAST('2022-12-22' AS DATE)),
            (1, 1, 'Michael Chen', 1256796.23, CAST('2022-12-23' AS DATE)),
            (1, 1, 'Michael Chen', 1244610.95, CAST('2022-12-27' AS DATE)),
            (1, 1, 'Michael Chen', 1231588.07, CAST('2022-12-28' AS DATE)),
            (1, 1, 'Michael Chen', 1256971.67, CAST('2022-12-29' AS DATE)),
            (1, 1, 'Michael Chen', 1253123.51, CAST('2022-12-30' AS DATE)),
            (1, 1, 'Michael Chen', 1252509.80, CAST('2023-01-03' AS DATE)),
            (1, 1, 'Michael Chen', 1246021.34, CAST('2023-01-04' AS DATE)),
            (1, 1, 'Michael Chen', 1225214.71, CAST('2023-01-05' AS DATE)),
            (1, 1, 'Michael Chen', 1249067.97, CAST('2023-01-06' AS DATE)),
            (1, 1, 'Michael Chen', 1250757.31, CAST('2023-01-09' AS DATE)),
            (1, 1, 'Michael Chen', 1264750.00, CAST('2023-01-10' AS DATE)),
            (1, 1, 'Michael Chen', 1291087.91, CAST('2023-01-11' AS DATE)),
            (1, 1, 'Michael Chen', 1297264.39, CAST('2023-01-12' AS DATE)),
            (1, 1, 'Michael Chen', 1307904.12, CAST('2023-01-13' AS DATE)),
            (1, 1, 'Michael Chen', 1304659.33, CAST('2023-01-17' AS DATE)),
            (1, 1, 'Michael Chen', 1285537.62, CAST('2023-01-18' AS DATE)),
            (1, 1, 'Michael Chen', 1273157.09, CAST('2023-01-19' AS DATE)),
            (1, 1, 'Michael Chen', 1302983.75, CAST('2023-01-20' AS DATE)),
            (1, 1, 'Michael Chen', 1316480.21, CAST('2023-01-23' AS DATE)),
            (1, 1, 'Michael Chen', 1311081.93, CAST('2023-01-24' AS DATE)),
            (1, 1, 'Michael Chen', 1311981.91, CAST('2023-01-25' AS DATE)),
            (1, 1, 'Michael Chen', 1331508.53, CAST('2023-01-26' AS DATE)),
            (1, 1, 'Michael Chen', 1338383.68, CAST('2023-01-27' AS DATE)),
            (1, 1, 'Michael Chen', 1316793.93, CAST('2023-01-30' AS DATE)),
            (1, 1, 'Michael Chen', 1339934.67, CAST('2023-01-31' AS DATE)),
            (1, 1, 'Michael Chen', 1359810.33, CAST('2023-02-01' AS DATE)),
            (1, 1, 'Michael Chen', 1396544.19, CAST('2023-02-02' AS DATE)),
            (1, 1, 'Michael Chen', 1362390.10, CAST('2023-02-03' AS DATE)),
            (1, 1, 'Michael Chen', 1352910.57, CAST('2023-02-06' AS DATE)),
            (1, 1, 'Michael Chen', 1375612.33, CAST('2023-02-07' AS DATE)),
            (1, 1, 'Michael Chen', 1363365.84, CAST('2023-02-08' AS DATE)),
            (1, 1, 'Michael Chen', 1349492.76, CAST('2023-02-09' AS DATE)),
            (1, 1, 'Michael Chen', 1348715.67, CAST('2023-02-10' AS DATE)),
            (1, 1, 'Michael Chen', 1371048.68, CAST('2023-02-13' AS DATE)),
            (1, 1, 'Michael Chen', 1373272.64, CAST('2023-02-14' AS DATE)),
            (1, 1, 'Michael Chen', 1374285.20, CAST('2023-02-15' AS DATE)),
            (1, 1, 'Michael Chen', 1348644.91, CAST('2023-02-16' AS DATE)),
            (1, 1, 'Michael Chen', 1342576.71, CAST('2023-02-17' AS DATE)),
            (1, 1, 'Michael Chen', 1314308.82, CAST('2023-02-21' AS DATE)),
            (1, 1, 'Michael Chen', 1314391.64, CAST('2023-02-22' AS DATE)),
            (1, 1, 'Michael Chen', 1328094.21, CAST('2023-02-23' AS DATE)),
            (1, 1, 'Michael Chen', 1307250.27, CAST('2023-02-24' AS DATE)),
            (1, 1, 'Michael Chen', 1310355.61, CAST('2023-02-27' AS DATE)),
            (1, 1, 'Michael Chen', 1305982.13, CAST('2023-02-28' AS DATE)),
            (1, 1, 'Michael Chen', 1295379.48, CAST('2023-03-01' AS DATE)),
            (1, 1, 'Michael Chen', 1307445.39, CAST('2023-03-02' AS DATE)),
            (1, 1, 'Michael Chen', 1330697.66, CAST('2023-03-03' AS DATE)),
            (1, 1, 'Michael Chen', 1328657.87, CAST('2023-03-06' AS DATE)),
            (1, 1, 'Michael Chen', 1312324.71, CAST('2023-03-07' AS DATE)),
            (1, 1, 'Michael Chen', 1313800.69, CAST('2023-03-08' AS DATE)),
            (1, 1, 'Michael Chen', 1294462.90, CAST('2023-03-09' AS DATE)),
            (1, 1, 'Michael Chen', 1276235.01, CAST('2023-03-10' AS DATE)),
            (1, 1, 'Michael Chen', 1287325.72, CAST('2023-03-13' AS DATE)),
            (1, 1, 'Michael Chen', 1313491.57, CAST('2023-03-14' AS DATE)),
            (1, 1, 'Michael Chen', 1317612.51, CAST('2023-03-15' AS DATE)),
            (1, 1, 'Michael Chen', 1351703.09, CAST('2023-03-16' AS DATE)),
            (1, 1, 'Michael Chen', 1343268.82, CAST('2023-03-17' AS DATE)),
            (1, 1, 'Michael Chen', 1341746.17, CAST('2023-03-20' AS DATE)),
            (1, 1, 'Michael Chen', 1358609.22, CAST('2023-03-21' AS DATE)),
            (1, 1, 'Michael Chen', 1340354.59, CAST('2023-03-22' AS DATE)),
            (1, 1, 'Michael Chen', 1348694.20, CAST('2023-03-23' AS DATE)),
            (1, 1, 'Michael Chen', 1356504.70, CAST('2023-03-24' AS DATE)),
            (1, 1, 'Michael Chen', 1353687.91, CAST('2023-03-27' AS DATE)),
            (1, 1, 'Michael Chen', 1347762.06, CAST('2023-03-28' AS DATE)),
            (1, 1, 'Michael Chen', 1369402.88, CAST('2023-03-29' AS DATE)),
            (1, 1, 'Michael Chen', 1381904.29, CAST('2023-03-30' AS DATE)),
            (1, 1, 'Michael Chen', 1400689.44, CAST('2023-03-31' AS DATE)),
            (1, 1, 'Michael Chen', 1403044.25, CAST('2023-04-03' AS DATE)),
            (1, 1, 'Michael Chen', 1401770.50, CAST('2023-04-04' AS DATE)),
            (1, 1, 'Michael Chen', 1394828.11, CAST('2023-04-05' AS DATE)),
            (1, 1, 'Michael Chen', 1407853.28, CAST('2023-04-06' AS DATE)),
            (1, 1, 'Michael Chen', 1407392.37, CAST('2023-04-10' AS DATE)),
            (1, 1, 'Michael Chen', 1396195.40, CAST('2023-04-11' AS DATE)),
            (1, 1, 'Michael Chen', 1388826.08, CAST('2023-04-12' AS DATE)),
            (1, 1, 'Michael Chen', 1416003.09, CAST('2023-04-13' AS DATE)),
            (1, 1, 'Michael Chen', 1409015.45, CAST('2023-04-14' AS DATE)),
            (1, 1, 'Michael Chen', 1415236.64, CAST('2023-04-17' AS DATE)),
            (1, 1, 'Michael Chen', 1413917.82, CAST('2023-04-18' AS DATE)),
            (1, 1, 'Michael Chen', 1419467.97, CAST('2023-04-19' AS DATE)),
            (1, 1, 'Michael Chen', 1409763.25, CAST('2023-04-20' AS DATE)),
            (1, 1, 'Michael Chen', 1418460.51, CAST('2023-04-21' AS DATE)),
            (1, 1, 'Michael Chen', 1414402.29, CAST('2023-04-24' AS DATE)),
            (1, 1, 'Michael Chen', 1386315.31, CAST('2023-04-25' AS DATE)),
            (1, 1, 'Michael Chen', 1408078.03, CAST('2023-04-26' AS DATE)),
            (1, 1, 'Michael Chen', 1440317.35, CAST('2023-04-27' AS DATE)),
            (1, 1, 'Michael Chen', 1442630.53, CAST('2023-04-28' AS DATE)),
            (1, 1, 'Michael Chen', 1437969.92, CAST('2023-05-01' AS DATE)),
            (1, 1, 'Michael Chen', 1431231.42, CAST('2023-05-02' AS DATE)),
            (1, 1, 'Michael Chen', 1425939.97, CAST('2023-05-03' AS DATE)),
            (1, 1, 'Michael Chen', 1421204.20, CAST('2023-05-04' AS DATE)),
            (1, 1, 'Michael Chen', 1445551.15, CAST('2023-05-05' AS DATE)),
            (1, 1, 'Michael Chen', 1444048.63, CAST('2023-05-08' AS DATE)),
            (1, 1, 'Michael Chen', 1438477.29, CAST('2023-05-09' AS DATE)),
            (1, 1, 'Michael Chen', 1455621.94, CAST('2023-05-10' AS DATE)),
            (1, 1, 'Michael Chen', 1454515.68, CAST('2023-05-11' AS DATE)),
            (1, 1, 'Michael Chen', 1447469.93, CAST('2023-05-12' AS DATE)),
            (1, 1, 'Michael Chen', 1453395.01, CAST('2023-05-15' AS DATE)),
            (1, 1, 'Michael Chen', 1453987.95, CAST('2023-05-16' AS DATE)),
            (1, 1, 'Michael Chen', 1470619.58, CAST('2023-05-17' AS DATE)),
            (1, 1, 'Michael Chen', 1488866.39, CAST('2023-05-18' AS DATE)),
            (1, 1, 'Michael Chen', 1484287.48, CAST('2023-05-19' AS DATE)),
            (1, 1, 'Michael Chen', 1485636.13, CAST('2023-05-22' AS DATE)),
            (1, 1, 'Michael Chen', 1468719.06, CAST('2023-05-23' AS DATE)),
            (1, 1, 'Michael Chen', 1464310.14, CAST('2023-05-24' AS DATE)),
            (1, 1, 'Michael Chen', 1492133.84, CAST('2023-05-25' AS DATE)),
            (1, 1, 'Michael Chen', 1518883.58, CAST('2023-05-26' AS DATE)),
            (1, 1, 'Michael Chen', 1521093.88, CAST('2023-05-30' AS DATE)),
            (1, 1, 'Michael Chen', 1509810.84, CAST('2023-05-31' AS DATE)),
            (1, 1, 'Michael Chen', 1530588.38, CAST('2023-06-01' AS DATE)),
            (1, 1, 'Michael Chen', 1547582.68, CAST('2023-06-02' AS DATE)),
            (1, 1, 'Michael Chen', 1549604.38, CAST('2023-06-05' AS DATE)),
            (1, 1, 'Michael Chen', 1548025.52, CAST('2023-06-06' AS DATE)),
            (1, 1, 'Michael Chen', 1520578.24, CAST('2023-06-07' AS DATE)),
            (1, 1, 'Michael Chen', 1535875.60, CAST('2023-06-08' AS DATE)),
            (1, 1, 'Michael Chen', 1537693.20, CAST('2023-06-09' AS DATE)),
            (1, 1, 'Michael Chen', 1557650.15, CAST('2023-06-12' AS DATE)),
            (1, 1, 'Michael Chen', 1569528.51, CAST('2023-06-13' AS DATE)),
            (1, 1, 'Michael Chen', 1574494.72, CAST('2023-06-14' AS DATE)),
            (1, 1, 'Michael Chen', 1598061.87, CAST('2023-06-15' AS DATE)),
            (1, 1, 'Michael Chen', 1586422.21, CAST('2023-06-16' AS DATE)),
            (1, 1, 'Michael Chen', 1581842.29, CAST('2023-06-20' AS DATE)),
            (1, 1, 'Michael Chen', 1570231.58, CAST('2023-06-21' AS DATE)),
            (1, 1, 'Michael Chen', 1591203.11, CAST('2023-06-22' AS DATE)),
            (1, 1, 'Michael Chen', 1576970.53, CAST('2023-06-23' AS DATE)),
            (1, 1, 'Michael Chen', 1558253.72, CAST('2023-06-26' AS DATE)),
            (1, 1, 'Michael Chen', 1576865.55, CAST('2023-06-27' AS DATE)),
            (1, 1, 'Michael Chen', 1575946.11, CAST('2023-06-28' AS DATE)),
            (1, 1, 'Michael Chen', 1576187.36, CAST('2023-06-29' AS DATE)),
            (1, 1, 'Michael Chen', 1599768.25, CAST('2023-06-30' AS DATE)),
            (1, 1, 'Michael Chen', 1595366.98, CAST('2023-07-03' AS DATE)),
            (1, 1, 'Michael Chen', 1594511.82, CAST('2023-07-05' AS DATE)),
            (1, 1, 'Michael Chen', 1586176.16, CAST('2023-07-06' AS DATE)),
            (1, 1, 'Michael Chen', 1581310.30, CAST('2023-07-07' AS DATE)),
            (1, 1, 'Michael Chen', 1573838.47, CAST('2023-07-10' AS DATE)),
            (1, 1, 'Michael Chen', 1582081.65, CAST('2023-07-11' AS DATE)),
            (1, 1, 'Michael Chen', 1598718.72, CAST('2023-07-12' AS DATE)),
            (1, 1, 'Michael Chen', 1621080.12, CAST('2023-07-13' AS DATE)),
            (1, 1, 'Michael Chen', 1627116.20, CAST('2023-07-14' AS DATE)),
            (1, 1, 'Michael Chen', 1628432.63, CAST('2023-07-17' AS DATE)),
            (1, 1, 'Michael Chen', 1650402.00, CAST('2023-07-18' AS DATE)),
            (1, 1, 'Michael Chen', 1652289.05, CAST('2023-07-19' AS DATE)),
            (1, 1, 'Michael Chen', 1628981.25, CAST('2023-07-20' AS DATE)),
            (1, 1, 'Michael Chen', 1625935.76, CAST('2023-07-21' AS DATE)),
            (1, 1, 'Michael Chen', 1627322.19, CAST('2023-07-24' AS DATE)),
            (1, 1, 'Michael Chen', 1638065.55, CAST('2023-07-25' AS DATE)),
            (1, 1, 'Michael Chen', 1621400.55, CAST('2023-07-26' AS DATE)),
            (1, 1, 'Michael Chen', 1608898.12, CAST('2023-07-27' AS DATE)),
            (1, 1, 'Michael Chen', 1633985.76, CAST('2023-07-28' AS DATE)),
            (1, 1, 'Michael Chen', 1633507.67, CAST('2023-07-31' AS DATE)),
            (1, 1, 'Michael Chen', 1626052.02, CAST('2023-08-01' AS DATE)),
            (1, 1, 'Michael Chen', 1595795.69, CAST('2023-08-02' AS DATE)),
            (1, 1, 'Michael Chen', 1593331.56, CAST('2023-08-03' AS DATE)),
            (1, 1, 'Michael Chen', 1612911.90, CAST('2023-08-04' AS DATE)),
            (1, 1, 'Michael Chen', 1629954.24, CAST('2023-08-07' AS DATE)),
            (1, 1, 'Michael Chen', 1618852.97, CAST('2023-08-08' AS DATE)),
            (1, 1, 'Michael Chen', 1601630.13, CAST('2023-08-09' AS DATE)),
            (1, 1, 'Michael Chen', 1603416.89, CAST('2023-08-10' AS DATE)),
            (1, 1, 'Michael Chen', 1598928.01, CAST('2023-08-11' AS DATE)),
            (1, 1, 'Michael Chen', 1617095.64, CAST('2023-08-14' AS DATE)),
            (1, 1, 'Michael Chen', 1601424.62, CAST('2023-08-15' AS DATE)),
            (1, 1, 'Michael Chen', 1587653.42, CAST('2023-08-16' AS DATE)),
            (1, 1, 'Michael Chen', 1574354.42, CAST('2023-08-17' AS DATE)),
            (1, 1, 'Michael Chen', 1572769.26, CAST('2023-08-18' AS DATE)),
            (1, 1, 'Michael Chen', 1594018.08, CAST('2023-08-21' AS DATE)),
            (1, 1, 'Michael Chen', 1588440.69, CAST('2023-08-22' AS DATE)),
            (1, 1, 'Michael Chen', 1606356.48, CAST('2023-08-23' AS DATE)),
            (1, 1, 'Michael Chen', 1581215.23, CAST('2023-08-24' AS DATE)),
            (1, 1, 'Michael Chen', 1590850.12, CAST('2023-08-25' AS DATE)),
            (1, 1, 'Michael Chen', 1597434.09, CAST('2023-08-28' AS DATE)),
            (1, 1, 'Michael Chen', 1621538.98, CAST('2023-08-29' AS DATE)),
            (1, 1, 'Michael Chen', 1625922.00, CAST('2023-08-30' AS DATE)),
            (1, 1, 'Michael Chen', 1626854.41, CAST('2023-08-31' AS DATE)),
            (1, 1, 'Michael Chen', 1628216.47, CAST('2023-09-01' AS DATE)),
            (1, 1, 'Michael Chen', 1626382.30, CAST('2023-09-05' AS DATE)),
            (1, 1, 'Michael Chen', 1612861.77, CAST('2023-09-06' AS DATE)),
            (1, 1, 'Michael Chen', 1611798.61, CAST('2023-09-07' AS DATE)),
            (1, 1, 'Michael Chen', 1616338.28, CAST('2023-09-08' AS DATE)),
            (1, 1, 'Michael Chen', 1635252.78, CAST('2023-09-11' AS DATE)),
            (1, 1, 'Michael Chen', 1620154.06, CAST('2023-09-12' AS DATE)),
            (1, 1, 'Michael Chen', 1634304.82, CAST('2023-09-13' AS DATE)),
            (1, 1, 'Michael Chen', 1642529.22, CAST('2023-09-14' AS DATE)),
            (1, 1, 'Michael Chen', 1611701.15, CAST('2023-09-15' AS DATE)),
            (1, 1, 'Michael Chen', 1609112.84, CAST('2023-09-18' AS DATE)),
            (1, 1, 'Michael Chen', 1601933.33, CAST('2023-09-19' AS DATE)),
            (1, 1, 'Michael Chen', 1580239.57, CAST('2023-09-20' AS DATE)),
            (1, 1, 'Michael Chen', 1551725.83, CAST('2023-09-21' AS DATE)),
            (1, 1, 'Michael Chen', 1548079.91, CAST('2023-09-22' AS DATE)),
            (1, 1, 'Michael Chen', 1558014.18, CAST('2023-09-25' AS DATE)),
            (1, 1, 'Michael Chen', 1530585.78, CAST('2023-09-26' AS DATE)),
            (1, 1, 'Michael Chen', 1531609.69, CAST('2023-09-27' AS DATE)),
            (1, 1, 'Michael Chen', 1538439.46, CAST('2023-09-28' AS DATE)),
            (1, 1, 'Michael Chen', 1540637.96, CAST('2023-09-29' AS DATE)),
            (1, 1, 'Michael Chen', 1553536.80, CAST('2023-10-02' AS DATE)),
            (1, 1, 'Michael Chen', 1521954.79, CAST('2023-10-03' AS DATE)),
            (1, 1, 'Michael Chen', 1538494.34, CAST('2023-10-04' AS DATE)),
            (1, 1, 'Michael Chen', 1539933.71, CAST('2023-10-05' AS DATE)),
            (1, 1, 'Michael Chen', 1564367.33, CAST('2023-10-06' AS DATE)),
            (1, 1, 'Michael Chen', 1570979.23, CAST('2023-10-09' AS DATE)),
            (1, 1, 'Michael Chen', 1577774.07, CAST('2023-10-10' AS DATE)),
            (1, 1, 'Michael Chen', 1589775.49, CAST('2023-10-11' AS DATE)),
            (1, 1, 'Michael Chen', 1583027.37, CAST('2023-10-12' AS DATE)),
            (1, 1, 'Michael Chen', 1569774.39, CAST('2023-10-13' AS DATE)),
            (1, 1, 'Michael Chen', 1590226.09, CAST('2023-10-16' AS DATE)),
            (1, 1, 'Michael Chen', 1582502.00, CAST('2023-10-17' AS DATE)),
            (1, 1, 'Michael Chen', 1559182.46, CAST('2023-10-18' AS DATE)),
            (1, 1, 'Michael Chen', 1552882.48, CAST('2023-10-19' AS DATE)),
            (1, 1, 'Michael Chen', 1531817.43, CAST('2023-10-20' AS DATE)),
            (1, 1, 'Michael Chen', 1538132.10, CAST('2023-10-23' AS DATE)),
            (1, 1, 'Michael Chen', 1550436.17, CAST('2023-10-24' AS DATE)),
            (1, 1, 'Michael Chen', 1531797.69, CAST('2023-10-25' AS DATE)),
            (1, 1, 'Michael Chen', 1502004.63, CAST('2023-10-26' AS DATE)),
            (1, 1, 'Michael Chen', 1513582.38, CAST('2023-10-27' AS DATE)),
            (1, 1, 'Michael Chen', 1540977.96, CAST('2023-10-30' AS DATE)),
            (1, 1, 'Michael Chen', 1547021.85, CAST('2023-10-31' AS DATE)),
            (1, 1, 'Michael Chen', 1573407.49, CAST('2023-11-01' AS DATE)),
            (1, 1, 'Michael Chen', 1595530.43, CAST('2023-11-02' AS DATE)),
            (1, 1, 'Michael Chen', 1612004.02, CAST('2023-11-03' AS DATE)),
            (1, 1, 'Michael Chen', 1622641.68, CAST('2023-11-06' AS DATE)),
            (1, 1, 'Michael Chen', 1635497.78, CAST('2023-11-07' AS DATE)),
            (1, 1, 'Michael Chen', 1637907.84, CAST('2023-11-08' AS DATE)),
            (1, 1, 'Michael Chen', 1622469.47, CAST('2023-11-09' AS DATE)),
            (1, 1, 'Michael Chen', 1651573.62, CAST('2023-11-10' AS DATE)),
            (1, 1, 'Michael Chen', 1648332.79, CAST('2023-11-13' AS DATE)),
            (1, 1, 'Michael Chen', 1675380.84, CAST('2023-11-14' AS DATE)),
            (1, 1, 'Michael Chen', 1670160.74, CAST('2023-11-15' AS DATE)),
            (1, 1, 'Michael Chen', 1679280.51, CAST('2023-11-16' AS DATE)),
            (1, 1, 'Michael Chen', 1677274.73, CAST('2023-11-17' AS DATE)),
            (1, 1, 'Michael Chen', 1696243.81, CAST('2023-11-20' AS DATE)),
            (1, 1, 'Michael Chen', 1686168.04, CAST('2023-11-21' AS DATE)),
            (1, 1, 'Michael Chen', 1697897.71, CAST('2023-11-22' AS DATE)),
            (1, 1, 'Michael Chen', 1697209.99, CAST('2023-11-24' AS DATE)),
            (1, 1, 'Michael Chen', 1698840.48, CAST('2023-11-27' AS DATE)),
            (1, 1, 'Michael Chen', 1699850.00, CAST('2023-11-28' AS DATE)),
            (1, 1, 'Michael Chen', 1694841.59, CAST('2023-11-29' AS DATE)),
            (1, 1, 'Michael Chen', 1697154.18, CAST('2023-11-30' AS DATE)),
            (1, 1, 'Michael Chen', 1699695.64, CAST('2023-12-01' AS DATE)),
            (1, 1, 'Michael Chen', 1684438.55, CAST('2023-12-04' AS DATE)),
            (1, 1, 'Michael Chen', 1693865.14, CAST('2023-12-05' AS DATE)),
            (1, 1, 'Michael Chen', 1680686.61, CAST('2023-12-06' AS DATE)),
            (1, 1, 'Michael Chen', 1694495.24, CAST('2023-12-07' AS DATE)),
            (1, 1, 'Michael Chen', 1704112.18, CAST('2023-12-08' AS DATE)),
            (1, 1, 'Michael Chen', 1699831.33, CAST('2023-12-11' AS DATE)),
            (1, 1, 'Michael Chen', 1713250.66, CAST('2023-12-12' AS DATE)),
            (1, 1, 'Michael Chen', 1731386.60, CAST('2023-12-13' AS DATE)),
            (1, 1, 'Michael Chen', 1721389.32, CAST('2023-12-14' AS DATE)),
            (1, 1, 'Michael Chen', 1729058.45, CAST('2023-12-15' AS DATE)),
            (1, 1, 'Michael Chen', 1745920.22, CAST('2023-12-18' AS DATE)),
            (1, 1, 'Michael Chen', 1751493.36, CAST('2023-12-19' AS DATE)),
            (1, 1, 'Michael Chen', 1728206.76, CAST('2023-12-20' AS DATE)),
            (1, 1, 'Michael Chen', 1746717.83, CAST('2023-12-21' AS DATE)),
            (1, 1, 'Michael Chen', 1749980.43, CAST('2023-12-22' AS DATE)),
            (1, 1, 'Michael Chen', 1754751.74, CAST('2023-12-26' AS DATE)),
            (1, 1, 'Michael Chen', 1756936.20, CAST('2023-12-27' AS DATE)),
            (1, 1, 'Michael Chen', 1759545.69, CAST('2023-12-28' AS DATE)),
            (1, 1, 'Michael Chen', 1755193.55, CAST('2023-12-29' AS DATE)),
            (1, 1, 'Michael Chen', 1743752.64, CAST('2024-01-02' AS DATE)),
            (1, 1, 'Michael Chen', 1732936.68, CAST('2024-01-03' AS DATE)),
            (1, 1, 'Michael Chen', 1722728.10, CAST('2024-01-04' AS DATE)),
            (1, 1, 'Michael Chen', 1726969.72, CAST('2024-01-05' AS DATE)),
            (1, 1, 'Michael Chen', 1761591.87, CAST('2024-01-08' AS DATE)),
            (1, 1, 'Michael Chen', 1768498.31, CAST('2024-01-09' AS DATE)),
            (1, 1, 'Michael Chen', 1788030.91, CAST('2024-01-10' AS DATE)),
            (1, 1, 'Michael Chen', 1793101.31, CAST('2024-01-11' AS DATE)),
            (1, 1, 'Michael Chen', 1795529.29, CAST('2024-01-12' AS DATE)),
            (1, 1, 'Michael Chen', 1794300.78, CAST('2024-01-16' AS DATE)),
            (1, 1, 'Michael Chen', 1785236.97, CAST('2024-01-17' AS DATE)),
            (1, 1, 'Michael Chen', 1801618.97, CAST('2024-01-18' AS DATE)),
            (1, 1, 'Michael Chen', 1824065.61, CAST('2024-01-19' AS DATE)),
            (1, 1, 'Michael Chen', 1823926.13, CAST('2024-01-22' AS DATE)),
            (1, 1, 'Michael Chen', 1831086.33, CAST('2024-01-23' AS DATE)),
            (1, 1, 'Michael Chen', 1837997.74, CAST('2024-01-24' AS DATE)),
            (1, 1, 'Michael Chen', 1845991.48, CAST('2024-01-25' AS DATE)),
            (1, 1, 'Michael Chen', 1847035.55, CAST('2024-01-26' AS DATE)),
            (1, 1, 'Michael Chen', 1868542.99, CAST('2024-01-29' AS DATE)),
            (1, 1, 'Michael Chen', 1863113.34, CAST('2024-01-30' AS DATE)),
            (1, 1, 'Michael Chen', 1829500.84, CAST('2024-01-31' AS DATE)),
            (1, 1, 'Michael Chen', 1860199.63, CAST('2024-02-01' AS DATE)),
            (1, 1, 'Michael Chen', 1906575.46, CAST('2024-02-02' AS DATE)),
            (1, 1, 'Michael Chen', 1903088.51, CAST('2024-02-05' AS DATE)),
            (1, 1, 'Michael Chen', 1903737.75, CAST('2024-02-06' AS DATE)),
            (1, 1, 'Michael Chen', 1925876.64, CAST('2024-02-07' AS DATE)),
            (1, 1, 'Michael Chen', 1923737.22, CAST('2024-02-08' AS DATE)),
            (1, 1, 'Michael Chen', 1949371.32, CAST('2024-02-09' AS DATE)),
            (1, 1, 'Michael Chen', 1940383.19, CAST('2024-02-12' AS DATE)),
            (1, 1, 'Michael Chen', 1910416.84, CAST('2024-02-13' AS DATE)),
            (1, 1, 'Michael Chen', 1932348.28, CAST('2024-02-14' AS DATE)),
            (1, 1, 'Michael Chen', 1931127.28, CAST('2024-02-15' AS DATE)),
            (1, 1, 'Michael Chen', 1925266.10, CAST('2024-02-16' AS DATE)),
            (1, 1, 'Michael Chen', 1906773.74, CAST('2024-02-20' AS DATE)),
            (1, 1, 'Michael Chen', 1905948.96, CAST('2024-02-21' AS DATE)),
            (1, 1, 'Michael Chen', 1970637.74, CAST('2024-02-22' AS DATE)),
            (1, 1, 'Michael Chen', 1972711.48, CAST('2024-02-23' AS DATE)),
            (1, 1, 'Michael Chen', 1965941.22, CAST('2024-02-26' AS DATE)),
            (1, 1, 'Michael Chen', 1964249.05, CAST('2024-02-27' AS DATE)),
            (1, 1, 'Michael Chen', 1958490.62, CAST('2024-02-28' AS DATE)),
            (1, 1, 'Michael Chen', 1974658.40, CAST('2024-02-29' AS DATE)),
            (1, 1, 'Michael Chen', 1996846.18, CAST('2024-03-01' AS DATE)),
            (1, 1, 'Michael Chen', 2000224.90, CAST('2024-03-04' AS DATE)),
            (1, 1, 'Michael Chen', 1972296.18, CAST('2024-03-05' AS DATE)),
            (1, 1, 'Michael Chen', 1982307.25, CAST('2024-03-06' AS DATE)),
            (1, 1, 'Michael Chen', 2013977.36, CAST('2024-03-07' AS DATE)),
            (1, 1, 'Michael Chen', 1991540.04, CAST('2024-03-08' AS DATE)),
            (1, 1, 'Michael Chen', 1977669.89, CAST('2024-03-11' AS DATE)),
            (1, 1, 'Michael Chen', 2018629.99, CAST('2024-03-12' AS DATE)),
            (1, 1, 'Michael Chen', 2016193.46, CAST('2024-03-13' AS DATE)),
            (1, 1, 'Michael Chen', 2021874.88, CAST('2024-03-14' AS DATE)),
            (1, 1, 'Michael Chen', 1997735.16, CAST('2024-03-15' AS DATE)),
            (1, 1, 'Michael Chen', 2003978.28, CAST('2024-03-18' AS DATE)),
            (1, 1, 'Michael Chen', 2019526.25, CAST('2024-03-19' AS DATE)),
            (1, 1, 'Michael Chen', 2036295.51, CAST('2024-03-20' AS DATE)),
            (1, 1, 'Michael Chen', 2045893.30, CAST('2024-03-21' AS DATE)),
            (1, 1, 'Michael Chen', 2051053.90, CAST('2024-03-22' AS DATE)),
            (1, 1, 'Michael Chen', 2045508.05, CAST('2024-03-25' AS DATE)),
            (1, 1, 'Michael Chen', 2036048.48, CAST('2024-03-26' AS DATE)),
            (1, 1, 'Michael Chen', 2043842.82, CAST('2024-03-27' AS DATE)),
            (1, 1, 'Michael Chen', 2044258.12, CAST('2024-03-28' AS DATE)),
            (1, 1, 'Michael Chen', 2045550.96, CAST('2024-04-01' AS DATE)),
            (1, 1, 'Michael Chen', 2029712.92, CAST('2024-04-02' AS DATE)),
            (1, 1, 'Michael Chen', 2031761.42, CAST('2024-04-03' AS DATE)),
            (1, 1, 'Michael Chen', 2004468.82, CAST('2024-04-04' AS DATE)),
            (1, 1, 'Michael Chen', 2037388.21, CAST('2024-04-05' AS DATE)),
            (1, 1, 'Michael Chen', 2034206.30, CAST('2024-04-08' AS DATE)),
            (1, 1, 'Michael Chen', 2035256.00, CAST('2024-04-09' AS DATE)),
            (1, 1, 'Michael Chen', 2025569.16, CAST('2024-04-10' AS DATE)),
            (1, 1, 'Michael Chen', 2048702.85, CAST('2024-04-11' AS DATE)),
            (1, 1, 'Michael Chen', 2016646.86, CAST('2024-04-12' AS DATE)),
            (1, 1, 'Michael Chen', 1987818.69, CAST('2024-04-15' AS DATE)),
            (1, 1, 'Michael Chen', 1990504.19, CAST('2024-04-16' AS DATE)),
            (1, 1, 'Michael Chen', 1971008.29, CAST('2024-04-17' AS DATE)),
            (1, 1, 'Michael Chen', 1958407.31, CAST('2024-04-18' AS DATE)),
            (1, 1, 'Michael Chen', 1919260.43, CAST('2024-04-19' AS DATE)),
            (1, 1, 'Michael Chen', 1941485.02, CAST('2024-04-22' AS DATE)),
            (1, 1, 'Michael Chen', 1971730.17, CAST('2024-04-23' AS DATE)),
            (1, 1, 'Michael Chen', 1960201.00, CAST('2024-04-24' AS DATE)),
            (1, 1, 'Michael Chen', 1945210.15, CAST('2024-04-25' AS DATE)),
            (1, 1, 'Michael Chen', 1982984.78, CAST('2024-04-26' AS DATE)),
            (1, 1, 'Michael Chen', 1985180.88, CAST('2024-04-29' AS DATE)),
            (1, 1, 'Michael Chen', 1944907.67, CAST('2024-04-30' AS DATE)),
            (1, 1, 'Michael Chen', 1950715.59, CAST('2024-05-01' AS DATE)),
            (1, 1, 'Michael Chen', 1977611.36, CAST('2024-05-02' AS DATE)),
            (1, 1, 'Michael Chen', 2006241.15, CAST('2024-05-03' AS DATE)),
            (1, 1, 'Michael Chen', 2034656.00, CAST('2024-05-06' AS DATE)),
            (1, 1, 'Michael Chen', 2029708.02, CAST('2024-05-07' AS DATE)),
            (1, 1, 'Michael Chen', 2027623.73, CAST('2024-05-08' AS DATE)),
            (1, 1, 'Michael Chen', 2035525.41, CAST('2024-05-09' AS DATE)),
            (1, 1, 'Michael Chen', 2037732.19, CAST('2024-05-10' AS DATE)),
            (1, 1, 'Michael Chen', 2036059.33, CAST('2024-05-13' AS DATE)),
            (1, 1, 'Michael Chen', 2046826.88, CAST('2024-05-14' AS DATE)),
            (1, 1, 'Michael Chen', 2073395.31, CAST('2024-05-15' AS DATE)),
            (1, 1, 'Michael Chen', 2064058.22, CAST('2024-05-16' AS DATE)),
            (1, 1, 'Michael Chen', 2062231.51, CAST('2024-05-17' AS DATE)),
            (1, 1, 'Michael Chen', 2071191.37, CAST('2024-05-20' AS DATE)),
            (1, 1, 'Michael Chen', 2077592.62, CAST('2024-05-21' AS DATE)),
            (1, 1, 'Michael Chen', 2076736.15, CAST('2024-05-22' AS DATE)),
            (1, 1, 'Michael Chen', 2080083.39, CAST('2024-05-23' AS DATE)),
            (1, 1, 'Michael Chen', 2092481.26, CAST('2024-05-24' AS DATE)),
            (1, 1, 'Michael Chen', 2109332.27, CAST('2024-05-28' AS DATE)),
            (1, 1, 'Michael Chen', 2102387.27, CAST('2024-05-29' AS DATE)),
            (1, 1, 'Michael Chen', 2067312.35, CAST('2024-05-30' AS DATE)),
            (1, 1, 'Michael Chen', 2070710.19, CAST('2024-05-31' AS DATE)),
            (1, 1, 'Michael Chen', 2087463.28, CAST('2024-06-03' AS DATE)),
            (1, 1, 'Michael Chen', 2097267.22, CAST('2024-06-04' AS DATE)),
            (1, 1, 'Michael Chen', 2133532.97, CAST('2024-06-05' AS DATE)),
            (1, 1, 'Michael Chen', 2138911.73, CAST('2024-06-06' AS DATE)),
            (1, 1, 'Michael Chen', 2135652.07, CAST('2024-06-07' AS DATE)),
            (1, 1, 'Michael Chen', 2151221.20, CAST('2024-06-10' AS DATE)),
            (1, 1, 'Michael Chen', 2155218.26, CAST('2024-06-11' AS DATE)),
            (1, 1, 'Michael Chen', 2178881.53, CAST('2024-06-12' AS DATE)),
            (1, 1, 'Michael Chen', 2184331.39, CAST('2024-06-13' AS DATE)),
            (1, 1, 'Michael Chen', 2190180.62, CAST('2024-06-14' AS DATE)),
            (1, 1, 'Michael Chen', 2200466.34, CAST('2024-06-17' AS DATE)),
            (1, 1, 'Michael Chen', 2208076.09, CAST('2024-06-18' AS DATE)),
            (1, 1, 'Michael Chen', 2202277.91, CAST('2024-06-20' AS DATE)),
            (1, 1, 'Michael Chen', 2203393.56, CAST('2024-06-21' AS DATE)),
            (1, 1, 'Michael Chen', 2174651.85, CAST('2024-06-24' AS DATE)),
            (1, 1, 'Michael Chen', 2199767.54, CAST('2024-06-25' AS DATE)),
            (1, 1, 'Michael Chen', 2216047.81, CAST('2024-06-26' AS DATE)),
            (1, 1, 'Michael Chen', 2220620.70, CAST('2024-06-27' AS DATE)),
            (1, 1, 'Michael Chen', 2200577.92, CAST('2024-06-28' AS DATE)),
            (1, 1, 'Michael Chen', 2220759.58, CAST('2024-07-01' AS DATE)),
            (1, 1, 'Michael Chen', 2229065.38, CAST('2024-07-02' AS DATE)),
            (1, 1, 'Michael Chen', 2239539.61, CAST('2024-07-03' AS DATE)),
            (1, 1, 'Michael Chen', 2252883.83, CAST('2024-07-05' AS DATE)),
            (1, 1, 'Michael Chen', 2255919.90, CAST('2024-07-08' AS DATE)),
            (1, 1, 'Michael Chen', 2258317.32, CAST('2024-07-09' AS DATE)),
            (1, 1, 'Michael Chen', 2284992.74, CAST('2024-07-10' AS DATE)),
            (1, 1, 'Michael Chen', 2242707.71, CAST('2024-07-11' AS DATE)),
            (1, 1, 'Michael Chen', 2251596.48, CAST('2024-07-12' AS DATE)),
            (1, 1, 'Michael Chen', 2247701.77, CAST('2024-07-15' AS DATE)),
            (1, 1, 'Michael Chen', 2248637.07, CAST('2024-07-16' AS DATE)),
            (1, 1, 'Michael Chen', 2203016.23, CAST('2024-07-17' AS DATE)),
            (1, 1, 'Michael Chen', 2184400.04, CAST('2024-07-18' AS DATE)),
            (1, 1, 'Michael Chen', 2169268.23, CAST('2024-07-19' AS DATE)),
            (1, 1, 'Michael Chen', 2196943.71, CAST('2024-07-22' AS DATE)),
            (1, 1, 'Michael Chen', 2203621.60, CAST('2024-07-23' AS DATE)),
            (1, 1, 'Michael Chen', 2141859.73, CAST('2024-07-24' AS DATE)),
            (1, 1, 'Michael Chen', 2118819.01, CAST('2024-07-25' AS DATE)),
            (1, 1, 'Michael Chen', 2143647.52, CAST('2024-07-26' AS DATE)),
            (1, 1, 'Michael Chen', 2143764.66, CAST('2024-07-29' AS DATE)),
            (1, 1, 'Michael Chen', 2115468.27, CAST('2024-07-30' AS DATE)),
            (1, 1, 'Michael Chen', 2161613.30, CAST('2024-07-31' AS DATE)),
            (1, 1, 'Michael Chen', 2129484.37, CAST('2024-08-01' AS DATE)),
            (1, 1, 'Michael Chen', 2068390.53, CAST('2024-08-02' AS DATE)),
            (1, 1, 'Michael Chen', 1995531.81, CAST('2024-08-05' AS DATE)),
            (1, 1, 'Michael Chen', 2018596.87, CAST('2024-08-06' AS DATE)),
            (1, 1, 'Michael Chen', 1998743.02, CAST('2024-08-07' AS DATE)),
            (1, 1, 'Michael Chen', 2046403.99, CAST('2024-08-08' AS DATE)),
            (1, 1, 'Michael Chen', 2056411.19, CAST('2024-08-09' AS DATE)),
            (1, 1, 'Michael Chen', 2065879.42, CAST('2024-08-12' AS DATE)),
            (1, 1, 'Michael Chen', 2112385.08, CAST('2024-08-13' AS DATE)),
            (1, 1, 'Michael Chen', 2122653.78, CAST('2024-08-14' AS DATE)),
            (1, 1, 'Michael Chen', 2169107.03, CAST('2024-08-15' AS DATE)),
            (1, 1, 'Michael Chen', 2171012.50, CAST('2024-08-16' AS DATE)),
            (1, 1, 'Michael Chen', 2198715.60, CAST('2024-08-19' AS DATE)),
            (1, 1, 'Michael Chen', 2197046.83, CAST('2024-08-20' AS DATE)),
            (1, 1, 'Michael Chen', 2205465.99, CAST('2024-08-21' AS DATE)),
            (1, 1, 'Michael Chen', 2171082.25, CAST('2024-08-22' AS DATE)),
            (1, 1, 'Michael Chen', 2197112.50, CAST('2024-08-23' AS DATE)),
            (1, 1, 'Michael Chen', 2181517.06, CAST('2024-08-26' AS DATE)),
            (1, 1, 'Michael Chen', 2183003.23, CAST('2024-08-27' AS DATE)),
            (1, 1, 'Michael Chen', 2164300.10, CAST('2024-08-28' AS DATE)),
            (1, 1, 'Michael Chen', 2152827.73, CAST('2024-08-29' AS DATE)),
            (1, 1, 'Michael Chen', 2183069.32, CAST('2024-08-30' AS DATE)),
            (1, 1, 'Michael Chen', 2127582.81, CAST('2024-09-03' AS DATE)),
            (1, 1, 'Michael Chen', 2115025.43, CAST('2024-09-04' AS DATE)),
            (1, 1, 'Michael Chen', 2119593.85, CAST('2024-09-05' AS DATE)),
            (1, 1, 'Michael Chen', 2075331.42, CAST('2024-09-06' AS DATE)),
            (1, 1, 'Michael Chen', 2106406.88, CAST('2024-09-09' AS DATE)),
            (1, 1, 'Michael Chen', 2132208.21, CAST('2024-09-10' AS DATE)),
            (1, 1, 'Michael Chen', 2178394.91, CAST('2024-09-11' AS DATE)),
            (1, 1, 'Michael Chen', 2200708.65, CAST('2024-09-12' AS DATE)),
            (1, 1, 'Michael Chen', 2208451.32, CAST('2024-09-13' AS DATE)),
            (1, 1, 'Michael Chen', 2204011.95, CAST('2024-09-16' AS DATE)),
            (1, 1, 'Michael Chen', 2206655.16, CAST('2024-09-17' AS DATE)),
            (1, 1, 'Michael Chen', 2193128.73, CAST('2024-09-18' AS DATE)),
            (1, 1, 'Michael Chen', 2233484.66, CAST('2024-09-19' AS DATE)),
            (1, 1, 'Michael Chen', 2225971.63, CAST('2024-09-20' AS DATE)),
            (1, 1, 'Michael Chen', 2229902.31, CAST('2024-09-23' AS DATE)),
            (1, 1, 'Michael Chen', 2237125.03, CAST('2024-09-24' AS DATE)),
            (1, 1, 'Michael Chen', 2238325.25, CAST('2024-09-25' AS DATE)),
            (1, 1, 'Michael Chen', 2240228.34, CAST('2024-09-26' AS DATE)),
            (1, 1, 'Michael Chen', 2222932.11, CAST('2024-09-27' AS DATE)),
            (1, 1, 'Michael Chen', 2227625.55, CAST('2024-09-30' AS DATE)),
            (1, 1, 'Michael Chen', 2195586.56, CAST('2024-10-01' AS DATE)),
            (1, 1, 'Michael Chen', 2195166.28, CAST('2024-10-02' AS DATE)),
            (1, 1, 'Michael Chen', 2193232.56, CAST('2024-10-03' AS DATE)),
            (1, 1, 'Michael Chen', 2213952.49, CAST('2024-10-04' AS DATE)),
            (1, 1, 'Michael Chen', 2193132.73, CAST('2024-10-07' AS DATE)),
            (1, 1, 'Michael Chen', 2223293.04, CAST('2024-10-08' AS DATE)),
            (1, 1, 'Michael Chen', 2238854.63, CAST('2024-10-09' AS DATE)),
            (1, 1, 'Michael Chen', 2242457.83, CAST('2024-10-10' AS DATE)),
            (1, 1, 'Michael Chen', 2254960.07, CAST('2024-10-11' AS DATE)),
            (1, 1, 'Michael Chen', 2271098.25, CAST('2024-10-14' AS DATE)),
            (1, 1, 'Michael Chen', 2246741.92, CAST('2024-10-15' AS DATE)),
            (1, 1, 'Michael Chen', 2256340.34, CAST('2024-10-16' AS DATE)),
            (1, 1, 'Michael Chen', 2259036.04, CAST('2024-10-17' AS DATE)),
            (1, 1, 'Michael Chen', 2270697.11, CAST('2024-10-18' AS DATE)),
            (1, 1, 'Michael Chen', 2279014.43, CAST('2024-10-21' AS DATE)),
            (1, 1, 'Michael Chen', 2288496.81, CAST('2024-10-22' AS DATE)),
            (1, 1, 'Michael Chen', 2256974.70, CAST('2024-10-23' AS DATE)),
            (1, 1, 'Michael Chen', 2261983.88, CAST('2024-10-24' AS DATE)),
            (1, 1, 'Michael Chen', 2269159.50, CAST('2024-10-25' AS DATE)),
            (1, 1, 'Michael Chen', 2269547.52, CAST('2024-10-28' AS DATE)),
            (1, 1, 'Michael Chen', 2282456.29, CAST('2024-10-29' AS DATE)),
            (1, 1, 'Michael Chen', 2279675.97, CAST('2024-10-30' AS DATE)),
            (1, 1, 'Michael Chen', 2205175.65, CAST('2024-10-31' AS DATE)),
            (1, 1, 'Michael Chen', 2244315.00, CAST('2024-11-01' AS DATE)),
            (1, 1, 'Michael Chen', 2236038.37, CAST('2024-11-04' AS DATE)),
            (1, 1, 'Michael Chen', 2267497.30, CAST('2024-11-05' AS DATE)),
            (1, 1, 'Michael Chen', 2325349.47, CAST('2024-11-06' AS DATE)),
            (1, 1, 'Michael Chen', 2352704.26, CAST('2024-11-07' AS DATE)),
            (1, 1, 'Michael Chen', 2349020.10, CAST('2024-11-08' AS DATE)),
            (1, 1, 'Michael Chen', 2335168.96, CAST('2024-11-11' AS DATE)),
            (1, 1, 'Michael Chen', 2344220.59, CAST('2024-11-12' AS DATE)),
            (1, 1, 'Michael Chen', 2351691.03, CAST('2024-11-13' AS DATE)),
            (1, 1, 'Michael Chen', 2338462.73, CAST('2024-11-14' AS DATE)),
            (1, 1, 'Michael Chen', 2279668.08, CAST('2024-11-15' AS DATE)),
            (1, 1, 'Michael Chen', 2277717.33, CAST('2024-11-18' AS DATE)),
            (1, 1, 'Michael Chen', 2303533.64, CAST('2024-11-19' AS DATE)),
            (1, 1, 'Michael Chen', 2298707.02, CAST('2024-11-20' AS DATE)),
            (1, 1, 'Michael Chen', 2296660.44, CAST('2024-11-21' AS DATE)),
            (1, 1, 'Michael Chen', 2290926.38, CAST('2024-11-22' AS DATE)),
            (1, 1, 'Michael Chen', 2293996.73, CAST('2024-11-25' AS DATE)),
            (1, 1, 'Michael Chen', 2324831.94, CAST('2024-11-26' AS DATE)),
            (1, 1, 'Michael Chen', 2310943.08, CAST('2024-11-27' AS DATE)),
            (1, 1, 'Michael Chen', 2328373.98, CAST('2024-11-29' AS DATE)),
            (1, 1, 'Michael Chen', 2343772.68, CAST('2024-12-02' AS DATE)),
            (1, 1, 'Michael Chen', 2352311.90, CAST('2024-12-03' AS DATE)),
            (1, 1, 'Michael Chen', 2385005.70, CAST('2024-12-04' AS DATE)),
            (1, 1, 'Michael Chen', 2390103.32, CAST('2024-12-05' AS DATE)),
            (1, 1, 'Michael Chen', 2398546.96, CAST('2024-12-06' AS DATE)),
            (1, 1, 'Michael Chen', 2387519.80, CAST('2024-12-09' AS DATE)),
            (1, 1, 'Michael Chen', 2370170.16, CAST('2024-12-10' AS DATE)),
            (1, 1, 'Michael Chen', 2398818.44, CAST('2024-12-11' AS DATE)),
            (1, 1, 'Michael Chen', 2385020.95, CAST('2024-12-12' AS DATE)),
            (1, 1, 'Michael Chen', 2371979.34, CAST('2024-12-13' AS DATE)),
            (1, 1, 'Michael Chen', 2383169.63, CAST('2024-12-16' AS DATE)),
            (1, 1, 'Michael Chen', 2375420.49, CAST('2024-12-17' AS DATE)),
            (1, 1, 'Michael Chen', 2302764.92, CAST('2024-12-18' AS DATE)),
            (1, 1, 'Michael Chen', 2309524.40, CAST('2024-12-19' AS DATE)),
            (1, 1, 'Michael Chen', 2334627.95, CAST('2024-12-20' AS DATE)),
            (1, 1, 'Michael Chen', 2352305.88, CAST('2024-12-23' AS DATE)),
            (1, 1, 'Michael Chen', 2375834.42, CAST('2024-12-24' AS DATE)),
            (1, 1, 'Michael Chen', 2370942.56, CAST('2024-12-26' AS DATE)),
            (1, 1, 'Michael Chen', 2339163.32, CAST('2024-12-27' AS DATE)),
            (1, 1, 'Michael Chen', 2316122.88, CAST('2024-12-30' AS DATE)),
            (1, 1, 'Michael Chen', 2299183.96, CAST('2024-12-31' AS DATE)),
            (1, 1, 'Michael Chen', 2305338.63, CAST('2025-01-02' AS DATE)),
            (1, 1, 'Michael Chen', 2345345.26, CAST('2025-01-03' AS DATE)),
            (1, 1, 'Michael Chen', 2373040.53, CAST('2025-01-06' AS DATE)),
            (1, 1, 'Michael Chen', 2327787.06, CAST('2025-01-07' AS DATE)),
            (1, 1, 'Michael Chen', 2332816.68, CAST('2025-01-08' AS DATE)),
            (1, 1, 'Michael Chen', 2296437.89, CAST('2025-01-10' AS DATE)),
            (1, 1, 'Michael Chen', 2292604.23, CAST('2025-01-13' AS DATE)),
            (1, 1, 'Michael Chen', 2283800.72, CAST('2025-01-14' AS DATE)),
            (1, 1, 'Michael Chen', 2332394.76, CAST('2025-01-15' AS DATE)),
            (1, 1, 'Michael Chen', 2318895.58, CAST('2025-01-16' AS DATE)),
            (1, 1, 'Michael Chen', 2349594.94, CAST('2025-01-17' AS DATE)),
            (1, 1, 'Michael Chen', 2378748.12, CAST('2025-01-21' AS DATE)),
            (1, 1, 'Michael Chen', 2424803.02, CAST('2025-01-22' AS DATE)),
            (1, 1, 'Michael Chen', 2434903.03, CAST('2025-01-23' AS DATE)),
            (1, 1, 'Michael Chen', 2418608.64, CAST('2025-01-24' AS DATE)),
            (1, 1, 'Michael Chen', 2349592.59, CAST('2025-01-27' AS DATE)),
            (1, 1, 'Michael Chen', 2398004.83, CAST('2025-01-28' AS DATE)),
            (1, 1, 'Michael Chen', 2373070.14, CAST('2025-01-29' AS DATE)),
            (1, 1, 'Michael Chen', 2348413.34, CAST('2025-01-30' AS DATE)),
            (1, 1, 'Michael Chen', 2338614.94, CAST('2025-01-31' AS DATE)),
            (1, 1, 'Michael Chen', 2321194.24, CAST('2025-02-03' AS DATE)),
            (1, 1, 'Michael Chen', 2341264.53, CAST('2025-02-04' AS DATE)),
            (1, 1, 'Michael Chen', 2351481.37, CAST('2025-02-05' AS DATE)),
            (1, 1, 'Michael Chen', 2368028.50, CAST('2025-02-06' AS DATE)),
            (1, 1, 'Michael Chen', 2334887.18, CAST('2025-02-07' AS DATE)),
            (1, 1, 'Michael Chen', 2358915.04, CAST('2025-02-10' AS DATE)),
            (1, 1, 'Michael Chen', 2355176.66, CAST('2025-02-11' AS DATE)),
            (1, 1, 'Michael Chen', 2338257.64, CAST('2025-02-12' AS DATE)),
            (1, 1, 'Michael Chen', 2362320.67, CAST('2025-02-13' AS DATE)),
            (1, 1, 'Michael Chen', 2361516.53, CAST('2025-02-14' AS DATE)),
            (1, 1, 'Michael Chen', 2362100.54, CAST('2025-02-18' AS DATE)),
            (1, 1, 'Michael Chen', 2373126.58, CAST('2025-02-19' AS DATE)),
            (1, 1, 'Michael Chen', 2368167.28, CAST('2025-02-20' AS DATE)),
            (1, 1, 'Michael Chen', 2317503.92, CAST('2025-02-21' AS DATE)),
            (1, 1, 'Michael Chen', 2293960.36, CAST('2025-02-24' AS DATE)),
            (1, 1, 'Michael Chen', 2277413.24, CAST('2025-02-25' AS DATE)),
            (1, 1, 'Michael Chen', 2291504.50, CAST('2025-02-26' AS DATE)),
            (1, 1, 'Michael Chen', 2232297.76, CAST('2025-02-27' AS DATE)),
            (1, 1, 'Michael Chen', 2271178.41, CAST('2025-02-28' AS DATE)),
            (1, 1, 'Michael Chen', 2208762.02, CAST('2025-03-03' AS DATE)),
            (1, 1, 'Michael Chen', 2198846.35, CAST('2025-03-04' AS DATE)),
            (1, 1, 'Michael Chen', 2236238.25, CAST('2025-03-05' AS DATE)),
            (1, 1, 'Michael Chen', 2186139.14, CAST('2025-03-06' AS DATE)),
            (1, 1, 'Michael Chen', 2188591.47, CAST('2025-03-07' AS DATE)),
            (1, 1, 'Michael Chen', 2127323.40, CAST('2025-03-10' AS DATE)),
            (1, 1, 'Michael Chen', 2126432.42, CAST('2025-03-11' AS DATE)),
            (1, 1, 'Michael Chen', 2151075.38, CAST('2025-03-12' AS DATE)),
            (1, 1, 'Michael Chen', 2123609.76, CAST('2025-03-13' AS DATE)),
            (1, 1, 'Michael Chen', 2174467.48, CAST('2025-03-14' AS DATE)),
            (1, 1, 'Michael Chen', 2175230.41, CAST('2025-03-17' AS DATE)),
            (1, 1, 'Michael Chen', 2145948.82, CAST('2025-03-18' AS DATE)),
            (1, 1, 'Michael Chen', 2169560.66, CAST('2025-03-19' AS DATE)),
            (1, 1, 'Michael Chen', 2167444.84, CAST('2025-03-20' AS DATE)),
            (1, 1, 'Michael Chen', 2172306.66, CAST('2025-03-21' AS DATE)),
            (1, 1, 'Michael Chen', 2213346.57, CAST('2025-03-24' AS DATE)),
            (1, 1, 'Michael Chen', 2216491.97, CAST('2025-03-25' AS DATE)),
            (1, 1, 'Michael Chen', 2175037.90, CAST('2025-03-26' AS DATE)),
            (1, 1, 'Michael Chen', 2169446.33, CAST('2025-03-27' AS DATE)),
            (1, 1, 'Michael Chen', 2118483.31, CAST('2025-03-28' AS DATE)),
            (1, 1, 'Michael Chen', 2114177.42, CAST('2025-03-31' AS DATE)),
            (1, 1, 'Michael Chen', 2125576.42, CAST('2025-04-01' AS DATE)),
            (1, 1, 'Michael Chen', 2141041.03, CAST('2025-04-02' AS DATE)),
            (1, 1, 'Michael Chen', 2035668.36, CAST('2025-04-03' AS DATE)),
            (1, 1, 'Michael Chen', 1929695.41, CAST('2025-04-04' AS DATE)),
            (1, 1, 'Michael Chen', 1940750.90, CAST('2025-04-07' AS DATE)),
            (1, 1, 'Michael Chen', 1910579.34, CAST('2025-04-08' AS DATE)),
            (1, 1, 'Michael Chen', 2115304.61, CAST('2025-04-09' AS DATE)),
            (1, 1, 'Michael Chen', 2028781.78, CAST('2025-04-10' AS DATE)),
            (1, 1, 'Michael Chen', 2068714.49, CAST('2025-04-11' AS DATE)),
            (1, 1, 'Michael Chen', 2073064.91, CAST('2025-04-14' AS DATE)),
            (1, 1, 'Michael Chen', 2065197.13, CAST('2025-04-15' AS DATE)),
            (1, 1, 'Michael Chen', 2002366.45, CAST('2025-04-16' AS DATE)),
            (1, 1, 'Michael Chen', 1987649.50, CAST('2025-04-17' AS DATE)),
            (1, 1, 'Michael Chen', 1933755.14, CAST('2025-04-21' AS DATE)),
            (1, 1, 'Michael Chen', 1981985.15, CAST('2025-04-22' AS DATE)),
            (1, 1, 'Michael Chen', 2026585.84, CAST('2025-04-23' AS DATE)),
            (1, 1, 'Michael Chen', 2080524.54, CAST('2025-04-24' AS DATE)),
            (1, 1, 'Michael Chen', 2107363.59, CAST('2025-04-25' AS DATE)),
            (1, 1, 'Michael Chen', 2100374.74, CAST('2025-04-28' AS DATE)),
            (1, 1, 'Michael Chen', 2110114.59, CAST('2025-04-29' AS DATE)),
            (1, 1, 'Michael Chen', 2107913.69, CAST('2025-04-30' AS DATE)),
            (1, 1, 'Michael Chen', 2156011.74, CAST('2025-05-01' AS DATE)),
            (1, 1, 'Michael Chen', 2188415.26, CAST('2025-05-02' AS DATE)),
            (1, 1, 'Michael Chen', 2175275.86, CAST('2025-05-05' AS DATE)),
            (1, 1, 'Michael Chen', 2153562.38, CAST('2025-05-06' AS DATE)),
            (1, 1, 'Michael Chen', 2174489.62, CAST('2025-05-07' AS DATE)),
            (1, 1, 'Michael Chen', 2190293.50, CAST('2025-05-08' AS DATE)),
            (1, 1, 'Michael Chen', 2186878.52, CAST('2025-05-09' AS DATE)),
            (1, 1, 'Michael Chen', 2276571.90, CAST('2025-05-12' AS DATE)),
            (1, 1, 'Michael Chen', 2294158.31, CAST('2025-05-13' AS DATE)),
            (1, 1, 'Michael Chen', 2302876.02, CAST('2025-05-14' AS DATE)),
            (1, 1, 'Michael Chen', 2300320.22, CAST('2025-05-15' AS DATE)),
            (1, 1, 'Michael Chen', 2314555.65, CAST('2025-05-16' AS DATE)),
            (1, 1, 'Michael Chen', 2324520.11, CAST('2025-05-19' AS DATE)),
            (1, 1, 'Michael Chen', 2315291.43, CAST('2025-05-20' AS DATE)),
            (1, 1, 'Michael Chen', 2276500.44, CAST('2025-05-21' AS DATE)),
            (1, 1, 'Michael Chen', 2283433.38, CAST('2025-05-22' AS DATE)),
            (1, 1, 'Michael Chen', 2264714.30, CAST('2025-05-23' AS DATE)),
            (1, 1, 'Michael Chen', 2316154.48, CAST('2025-05-27' AS DATE)),
            (1, 1, 'Michael Chen', 2302041.55, CAST('2025-05-28' AS DATE)),
            (1, 1, 'Michael Chen', 2321228.53, CAST('2025-05-29' AS DATE)),
            (1, 1, 'Michael Chen', 2312110.69, CAST('2025-05-30' AS DATE)),
            (1, 1, 'Michael Chen', 2327364.17, CAST('2025-06-02' AS DATE)),
            (1, 1, 'Michael Chen', 2340746.18, CAST('2025-06-03' AS DATE)),
            (1, 1, 'Michael Chen', 2346732.13, CAST('2025-06-04' AS DATE)),
            (1, 1, 'Michael Chen', 2343845.09, CAST('2025-06-05' AS DATE)),
            (1, 1, 'Michael Chen', 2373081.62, CAST('2025-06-06' AS DATE)),
            (1, 1, 'Michael Chen', 2384884.43, CAST('2025-06-09' AS DATE)),
            (1, 1, 'Michael Chen', 2395286.99, CAST('2025-06-10' AS DATE)),
            (1, 1, 'Michael Chen', 2383205.70, CAST('2025-06-11' AS DATE)),
            (1, 1, 'Michael Chen', 2400201.45, CAST('2025-06-12' AS DATE)),
            (1, 1, 'Michael Chen', 2376114.55, CAST('2025-06-13' AS DATE)),
            (1, 1, 'Michael Chen', 2401665.48, CAST('2025-06-16' AS DATE)),
            (1, 1, 'Michael Chen', 2384789.48, CAST('2025-06-17' AS DATE)),
            (1, 1, 'Michael Chen', 2385291.25, CAST('2025-06-18' AS DATE)),
            (1, 1, 'Michael Chen', 2369500.96, CAST('2025-06-20' AS DATE)),
            (1, 1, 'Michael Chen', 2385361.95, CAST('2025-06-23' AS DATE)),
            (1, 1, 'Michael Chen', 2419884.71, CAST('2025-06-24' AS DATE)),
            (1, 1, 'Michael Chen', 2435611.60, CAST('2025-06-25' AS DATE)),
            (1, 1, 'Michael Chen', 2460209.23, CAST('2025-06-26' AS DATE)),
            (1, 1, 'Michael Chen', 2480775.90, CAST('2025-06-27' AS DATE)),
            (1, 1, 'Michael Chen', 2480776.78, CAST('2025-06-30' AS DATE)),
            (1, 1, 'Michael Chen', 2469791.76, CAST('2025-07-01' AS DATE)),
            (1, 1, 'Michael Chen', 2478295.66, CAST('2025-07-02' AS DATE)),
            (1, 1, 'Michael Chen', 2505532.12, CAST('2025-07-03' AS DATE)),
            (1, 1, 'Michael Chen', 2492577.25, CAST('2025-07-07' AS DATE)),
            (1, 1, 'Michael Chen', 2488111.44, CAST('2025-07-08' AS DATE)),
            (1, 1, 'Michael Chen', 2515613.99, CAST('2025-07-09' AS DATE)),
            (1, 1, 'Michael Chen', 2519693.44, CAST('2025-07-10' AS DATE)),
            (1, 1, 'Michael Chen', 2522962.79, CAST('2025-07-11' AS DATE)),
            (1, 1, 'Michael Chen', 2523889.01, CAST('2025-07-14' AS DATE)),
            (1, 1, 'Michael Chen', 2533832.89, CAST('2025-07-15' AS DATE)),
            (1, 1, 'Michael Chen', 2535356.90, CAST('2025-07-16' AS DATE)),
            (1, 1, 'Michael Chen', 2549249.60, CAST('2025-07-17' AS DATE)),
            (1, 1, 'Michael Chen', 2547637.88, CAST('2025-07-18' AS DATE)),
            (1, 1, 'Michael Chen', 2551518.87, CAST('2025-07-21' AS DATE)),
            (1, 1, 'Michael Chen', 2538381.09, CAST('2025-07-22' AS DATE)),
            (1, 1, 'Michael Chen', 2562663.71, CAST('2025-07-23' AS DATE)),
            (1, 1, 'Michael Chen', 2581454.95, CAST('2025-07-24' AS DATE)),
            (1, 1, 'Michael Chen', 2587730.43, CAST('2025-07-25' AS DATE)),
            (1, 1, 'Michael Chen', 2593654.84, CAST('2025-07-28' AS DATE)),
            (1, 1, 'Michael Chen', 2582987.12, CAST('2025-07-29' AS DATE)),
            (1, 1, 'Michael Chen', 2589327.57, CAST('2025-07-30' AS DATE)),
            (1, 1, 'Michael Chen', 2605366.57, CAST('2025-07-31' AS DATE)),
            (1, 1, 'Michael Chen', 2534215.75, CAST('2025-08-01' AS DATE)),
            (1, 1, 'Michael Chen', 2571994.16, CAST('2025-08-04' AS DATE)),
            (1, 1, 'Michael Chen', 2558371.84, CAST('2025-08-05' AS DATE)),
            (1, 1, 'Michael Chen', 2577020.66, CAST('2025-08-06' AS DATE)),
            (1, 1, 'Michael Chen', 2573436.01, CAST('2025-08-07' AS DATE)),
            (1, 1, 'Michael Chen', 2587416.99, CAST('2025-08-08' AS DATE)),
            (1, 1, 'Michael Chen', 2581434.67, CAST('2025-08-11' AS DATE)),
            (1, 1, 'Michael Chen', 2604146.57, CAST('2025-08-12' AS DATE)),
            (1, 1, 'Michael Chen', 2605479.36, CAST('2025-08-13' AS DATE)),
            (1, 1, 'Michael Chen', 2622666.70, CAST('2025-08-14' AS DATE)),
            (1, 1, 'Michael Chen', 2619560.17, CAST('2025-08-15' AS DATE)),
            (1, 1, 'Michael Chen', 2619844.35, CAST('2025-08-18' AS DATE)),
            (1, 1, 'Michael Chen', 2587186.97, CAST('2025-08-19' AS DATE)),
            (1, 1, 'Michael Chen', 2573308.83, CAST('2025-08-20' AS DATE)),
            (1, 1, 'Michael Chen', 2563801.25, CAST('2025-08-21' AS DATE)),
            (1, 1, 'Michael Chen', 2603762.61, CAST('2025-08-22' AS DATE)),
            (1, 1, 'Michael Chen', 2594250.30, CAST('2025-08-25' AS DATE)),
            (1, 1, 'Michael Chen', 2603522.33, CAST('2025-08-26' AS DATE)),
            (1, 1, 'Michael Chen', 2611211.61, CAST('2025-08-27' AS DATE)),
            (1, 1, 'Michael Chen', 2618093.41, CAST('2025-08-28' AS DATE)),
            (1, 1, 'Michael Chen', 2592757.92, CAST('2025-08-29' AS DATE)),
            (1, 1, 'Michael Chen', 2570292.19, CAST('2025-09-02' AS DATE)),
            (1, 1, 'Michael Chen', 2574984.64, CAST('2025-09-03' AS DATE)),
            (1, 1, 'Michael Chen', 2608050.89, CAST('2025-09-04' AS DATE)),
            (1, 1, 'Michael Chen', 2575681.00, CAST('2025-09-05' AS DATE)),
            (1, 1, 'Michael Chen', 2590932.17, CAST('2025-09-08' AS DATE)),
            (1, 1, 'Michael Chen', 2605392.55, CAST('2025-09-09' AS DATE)),
            (1, 1, 'Michael Chen', 2605898.17, CAST('2025-09-10' AS DATE)),
            (1, 1, 'Michael Chen', 2618217.79, CAST('2025-09-11' AS DATE)),
            (1, 1, 'Michael Chen', 2621747.16, CAST('2025-09-12' AS DATE)),
            (1, 1, 'Michael Chen', 2636058.66, CAST('2025-09-15' AS DATE)),
            (1, 1, 'Michael Chen', 2626759.25, CAST('2025-09-16' AS DATE)),
            (1, 1, 'Michael Chen', 2612001.92, CAST('2025-09-17' AS DATE)),
            (1, 1, 'Michael Chen', 2628808.30, CAST('2025-09-18' AS DATE)),
            (1, 1, 'Michael Chen', 2644153.26, CAST('2025-09-19' AS DATE));"""
        ]
        
        logger.info(f"✅ Embedded SQL loaded: {len(create_statements)} CREATE, {len(insert_statements)} INSERT statements")
        return create_statements, insert_statements
    
    def create_tables(self) -> List[str]:
        """Create tables from SQL file"""
        try:
            logger.info("🚀 Creating tables from SQL file")
            
            create_statements, _ = self._get_embedded_sql()
            created_tables = []
            
            for i, create_stmt in enumerate(create_statements, 1):
                # Extract table name for logging
                table_match = re.search(r'CREATE EXTERNAL TABLE (\w+)', create_stmt, re.IGNORECASE)
                table_name = table_match.group(1) if table_match else f"table_{i}"
                
                logger.info(f"Creating table {i}/{len(create_statements)}: {table_name}")
                
                response = self.athena_client.start_query_execution(
                    QueryString=create_stmt,
                    QueryExecutionContext={'Database': self.database_name},
                    ResultConfiguration={
                        'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                    }
                )
                
                query_execution_id = response['QueryExecutionId']
                self._wait_for_query_completion(query_execution_id)
                
                created_tables.append(table_name)
                self.created_resources.append(('athena_table', table_name))
                logger.info(f"✅ Table created: {table_name}")
            
            logger.info(f"✅ All {len(created_tables)} tables created successfully")
            return created_tables
            
        except Exception as e:
            raise AthenaSetupError(f"Failed to create tables: {e}")
    
    def insert_data(self) -> int:
        """Insert data into tables sequentially"""
        try:
            logger.info("🚀 Inserting data into tables")
            
            _, insert_statements = self._get_embedded_sql()
            successful_inserts = 0
            
            for i, insert_stmt in enumerate(insert_statements, 1):
                # Extract table name for logging
                table_match = re.search(r'INSERT INTO (\w+)', insert_stmt, re.IGNORECASE)
                table_name = table_match.group(1) if table_match else f"unknown_table_{i}"
                
                logger.info(f"Inserting data {i}/{len(insert_statements)} into table: {table_name}")
                
                try:
                    response = self.athena_client.start_query_execution(
                        QueryString=insert_stmt,
                        QueryExecutionContext={'Database': self.database_name},
                        ResultConfiguration={
                            'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                        }
                    )
                    
                    query_execution_id = response['QueryExecutionId']
                    self._wait_for_query_completion(query_execution_id)
                    
                    successful_inserts += 1
                    logger.info(f"✅ Data inserted into: {table_name}")
                    
                    # Small delay between inserts to avoid throttling
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to insert data into {table_name}: {e}")
                    # Continue with next insert rather than failing completely
                    continue
            
            logger.info(f"✅ Data insertion completed: {successful_inserts}/{len(insert_statements)} successful")
            return successful_inserts
            
        except Exception as e:
            raise AthenaSetupError(f"Failed to insert data: {e}")
    
    def verify_setup(self) -> bool:
        """Verify the setup by running test queries"""
        try:
            logger.info("🔍 Verifying setup with test queries")
            
            # Test query to count records in each table
            test_queries = [
                "SELECT COUNT(*) as advisor_count FROM advisors",
                "SELECT COUNT(*) as client_count FROM clients", 
                "SELECT COUNT(*) as portfolio_count FROM portfolios",
                "SELECT COUNT(*) as security_count FROM securities",
                "SELECT COUNT(*) as holding_count FROM portfolio_holdings",
                "SELECT COUNT(*) as performance_count FROM performance_data",
                "SELECT COUNT(*) as daily_performance_count FROM client_daily_portfolio_performance"
            ]
            
            for query in test_queries:
                response = self.athena_client.start_query_execution(
                    QueryString=query,
                    QueryExecutionContext={'Database': self.database_name},
                    ResultConfiguration={
                        'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                    }
                )
                
                query_execution_id = response['QueryExecutionId']
                self._wait_for_query_completion(query_execution_id)
            
            logger.info("✅ Setup verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup verification failed: {e}")
            return False
    
    def print_status_summary(self):
        """Print comprehensive status summary"""
        print("\n" + "="*60)
        print("🎯 ATHENA DATABASE SETUP SUMMARY")
        print("="*60)
        
        print(f"📅 Setup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 AWS Region: {self.config.get('region_name', 'us-west-2')}")
        
        if self.bucket_name:
            print(f"🪣 S3 Bucket: {self.bucket_name}")
        
        if self.database_name:
            print(f"🗄️  Database: {self.database_name}")
        
        print(f"\n📋 Created Resources ({len(self.created_resources)}):")
        for resource_type, resource_name in self.created_resources:
            print(f"  ✅ {resource_type}: {resource_name}")
        
        print(f"\n📝 Configuration used:")
        for key, value in self.config.items():
            print(f"  • {key}: {value}")
        
        print("\n🔗 Connection Information:")
        print(f"  • S3 Bucket: s3://{self.bucket_name}")
        print(f"  • Athena Database: {self.database_name}")
        print(f"  • Query Results Location: s3://{self.bucket_name}/athena-results/")
        
        print("\n" + "="*60)
    
    def run_setup(self) -> bool:
        """Run the complete setup process"""
        try:
            logger.info("🚀 Starting Athena Database Setup")
            
            # Initialize AWS clients
            self._initialize_aws_clients()
            
            # Create S3 bucket
            self.create_s3_bucket()
            
            # Create Athena database
            self.create_athena_database()
            
            # Update configuration file with generated names
            self._update_config_file()
            
            # Create tables
            self.create_tables()
            
            # Insert data
            self.insert_data()
            
            # Verify setup
            self.verify_setup()
            
            # Print status summary
            self.print_status_summary()
            
            logger.info("🎉 Setup completed successfully!")
            return True
            
        except AthenaSetupError as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during setup: {e}")
            return False

    def delete_athena_resources(self):
        """Delete Athena database and all its tables"""
        try:
            logger.info(f"🗑️  Deleting Athena database: {self.database_name}")
            
            # List all tables in the database
            try:
                response = self.athena_client.list_table_metadata(
                    CatalogName='AwsDataCatalog',
                    DatabaseName=self.database_name
                )
                
                tables = [table['Name'] for table in response.get('TableMetadataList', [])]
                logger.info(f"Found {len(tables)} tables to delete: {tables}")
                
                # Drop each table
                for table_name in tables:
                    try:
                        logger.info(f"Dropping table: {table_name}")
                        query = f"DROP TABLE IF EXISTS {table_name}"
                        response = self.athena_client.start_query_execution(
                            QueryString=query,
                            QueryExecutionContext={'Database': self.database_name},
                            ResultConfiguration={
                                'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                            }
                        )
                        query_execution_id = response['QueryExecutionId']
                        self._wait_for_query_completion(query_execution_id)
                        logger.info(f"✅ Table dropped: {table_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to drop table {table_name}: {e}")
                        
            except Exception as e:
                logger.warning(f"⚠️  Failed to list tables: {e}")
            
            # Drop the database
            try:
                logger.info(f"Dropping database: {self.database_name}")
                query = f"DROP DATABASE IF EXISTS {self.database_name} CASCADE"
                response = self.athena_client.start_query_execution(
                    QueryString=query,
                    ResultConfiguration={
                        'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                    }
                )
                query_execution_id = response['QueryExecutionId']
                self._wait_for_query_completion(query_execution_id)
                logger.info(f"✅ Database dropped: {self.database_name}")
            except Exception as e:
                logger.error(f"❌ Failed to drop database: {e}")
                
        except Exception as e:
            logger.error(f"❌ Failed to delete Athena resources: {e}")
            raise AthenaSetupError(f"Failed to delete Athena resources: {e}")
    
    def delete_s3_bucket(self):
        """Delete S3 bucket and all its contents"""
        try:
            logger.info(f"🗑️  Deleting S3 bucket: {self.bucket_name}")
            
            # Delete all objects in the bucket
            try:
                logger.info("Listing objects in bucket...")
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.bucket_name)
                
                objects_deleted = 0
                for page in pages:
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        if objects:
                            logger.info(f"Deleting {len(objects)} objects...")
                            self.s3_client.delete_objects(
                                Bucket=self.bucket_name,
                                Delete={'Objects': objects}
                            )
                            objects_deleted += len(objects)
                
                logger.info(f"✅ Deleted {objects_deleted} objects from bucket")
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchBucket':
                    logger.warning(f"⚠️  Error deleting objects: {e}")
            
            # Delete all object versions (if versioning is enabled)
            try:
                logger.info("Checking for object versions...")
                paginator = self.s3_client.get_paginator('list_object_versions')
                pages = paginator.paginate(Bucket=self.bucket_name)
                
                versions_deleted = 0
                for page in pages:
                    # Delete versions
                    if 'Versions' in page:
                        versions = [{'Key': v['Key'], 'VersionId': v['VersionId']} 
                                   for v in page['Versions']]
                        if versions:
                            logger.info(f"Deleting {len(versions)} object versions...")
                            self.s3_client.delete_objects(
                                Bucket=self.bucket_name,
                                Delete={'Objects': versions}
                            )
                            versions_deleted += len(versions)
                    
                    # Delete delete markers
                    if 'DeleteMarkers' in page:
                        markers = [{'Key': m['Key'], 'VersionId': m['VersionId']} 
                                  for m in page['DeleteMarkers']]
                        if markers:
                            logger.info(f"Deleting {len(markers)} delete markers...")
                            self.s3_client.delete_objects(
                                Bucket=self.bucket_name,
                                Delete={'Objects': markers}
                            )
                            versions_deleted += len(markers)
                
                if versions_deleted > 0:
                    logger.info(f"✅ Deleted {versions_deleted} object versions/markers")
                    
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchBucket':
                    logger.warning(f"⚠️  Error deleting versions: {e}")
            
            # Delete the bucket
            try:
                logger.info(f"Deleting bucket: {self.bucket_name}")
                self.s3_client.delete_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ S3 bucket deleted: {self.bucket_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucket':
                    logger.warning(f"⚠️  Bucket {self.bucket_name} does not exist")
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Failed to delete S3 bucket: {e}")
            raise AthenaSetupError(f"Failed to delete S3 bucket: {e}")
    
    def delete_resources(self) -> bool:
        """Delete all Athena and S3 resources"""
        try:
            logger.info("🚀 Starting Athena Database Deletion")
            
            # Initialize AWS clients
            self._initialize_aws_clients()
            
            # Delete Athena resources
            self.delete_athena_resources()
            
            # Delete S3 bucket
            self.delete_s3_bucket()
            
            logger.info("🎉 All resources deleted successfully!")
            return True
            
        except AthenaSetupError as e:
            logger.error(f"❌ Deletion failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during deletion: {e}")
            return False

def main():
    """Main function to run the setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Amazon Athena Database Setup Script')
    parser.add_argument('--mode', type=str, required=True,
                       choices=['create', 'delete'],
                       help='Mode: create or delete Athena database resources')
    parser.add_argument('--config-path', type=str, 
                       help='Path to configuration file (default: auto-detect)')
    
    args = parser.parse_args()
    
    try:
        config_path = args.config_path
        
        if args.mode == 'create':
            logger.info("🎯 Mode: CREATE")
            setup = AthenaDatabaseSetup(config_path)
            success = setup.run_setup()
            
            if success:
                print("\n🎉 Database setup completed successfully!")
                sys.exit(0)
            else:
                print("\n❌ Database setup failed. Check logs for details.")
                sys.exit(1)
                
        elif args.mode == 'delete':
            logger.info("🎯 Mode: DELETE")
            
            # Load config to get the bucket and database names
            setup = AthenaDatabaseSetup(config_path)
            
            # Get the names from config
            bucket_name = setup.config.get('s3_bucket_name_for_athena')
            database_name = setup.config.get('database_name')
            
            if not bucket_name or not database_name:
                logger.error("❌ Missing s3_bucket_name_for_athena or database_name in config file")
                logger.error("   Please ensure these values are set in prereqs_config.yaml")
                sys.exit(1)
            
            logger.info(f"📋 S3 Bucket to delete: {bucket_name}")
            logger.info(f"📋 Database to delete: {database_name}")
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete the following resources:")
            print(f"   • Athena Database: {database_name}")
            print(f"   • S3 Bucket: {bucket_name}")
            print(f"   • All tables and data in the database")
            print(f"   • All objects in the S3 bucket")
            
            confirmation = input("\nType 'DELETE' to confirm deletion: ")
            if confirmation != 'DELETE':
                print("❌ Deletion cancelled")
                sys.exit(0)
            
            # Set the names from config
            setup.bucket_name = bucket_name
            setup.database_name = database_name
            
            # Delete resources
            success = setup.delete_resources()
            
            if success:
                print("\n🎉 Resources deleted successfully!")
                sys.exit(0)
            else:
                print("\n❌ Deletion failed. Check logs for details.")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()