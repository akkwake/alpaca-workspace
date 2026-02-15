-- TradingView webhook signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'tradingview',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    price NUMERIC,
    stop_loss NUMERIC,
    take_profit NUMERIC,
    quantity NUMERIC,
    strategy TEXT,
    confidence NUMERIC,
    raw_payload JSONB,
    processed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol);
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_processed ON signals (processed) WHERE NOT processed;

-- Normalized daily bars from Alpaca
CREATE TABLE IF NOT EXISTS market_data_daily (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume BIGINT NOT NULL,
    source TEXT NOT NULL DEFAULT 'alpaca',
    UNIQUE (symbol, date, source)
);

CREATE INDEX IF NOT EXISTS idx_market_data_daily_symbol_date
    ON market_data_daily (symbol, date DESC);
