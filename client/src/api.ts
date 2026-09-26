/**
 * Typed fetch wrapper for the SpaceOrigins backend content API.
 *
 * The backend is the real game (FastAPI/Python). The client never contains
 * simulation rules — it only reads content and world state from the API.
 *
 * Content API shape:
 *   GET /api/content/{type}       -> Array<{ id, meta, body }>
 *   GET /api/content/{type}/{id}  -> { id, meta, body }
 */

/** Base URL of the backend. Overridable at build time via VITE_API_BASE. */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/** One content item as returned by the backend. */
export interface ContentItem<TMeta> {
  id: string;
  meta: TMeta;
  body: string;
}

/** Frontmatter of a `places` content item (wiki/places/*.md). */
export interface PlaceMeta {
  name: string;
  type: "region" | "system" | "colony-site" | "station" | "anomaly";
  coordinates: [number, number, number];
  resources: string[];
  hazards: string[];
}

export type Place = ContentItem<PlaceMeta>;

/** Frontmatter of a `technologies` content item (wiki/technologies/*.md). */
export interface TechMeta {
  name: string;
  branch: string;
  tier: number;
  cost: number;
  prerequisites: string[];
  unlocks: string[];
  effects: Record<string, string>;
}

export type Tech = ContentItem<TechMeta>;

/** API is unreachable or returned an unusable response. */
export class ApiError extends Error {
  readonly status: number | null;
  constructor(message: string, status: number | null = null, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`);
  } catch (cause) {
    throw new ApiError(`Cannot reach backend at ${API_BASE}. Is the API running?`, null, { cause });
  }
  if (!response.ok) {
    throw new ApiError(
      `Backend returned ${response.status} ${response.statusText} for ${path}.`,
      response.status,
    );
  }
  const data: unknown = await response.json();
  return data as T;
}

/** GET /api/content/places — every known place in the mapped volume. */
export function getPlaces(): Promise<Place[]> {
  return request<Place[]>("/api/content/places");
}

/** GET /api/content/places/{id} — a single place. */
export function getPlace(id: string): Promise<Place> {
  return request<Place>(`/api/content/places/${encodeURIComponent(id)}`);
}

/** GET /api/content/technologies — the technology tree content. */
export function getTechnologies(): Promise<Tech[]> {
  return request<Tech[]>("/api/content/technologies");
}

/** GET /api/content/technologies/{id} — a single technology. */
export function getTechnology(id: string): Promise<Tech> {
  return request<Tech>(`/api/content/technologies/${encodeURIComponent(id)}`);
}
