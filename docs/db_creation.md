CREATE USER hemant WITH PASSWORD 'password';
ALTER ROLE hemant SET client_encoding TO 'utf8';
ALTER ROLE hemant SET timezone TO 'UTC';
ALTER ROLE hemant SET default_transaction_isolation TO 'read committed';

GRANT ALL PRIVILEGES ON DATABASE prompt_registry TO hemant;

// connect to the database
psql -U hemant -d prompt_registry -h localhost

// set the database url in env
DATABASE_URL=postgresql+asyncpg://hemant:password@localhost:5432/prompt_registry
