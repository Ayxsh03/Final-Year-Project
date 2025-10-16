import parquet from 'parquetjs-lite';

export async function toParquet(rows: any[]): Promise<Buffer> {
  if (!rows.length) return Buffer.from([]);
  const schemaObj: Record<string, any> = {};
  for (const k of Object.keys(rows[0])) {
    const v = rows[0][k];
    schemaObj[k] = { type: typeof v === 'number' ? 'DOUBLE' : 'UTF8', optional: true };
  }
  const schema = new parquet.ParquetSchema(schemaObj);
  const filePath = '/tmp/export.parquet';
  const writer = await parquet.ParquetWriter.openFile(schema, filePath);
  for (const r of rows) await writer.appendRow(r);
  await writer.close();
  const fs = await import('fs');
  return fs.readFileSync(filePath);
}
