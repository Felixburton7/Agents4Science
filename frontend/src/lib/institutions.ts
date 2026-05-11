import data from "@/data/institutions.json";

export interface Institution {
  id: string;
  name: string;
  city: string;
  country?: string;
  lat: number;
  lon: number;
  domain?: string;
  badge: string; // public path to badge image (SVG or PNG)
  pi: {
    real: string;
    display: string;
  };
}

export interface Origin {
  id: string;
  name: string;
  city: string;
  lat: number;
  lon: number;
  badge: string;
}

// Map an institution id -> served badge URL. The fetcher writes either .svg
// (real Wikimedia crest) or .png (monogram fallback); we resolve dynamically
// at the next.config layer using a small helper. Since Next.js public/ is
// flat, both extensions are queryable directly.
const KNOWN_SVG = new Set([
  "cambridge_uk",
  "cambridge_group",
  "mit",
  "stanford",
  "oxford",
  "berkeley",
  "eth",
  "tum",
]);

function badgePath(id: string): string {
  return KNOWN_SVG.has(id) ? `/badges/${id}.svg` : `/badges/${id}.png`;
}

export const ORIGIN: Origin = {
  id: data.origin.id,
  name: data.origin.name,
  city: data.origin.city,
  lat: data.origin.lat,
  lon: data.origin.lon,
  badge: badgePath(data.origin.id),
};

export const INSTITUTIONS: Institution[] = data.institutions.map((i) => ({
  id: i.id,
  name: i.name,
  city: i.city,
  country: i.country,
  lat: i.lat,
  lon: i.lon,
  domain: i.domain,
  badge: badgePath(i.id),
  pi: i.pi,
}));

export const INSTITUTIONS_BY_ID = new Map<string, Institution>(
  INSTITUTIONS.map((i) => [i.id, i]),
);

export function getInstitution(id: string): Institution | undefined {
  return INSTITUTIONS_BY_ID.get(id);
}
