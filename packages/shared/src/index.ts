/**
 * @throughline/shared — core production-graph entity types.
 *
 * NOTE: In production these types are GENERATED from `docs/openapi.yaml`
 * (the canonical API contract) and must never be hand-edited. The definitions
 * below are hand-written stand-ins for scaffolding/typechecking until the
 * generator (openapi-typescript) is wired into the build. JSON is camelCase,
 * URLs are kebab-case, IDs are opaque strings.
 *
 * See root CLAUDE.md §Conventions: "Generated TS types come from
 * docs/openapi.yaml — never hand-edit generated files."
 */

/** Opaque identifier (ULID/UUID) as returned by the API. */
export type Id = string;

/** ISO-8601 date string, e.g. "2026-07-01". */
export type IsoDate = string;

// ---------------------------------------------------------------------------
// Project
// ---------------------------------------------------------------------------

export type ProjectType = 'scripted' | 'commercial' | 'episodic';

export interface Project {
  id: Id;
  orgId: Id;
  title: string;
  type: ProjectType;
}

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------

export type IntExt = 'INT' | 'EXT' | 'INT/EXT';

/** Common story time-of-day slugs found in scene headings. */
export type TimeOfDay = 'DAY' | 'NIGHT' | 'DUSK' | 'DAWN' | 'CONTINUOUS' | string;

export interface Scene {
  id: Id;
  /** Scene number as it appears on the page (may be alphanumeric, e.g. "12A"). */
  number: string;
  intExt: IntExt;
  location: string;
  timeOfDay: TimeOfDay;
  /** Length in page eighths (industry-standard scene sizing). */
  pageEighths: number;
  /** Full slugline, e.g. "INT. WAREHOUSE - NIGHT". */
  heading: string;
  /** Character names present in the scene. */
  characters: string[];
}

// ---------------------------------------------------------------------------
// Breakdown elements
// ---------------------------------------------------------------------------

export type ElementType =
  | 'cast'
  | 'prop'
  | 'wardrobe'
  | 'location'
  | 'vehicle'
  | 'sfx'
  | 'vfx'
  | 'stunt'
  | 'animal'
  | 'sound'
  | 'setDressing';

/** Where a breakdown element originated. AI sources produce DRAFTS only. */
export type ElementSource = 'rule' | 'ner' | 'llm' | 'human';

/** Review status. `confirmed`/`rejected` may only be set by a human action. */
export type ElementStatus = 'draft' | 'confirmed' | 'rejected';

export interface Element {
  id: Id;
  etype: ElementType;
  name: string;
  /** Model/rule confidence in [0, 1]. */
  confidence: number;
  source: ElementSource;
  needsReview: boolean;
  status: ElementStatus;
}

// ---------------------------------------------------------------------------
// Schedule
// ---------------------------------------------------------------------------

export interface ShootingDay {
  id: Id;
  /** 1-based ordinal of the shooting day within the schedule. */
  index: number;
  date: IsoDate;
  primaryLocation: string;
}

/**
 * Day-Out-of-Days work codes.
 * SW = Start Work, W = Work, WF = Work Finish, H = Hold, SWF = Start-Work-Finish.
 */
export type DoodCode = 'SW' | 'W' | 'WF' | 'H' | 'SWF';

// ---------------------------------------------------------------------------
// Budget
// ---------------------------------------------------------------------------

export interface BudgetLine {
  id: Id;
  /** AICP/MM account code. */
  code: string;
  category: string;
  description: string;
  qty: number;
  unit: string;
  rate: number;
  /** Fringe percentage applied to this line (e.g. 22.5 for 22.5%). */
  fringePct: number;
}

// ---------------------------------------------------------------------------
// Ripple / propagation
// ---------------------------------------------------------------------------

/**
 * A single field-level change within a ProposedDiff, expressed as a
 * JSON-patch-like tuple keyed on the entity path.
 */
export interface DiffChange {
  path: string;
  before: unknown;
  after: unknown;
}

/**
 * A reviewable consequence of an edit rippling through the production graph.
 * AI proposes; a human confirms before it is applied.
 */
export interface ProposedDiff {
  id: Id;
  changes: DiffChange[];
  /** Net effect on the top sheet, in whole currency units (may be negative). */
  dollarDelta: number;
  /** Human-readable one-line summary, e.g. "+1 cast hold day". */
  summary: string;
}
