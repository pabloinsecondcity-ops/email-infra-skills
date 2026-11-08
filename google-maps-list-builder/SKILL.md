---
name: google-maps-list-builder
description: >-
  Use when Pablo wants to scrape Google Maps for local businesses by category
  and location (restaurants, clinics, gyms, salons, contractors) into a CSV
  ready for cold email enrichment, via the RapidAPI Maps Data API.
---
# Google Maps List Builder

Scrapes business listings from Google Maps. Give it a search query (e.g. "pizza restaurant") and a location (zip, city, or coordinates); it returns structured data for every matching business as CSV.

## How this fits the cold email flow

Google Maps gives COMPANIES (name, domain, phone, address, ratings), not PEOPLE.

1. Run this skill to get a CSV of businesses with `company_domain`
2. **Qualify a sample of 50** with an ICP prompt (icp-prompt-builder) before paying for enrichment
3. Find owners/managers (blitz-list-builder, or website owner research per `list-build` STEP 5)
4. Email waterfall to fill emails
5. Upload to Smartlead

## Required step: qualify first

**Do not skip.** Maps will return 10,000 "pizza restaurants in Illinois," most outside the real ICP. Sample ~50: evaluate 10 with an AI qualification prompt, collect corrections, refine, run the next 10, stop when 2 rounds need no corrections, then apply the tuned prompt to the rest.

**Why:** owner-finding and waterfall cost $0.10-$0.30 per contact; on 10,000 businesses that's $1K-$3K. Qualifying first saves 50-80% on average.

## Prerequisites

1. Node.js 18+ and npm
2. RapidAPI account subscribed to the **Maps Data API** (https://rapidapi.com/alexanderxbx/api/maps-data); key is the `X-RapidAPI-Key` header value. No Google Cloud account needed.

## Project setup

```bash
mkdir google-maps-scraper && cd google-maps-scraper
npm init -y
npm install typescript bottleneck
npm install -D @types/node tsx
```

`package.json` scripts: `"scrape": "tsx src/index.ts"`. `tsconfig.json`: target ES2022, module ESNext, moduleResolution bundler, esModuleInterop, strict, outDir dist, rootDir src, skipLibCheck, include src.

Key via env var `RAPIDAPI_KEY` (or `.env`, gitignored).

## File structure

```
google-maps-scraper/
  data/us-zip-codes.csv   # 42,734 US zips: zip,primary_city,state,timezone,area_codes,world_region,country,latitude,longitude,irs_estimated_population
  src/index.ts            # CLI entry
  src/client.ts           # RapidAPI client with rate limiting
  src/types.ts            # interfaces
  src/csv.ts              # CSV export
  src/zips.ts             # zip loader (state, city, min population)
```

## src/types.ts

```typescript
export interface SearchParams { query: string; lat?: number; lng?: number; limit?: number; zoom?: number; country?: string; }
export interface Place {
  place_id: string; name: string; address: string; lat: number; lng: number;
  rating?: number; reviews_count?: number; phone?: string; website?: string; types?: string[]; category?: string;
}
```

## src/zips.ts

```typescript
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

export interface ZipEntry { zip: string; city: string; state: string; lat: number; lng: number; population: number; }
let cache: ZipEntry[] | null = null;

function loadAll(): ZipEntry[] {
  if (cache) return cache;
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const raw = readFileSync(join(__dirname, '..', 'data', 'us-zip-codes.csv'), 'utf-8');
  cache = raw.trim().split('\n').slice(1).map(line => {
    const parts: string[] = []; let cur = ''; let q = false;
    for (const ch of line) { if (ch === '"') { q = !q; continue; } if (ch === ',' && !q) { parts.push(cur); cur = ''; continue; } cur += ch; }
    parts.push(cur);
    return { zip: parts[0]?.padStart(5, '0') || '', city: parts[1] || '', state: parts[2] || '',
      lat: parseFloat(parts[7]) || 0, lng: parseFloat(parts[8]) || 0, population: parseInt(parts[9]) || 0 };
  }).filter(z => z.zip.length === 5);
  return cache;
}
export const getZipsByState = (s: string) => loadAll().filter(z => z.state.toUpperCase() === s.toUpperCase());
export const getZipsByCity = (city: string, state?: string) => loadAll().filter(z => z.city.toLowerCase().includes(city.toLowerCase()) && (!state || z.state.toUpperCase() === state.toUpperCase()));
export const getZipsByMinPopulation = (min: number, state?: string) => loadAll().filter(z => z.population >= min && (!state || z.state.toUpperCase() === state.toUpperCase()));
```

## src/client.ts

```typescript
import Bottleneck from 'bottleneck';
import type { SearchParams, Place } from './types.js';

export class GoogleMapsClient {
  private limiter: Bottleneck; private apiKey: string; private host = 'maps-data.p.rapidapi.com'; private maxRetries: number;
  constructor(opts: { apiKey: string; requestsPerSecond?: number; maxRetries?: number }) {
    this.apiKey = opts.apiKey; this.maxRetries = opts.maxRetries ?? 3;
    this.limiter = new Bottleneck({ maxConcurrent: 1, minTime: Math.floor(1000 / (opts.requestsPerSecond ?? 2)) });
  }
  async search(p: SearchParams): Promise<Place[]> {
    const r: any = await this.request('searchmaps.php', {
      query: p.query, limit: String(p.limit ?? 20), country: p.country ?? 'us',
      ...(p.lat != null && { lat: String(p.lat) }), ...(p.lng != null && { lng: String(p.lng) }), ...(p.zoom != null && { zoom: String(p.zoom) }),
    });
    if (r.error) throw new Error(`Search failed: ${r.error}`);
    return (r.data || []).map((i: any) => ({
      place_id: i.place_id || '', name: i.title || i.name || '', address: i.address || '', lat: i.latitude || 0, lng: i.longitude || 0,
      rating: i.rating, reviews_count: i.reviews, phone: i.phone, website: i.website,
      types: i.types || (i.type ? [i.type] : []), category: i.category || i.type,
    }));
  }
  async geocode(query: string, country = 'us') {
    const r: any = await this.request('geocoding.php', { query: `${query}, ${country.toUpperCase()}` });
    if (!r.latitude || !r.longitude) throw new Error(`Could not geocode: ${query}`);
    return { lat: r.latitude, lng: r.longitude };
  }
  private request(endpoint: string, params: Record<string, string>) { return this.limiter.schedule(() => this.retry(endpoint, params)); }
  private async retry(endpoint: string, params: Record<string, string>, attempt = 0): Promise<any> {
    const url = new URL(`https://${this.host}/${endpoint}`);
    for (const [k, v] of Object.entries(params)) if (v != null) url.searchParams.set(k, v);
    try {
      const res = await fetch(url.toString(), { headers: { 'X-RapidAPI-Key': this.apiKey, 'X-RapidAPI-Host': this.host } });
      if (!res.ok) { const e: any = new Error(`API ${res.status}: ${res.statusText}`); e.statusCode = res.status; throw e; }
      return await res.json();
    } catch (err: any) {
      const ok = attempt < this.maxRetries && (err.statusCode === 429 || err.statusCode >= 500 || err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT');
      if (ok) { await new Promise(r => setTimeout(r, 1000 * 2 ** attempt)); return this.retry(endpoint, params, attempt + 1); }
      throw err;
    }
  }
}
```

## src/csv.ts

```typescript
import { writeFile, mkdir } from 'fs/promises';
import { dirname } from 'path';
import type { Place } from './types.js';
const HEADERS = ['place_id','name','address','phone','website','rating','reviews_count','lat','lng','category'];
const esc = (v: any) => v == null ? '' : (s => /[,"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s)(String(v));
export async function exportCSV(places: Place[], out: string) {
  await mkdir(dirname(out), { recursive: true });
  await writeFile(out, [HEADERS.join(','), ...places.map(p => HEADERS.map(h => esc((p as any)[h])).join(','))].join('\n') + '\n', 'utf-8');
}
```

## src/index.ts

```typescript
import { GoogleMapsClient } from './client.js';
import { exportCSV } from './csv.js';
import { getZipsByState, getZipsByMinPopulation } from './zips.js';
import type { Place } from './types.js';

const arg = (a: string[], p: string) => { const m = a.find(x => x.startsWith(p)); return m ? m.split('=').slice(1).join('=') : undefined; };

async function main() {
  const a = process.argv.slice(2);
  const query = arg(a, '--query='), zips = arg(a, '--zips='), cities = arg(a, '--cities='), state = arg(a, '--state='), minPop = arg(a, '--min-pop=');
  const limit = parseInt(arg(a, '--limit=') || '20', 10), output = arg(a, '--output=') || './output/results.csv';
  if (!query || (!zips && !cities && !state)) { console.log('Usage: --query="dentist" (--zips=10014,10013 | --cities="Austin TX,Dallas TX" | --state=TX [--min-pop=10000]) [--limit=20] [--output=path]'); process.exit(1); }
  const apiKey = process.env.RAPIDAPI_KEY; if (!apiKey) { console.error('RAPIDAPI_KEY is required'); process.exit(1); }
  const locs: string[] = [];
  if (zips) locs.push(...zips.split(',').map(s => s.trim()));
  if (cities) locs.push(...cities.split(',').map(s => s.trim()));
  if (state) { const n = minPop ? parseInt(minPop, 10) : 0; locs.push(...(n > 0 ? getZipsByMinPopulation(n, state) : getZipsByState(state)).map(z => z.zip)); }
  const client = new GoogleMapsClient({ apiKey, requestsPerSecond: 2 });
  const all: Place[] = [];
  for (const [i, loc] of locs.entries()) {
    try { const r = await client.search({ query: `${query} in ${loc}`, limit, country: 'us' }); all.push(...r); console.log(`[${i + 1}/${locs.length}] ${loc}: ${r.length}`); }
    catch (e: any) { console.error(`${loc}: ${e.message}`); }
  }
  const seen = new Set<string>(); const unique = all.filter(p => !seen.has(p.place_id) && (seen.add(p.place_id), true));
  console.log(`Total ${all.length}, ${unique.length} unique`);
  await exportCSV(unique, output);
}
main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
```

## Running it

```bash
npm run scrape -- --query="pizza restaurant" --zips=10014,10013,10012
npm run scrape -- --query="dentist" --state=TX --min-pop=5000
npm run scrape -- --query="gym" --cities="Austin TX,Dallas TX,San Antonio TX"
npm run scrape -- --query="gym" --zips=90210 --output=./data/gyms.csv
```

Optional: the original also had an Express `src/server.ts` (simple form, POST /scrape returns a CSV download) deployable to Railway, Render, Fly.io, Vercel or Docker.

## API reference

Maps Data API endpoints: `searchmaps.php` (query + location), `geocoding.php` (address/zip to lat/lng), `nearby.php` (near a point), `place.php` (one business by place_id). Client is fixed at 2 requests/second with retries on 429s. Fields: place_id, name, address, phone, website, rating, reviews_count, lat/lng, types/category.

## Tips

- "query in zipcode" works best for US searches.
- 20 results per search max; cover more with overlapping zips.
- Dedup by `place_id`.
- Use `types` to filter irrelevant results (e.g. drop "bar" when searching "restaurant").
- Under 200 businesses means the query or location is too narrow; widen before proceeding.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- `RAPIDAPI_KEY` is not set on the box. Pablo adds it as an env var; never paste it into a skill or chat.
- The zip CSV, blitz-list-builder, email-waterfall, icp-prompt-builder and list-quality-scorecard were not in the export.
- Output CSVs go to `/workspace/`.
