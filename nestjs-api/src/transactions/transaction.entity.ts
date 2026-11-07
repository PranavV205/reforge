import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { numericTransformer } from '../database/numeric.transformer';

/** PAYMENT pays a merchant, TRANSFER sends to a UPI ID, CASH_OUT withdraws. */
export type TransactionType = 'PAYMENT' | 'TRANSFER' | 'CASH_OUT';

export type Verdict = 'fraud' | 'legitimate';

/**
 * Every scored transaction: the payment, the four balance features the ledger
 * produced for it, what the model said, and the ground truth label.
 */
@Entity('transactions')
export class Transaction {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'sender_upi_id', type: 'varchar', length: 255 })
  senderUpiId: string;

  @Column({ type: 'varchar', length: 20 })
  type: TransactionType;

  /** A merchant name, a UPI ID, or a cash agent account, depending on `type`. */
  @Column({ type: 'varchar', length: 255 })
  payee: string;

  @Column({ type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  amount: number;

  // The four PaySim balance features. Filled in by the ledger, never by the client,
  // so a caller cannot hand the model whatever balances it likes.
  @Column({ name: 'old_balance_orig', type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  oldBalanceOrig: number;

  @Column({ name: 'new_balance_orig', type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  newBalanceOrig: number;

  @Column({ name: 'old_balance_dest', type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  oldBalanceDest: number;

  @Column({ name: 'new_balance_dest', type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  newBalanceDest: number;

  /** What the model predicted. This is a guess, not the truth: see `isFraud`. */
  @Column({ type: 'varchar', length: 20 })
  verdict: Verdict;

  /** `predict_proba` for the fraud class, 0 to 1. Uncalibrated. */
  @Column({ type: 'decimal', precision: 4, scale: 3, transformer: numericTransformer })
  confidence: number;

  /** Which model version produced the verdict, for auditing a bad call later. */
  @Column({ name: 'model_version', type: 'varchar', length: 20 })
  modelVersion: string;

  /** Indexed: the dashboard reads recent transactions and fraud rate by time window. */
  @Index()
  @CreateDateColumn({ name: 'scored_at', type: 'timestamptz' })
  scoredAt: Date;

  /**
   * Ground truth, and the model's training target.
   *
   * Nullable because "nobody has disputed this yet and the window has not closed" is a
   * real state, not missing data. Nothing on the scoring path may read this column:
   * the only legitimate reader is retraining, and only for rows whose
   * `labelAvailableAt` has already passed.
   */
  @Column({ name: 'is_fraud', type: 'boolean', nullable: true })
  isFraud: boolean | null;

  /**
   * When training is allowed to see `isFraud`. Set to creation time plus
   * LABEL_DELAY_SECONDS, standing in for a real 30 to 90 day chargeback window.
   * Indexed because the retraining query filters on it.
   */
  @Index()
  @Column({ name: 'label_available_at', type: 'timestamptz', nullable: true })
  labelAvailableAt: Date | null;
}
