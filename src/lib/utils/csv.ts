import { stringify } from '@fast-csv/format';

export async function toCSV(rows: any[]): Promise<Buffer> {
  return await new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    const stream = stringify({ headers: true });
    stream.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    stream.on('end', () => resolve(Buffer.concat(chunks)));
    stream.on('error', reject);
    for (const r of rows) stream.write(r);
    stream.end();
  });
}
