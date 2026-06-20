import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import JSZip from 'jszip';

const MAX_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_EXT = ['.csv', '.xlsx'];

export function validateSampleFile(file) {
  const name = (file?.name || '').toLowerCase();
  if (!ALLOWED_EXT.some((ext) => name.endsWith(ext))) {
    return 'Only .csv or .xlsx files are supported';
  }
  if (file.size > MAX_SIZE) return 'File is too large (max 5MB)';
  return '';
}

// Reads only headers + a couple of sample rows — used as a format guide for the LLM prompt,
// not the full file contents.
export async function parseSampleFile(file) {
  const name = (file.name || '').toLowerCase();
  if (name.endsWith('.csv')) {
    const text = await file.text();
    const { data } = Papa.parse(text, { header: true, skipEmptyLines: true, preview: 3 });
    const headers = data.length ? Object.keys(data[0]) : [];
    return { format: 'csv', headers, sampleRows: data.slice(0, 2) };
  }

  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: 'array' });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: '' });
  const headers = rows.length ? Object.keys(rows[0]) : [];
  return { format: 'xlsx', headers, sampleRows: rows.slice(0, 2) };
}

// Full parse (all rows) — used when the uploaded file IS the test case data, not just a format sample.
export async function parseFullFile(file) {
  const name = (file.name || '').toLowerCase();
  if (name.endsWith('.csv')) {
    const text = await file.text();
    const { data } = Papa.parse(text, { header: true, skipEmptyLines: true });
    return { columns: data.length ? Object.keys(data[0]) : [], rows: data };
  }

  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: 'array' });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: '' });
  return { columns: rows.length ? Object.keys(rows[0]) : [], rows };
}

export function toCsvBlob(columns, rows) {
  const csv = Papa.unparse({ fields: columns, data: rows.map((r) => columns.map((c) => r[c] ?? '')) });
  return new Blob([csv], { type: 'text/csv' });
}

export function toXlsxBlob(columns, rows) {
  const ws = XLSX.utils.json_to_sheet(rows, { header: columns });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Test Cases');
  const out = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new Blob([out], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

export async function buildZip(files) {
  const zip = new JSZip();
  files.forEach((f) => zip.file(f.filename, f.content));
  return zip.generateAsync({ type: 'blob' });
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
