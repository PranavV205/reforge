import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { Account } from '../ledger/account.entity';
import { Transaction } from '../transactions/transaction.entity';

/**
 * Postgres connection for the `reforge` application database.
 *
 * Note this is a different database from the one Temporal uses, on the same server.
 * Temporal owns `temporal`; this owns `reforge`, created by scripts/init-db.sql.
 */
export function databaseConfig(): TypeOrmModuleOptions {
  return {
    type: 'postgres',
    host: process.env.POSTGRES_HOST || 'localhost',
    port: Number(process.env.POSTGRES_PORT || 5432),
    username: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || 'postgres',
    database: process.env.POSTGRES_DB || 'reforge',
    entities: [Account, Transaction],

    // gen_random_uuid() is core in Postgres 13+. Without this, TypeORM emits
    // uuid_generate_v4() in the DDL, which needs the uuid-ossp extension installed
    // and fails on a stock postgres:15 image.
    uuidExtension: 'pgcrypto',

    // Dev convenience: TypeORM creates and alters tables to match the entities on
    // boot. scripts/init-db.sql cannot do this job, because docker-entrypoint-initdb.d
    // only runs on the first boot of an empty volume, so anyone with an existing
    // postgres_data volume would never get the tables.
    //
    // Replace this with real migrations before production: synchronize will happily
    // drop a column to match an entity.
    synchronize: process.env.NODE_ENV !== 'production',
  };
}
