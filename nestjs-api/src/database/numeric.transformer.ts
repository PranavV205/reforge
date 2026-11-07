import { ValueTransformer } from 'typeorm';

/**
 * Postgres returns DECIMAL as a string, deliberately, so that driver-level float
 * conversion can't lose precision. Money is stored as DECIMAL(14,2) for exactness,
 * but read back as a number so callers aren't doing string math everywhere.
 *
 * This is safe for reads: balances stay far below Number.MAX_SAFE_INTEGER. It is not
 * a licence to do ledger arithmetic in JS. Applying a balance change belongs in SQL
 * (`balance = balance - :amount`) so the exact decimal value is what gets updated.
 */
export const numericTransformer: ValueTransformer = {
  to: (value?: number | null) => value,
  from: (value?: string | null) =>
    value === null || value === undefined ? value : Number(value),
};
