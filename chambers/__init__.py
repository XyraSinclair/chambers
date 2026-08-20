"""chambers — formal and executable models for bounded computation over
private data. This file makes `chambers` a regular package so every import
path resolves each module to ONE object per process (the namespace-package
era allowed `ledger.Ledger is not chambers.kernel.ledger.Ledger`)."""
