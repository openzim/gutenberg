declare module 'sql.js/dist/sql-wasm.js' {
  interface SqlJsInitConfig {
    locateFile: (file: string) => string
  }

  interface SqlJsStatic {
    Database: new (data?: Uint8Array) => SqlJsDatabase
  }

  interface SqlJsDatabase {
    prepare: (sql: string) => any
    run: (sql: string) => void
    exec: (sql: string) => any
    close: () => void
  }

  const initSqlJs: (config: SqlJsInitConfig) => Promise<SqlJsStatic>
  export default initSqlJs
}
