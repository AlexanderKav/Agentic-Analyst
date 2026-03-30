-- scripts/init-mysql.sql
-- Create the sales table with standard column names
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,  -- Changed from sale_date to date
    customer VARCHAR(100),
    product VARCHAR(100),
    region VARCHAR(50),
    revenue DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    currency VARCHAR(3),
    quantity INT,
    payment_status VARCHAR(20),
    notes TEXT
);

-- Insert sample data (using 'date' instead of 'sale_date')
INSERT INTO sales (date, customer, product, region, revenue, cost, currency, quantity, payment_status, notes) VALUES
('2024-01-03', 'Acme Corp', 'Premium Plan', 'US', 1299.99, 723.45, 'USD', 2, 'paid', NULL),
('2024-01-05', 'BetaCo', 'Basic Plan', 'EU', 849.5, 412.3, 'EUR', 3, 'paid', 'First time customer'),
('2024-01-08', 'Delta Inc', 'Enterprise Plan', 'APAC', 5999, 2850, 'USD', 1, 'paid', 'Annual contract'),
('2024-01-12', 'Gamma LLC', 'Premium Plan', 'US', 1349.99, 789.5, 'USD', 2, 'paid', NULL),
('2024-01-15', 'Acme Corp', 'Basic Plan', 'US', 949.99, 502.3, 'USD', 3, 'pending', NULL),
('2024-01-18', 'Zeta Corp', 'Premium Plan', 'US', 1399.99, 823.45, 'USD', 2, 'paid', NULL),
('2024-01-20', 'BetaCo', 'Enterprise Plan', 'EU', 5499, 2675, 'EUR', 1, 'paid', 'Quarterly payment'),
('2024-01-22', NULL, 'Basic Plan', 'LATAM', 459.5, 289.3, 'USD', 2, 'failed', 'Missing customer'),
('2024-01-25', 'Theta Ltd', 'Premium Plan', 'APAC', 1199.99, 689.5, 'USD', 2, 'paid', NULL),
('2024-01-28', 'Acme Corp', 'Enterprise Plan', 'US', 6499, 3120, 'USD', 1, 'paid', 'Expansion deal'),
('2024-01-30', 'Iota Inc', 'Basic Plan', 'US', 449.99, 267.8, 'USD', 2, 'paid', NULL),
('2024-02-02', 'BetaCo', 'Premium Plan', 'EU', 1249.5, 689.3, 'EUR', 2, 'paid', NULL),
('2024-02-05', 'Delta Inc', 'Basic Plan', 'APAC', 789.99, 423.5, 'USD', 3, 'paid', NULL),
('2024-02-07', 'Kappa LLC', 'Enterprise Plan', 'US', 5799, 2710, 'USD', 1, 'refunded', 'Customer cancelled'),
('2024-02-10', 'Acme Corp', 'Basic Plan', 'US', 899.99, 489.3, 'USD', 3, 'paid', NULL),
('2024-02-12', 'Gamma LLC', 'Premium Plan', 'US', 1399.99, 812.45, 'USD', 2, 'paid', NULL),
('2024-02-15', 'Lambda Ltd', 'Enterprise Plan', 'EU', 6299, 3010, 'EUR', 1, 'paid', NULL),
('2024-02-18', 'BetaCo', 'Basic Plan', 'EU', 799.5, 398.3, 'EUR', 3, 'paid', NULL),
('2024-02-20', 'Delta Inc', 'Premium Plan', 'APAC', 1099.99, 623.5, 'USD', 2, 'paid', NULL),
('2024-02-22', NULL, 'Enterprise Plan', 'LATAM', 4799, 2390, 'USD', 1, 'pending', 'Missing customer'),
('2024-02-25', 'Acme Corp', 'Premium Plan', 'US', 1299.99, 712.45, 'USD', 2, 'paid', NULL),
('2024-02-28', 'Theta Ltd', 'Basic Plan', 'APAC', 549.99, 312.3, 'USD', 2, 'paid', NULL),
('2024-03-02', 'Zeta Corp', 'Enterprise Plan', 'US', 5999, 2910, 'USD', 1, 'paid', NULL),
('2024-03-05', 'BetaCo', 'Premium Plan', 'EU', 1199.5, 678.3, 'EUR', 2, 'paid', NULL),
('2024-03-08', 'Gamma LLC', 'Basic Plan', 'US', 799.99, 423.5, 'USD', 3, 'paid', NULL),
('2024-03-10', 'Delta Inc', 'Premium Plan', 'APAC', 1299.99, 723.45, 'USD', 2, 'paid', NULL),
('2024-03-12', 'Acme Corp', 'Enterprise Plan', 'US', 6799, 3290, 'USD', 1, 'paid', NULL),
('2024-03-15', 'Mu Inc', 'Premium Plan', 'US', 1199.99, 689.5, 'USD', 2, 'paid', 'New customer'),
('2024-03-18', 'BetaCo', 'Basic Plan', 'EU', 749.5, 389.3, 'EUR', 3, 'paid', NULL),
('2024-03-20', 'Kappa LLC', 'Basic Plan', 'US', 499.99, 267.8, 'USD', 2, 'refunded', 'Quality issues'),
('2024-03-22', 'Theta Ltd', 'Enterprise Plan', 'APAC', 5499, 2675, 'USD', 1, 'paid', NULL),
('2024-03-25', 'Acme Corp', 'Premium Plan', 'US', 1349.99, 789.5, 'USD', 2, 'paid', NULL),
('2024-03-28', 'Lambda Ltd', 'Premium Plan', 'EU', 1299.5, 712.3, 'EUR', 2, 'paid', NULL),
('2024-03-30', NULL, 'Basic Plan', 'LATAM', 499.99, 278.5, 'USD', 2, 'failed', NULL);

-- Create indexes
CREATE INDEX idx_date ON sales(date);
CREATE INDEX idx_customer ON sales(customer);
CREATE INDEX idx_region ON sales(region);
CREATE INDEX idx_payment_status ON sales(payment_status);

-- Create a view for monthly revenue
CREATE VIEW monthly_revenue AS
SELECT 
    DATE_FORMAT(date, '%Y-%m-01') as month,
    region,
    SUM(revenue) as total_revenue,
    COUNT(*) as transaction_count,
    AVG(revenue) as avg_transaction_value
FROM sales
WHERE payment_status = 'paid'
GROUP BY DATE_FORMAT(date, '%Y-%m-01'), region
ORDER BY month DESC;

-- Create a view for customer lifetime value
CREATE VIEW customer_lifetime_value AS
SELECT 
    customer,
    COUNT(*) as purchase_count,
    SUM(revenue) as total_spent,
    AVG(revenue) as avg_purchase_value,
    MIN(date) as first_purchase,
    MAX(date) as last_purchase
FROM sales
WHERE customer IS NOT NULL AND payment_status = 'paid'
GROUP BY customer
ORDER BY total_spent DESC;

-- Grant permissions
GRANT SELECT ON sales_db.* TO 'analyst_user'@'%';