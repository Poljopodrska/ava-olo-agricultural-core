-- Test SQL for AWS RDS
CREATE TABLE IF NOT EXISTS test_connection (
    id SERIAL PRIMARY KEY,
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_connection (message) VALUES ('Database connected successfully!');

SELECT * FROM test_connection;
