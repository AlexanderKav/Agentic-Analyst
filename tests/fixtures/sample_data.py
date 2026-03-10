"""Shared test datasets for integration tests."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_transaction_data():
    """Realistic transaction data for testing"""
    np.random.seed(42)  # For reproducible tests
    dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'customer': np.random.choice(['Acme Corp', 'Beta Inc', 'Gamma LLC', 'Delta Ltd'], len(dates)),
        'product': np.random.choice(['Widget Pro', 'Widget Basic', 'Widget Enterprise', 'Gadget'], len(dates)),
        'region': np.random.choice(['North America', 'Europe', 'Asia', 'South America'], len(dates)),
        'revenue': np.random.randint(500, 5000, len(dates)),
        'cost': np.random.randint(200, 3000, len(dates)),
        'quantity': np.random.randint(1, 20, len(dates)),
        'payment_status': np.random.choice(['paid', 'pending', 'overdue'], len(dates))
    })


@pytest.fixture
def precise_test_data():
    """Test data with known values for precise verification"""
    return pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'revenue': [1000, 2000, 1500],
        'cost': [400, 800, 600],
        'customer': ['A', 'B', 'A'],
        'product': ['X', 'Y', 'X'],
        'region': ['North', 'South', 'North'],
        'payment_status': ['paid', 'pending', 'paid'],
        'quantity': [10, 20, 15]
    })


@pytest.fixture
def sample_business_data():
    """Sample business data for insight agent testing"""
    return {
        "compute_kpis": {
            "total_revenue": 150000.0,
            "total_cost": 85000.0,
            "total_profit": 65000.0,
            "profit_margin": 0.43,
            "avg_order_value": 1250.0
        },
        "monthly_revenue": {
            "2024-01": 45000,
            "2024-02": 52000,
            "2024-03": 53000
        },
        "monthly_growth": {
            "2024-01": 0,
            "2024-02": 0.15,
            "2024-03": 0.02
        },
        "revenue_by_customer": {
            "Customer A": 75000,
            "Customer B": 45000,
            "Customer C": 30000
        },
        "revenue_by_product": {
            "Enterprise Plan": 214265.0,
            "Premium Plan": 64793.0,
            "Basic Plan": 28913.0
        },
        "detect_revenue_spikes": {
            "2024-02-15": 15000
        }
    }


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'revenue': [1000, 1200, 1100, 1300, 1250],
        'customer': ['A', 'B', 'A', 'C', 'B']
    })


@pytest.fixture
def varied_data():
    """Data with various types to test format compatibility"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'revenue': [100.50, 200.75, 150.25, 300.00, 250.50, 175.25, 225.75, 275.00, 125.50, 195.25],
        'cost': [50.25, 100.50, 75.25, 150.00, 125.25, 87.50, 112.75, 137.50, 62.75, 97.50],
        'customer': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C'],
        'product': ['X', 'Y', 'X', 'Z', 'Y', 'X', 'Z', 'Y', 'X', 'Z'],
        'quantity': [1, 2, 1, 3, 2, 1, 3, 2, 1, 2]
    })


@pytest.fixture
def bad_data():
    """Problematic data to test error handling"""
    return pd.DataFrame({
        'date': ['2024-01-01', 'invalid-date', None],
        'revenue': [100, -500, None],
        'cost': [50, None, 'invalid'],
        'customer': ['A', '', None],
        'payment_status': ['paid', 'unknown', None]
    })


@pytest.fixture
def empty_data():
    """Empty dataframe"""
    return pd.DataFrame()


@pytest.fixture
def missing_columns_data():
    """Data with missing required columns"""
    return pd.DataFrame({
        'some_column': [1, 2, 3],
        'another_column': ['x', 'y', 'z']
    })


@pytest.fixture
def temp_chart_dir():
    """Temporary directory for chart output"""
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)