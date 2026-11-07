import { Column, CreateDateColumn, Entity, PrimaryColumn } from 'typeorm';
import { numericTransformer } from '../database/numeric.transformer';

/**
 * The simulated account ledger: one balance per UPI ID.
 *
 * This exists because the model takes four balance features (sender before and after,
 * receiver before and after) and the payment form can only supply sender, payee and
 * amount. Without a stored balance per UPI ID, a third of the feature vector cannot be
 * produced from a live transaction.
 */
@Entity('accounts')
export class Account {
  /**
   * The UPI ID is the natural key. There is no surrogate id: accounts are created on
   * first use and every ledger lookup is by UPI ID.
   */
  @PrimaryColumn({ name: 'upi_id', type: 'varchar', length: 255 })
  upiId: string;

  /** Random starting balance on first use. There is no signup in the demo. */
  @Column({ type: 'decimal', precision: 14, scale: 2, transformer: numericTransformer })
  balance: number;

  /**
   * Merchants report 0 for both receiver balance columns, because that is how PaySim
   * records them. Reporting real merchant balances would push live features away from
   * the training distribution, and the KS drift check would start firing on our own
   * app's output instead of on actual drift.
   */
  @Column({ name: 'is_merchant', type: 'boolean', default: false })
  isMerchant: boolean;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;
}
