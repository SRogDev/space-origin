/**
 * Technology route: honest placeholder. Fetches the technology content from
 * the live backend and renders a clean card list. The interactive graph
 * visualization is explicitly marked as a future phase.
 */
import { ApiError, type Tech, getTechnologies } from "./api";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderTechCard(tech: Tech): string {
  const meta = tech.meta;
  const prereqs =
    meta.prerequisites.length > 0 ? meta.prerequisites.map(escapeHtml).join(", ") : "none";
  return `<article class="hud-panel tech-card"><div class="tech-name">${escapeHtml(meta.name)}</div><div class="tech-meta-line">branch <span class="accent">${escapeHtml(meta.branch)}</span> · tier <span class="accent">${meta.tier}</span> · cost <span class="accent">${meta.cost}</span></div><div class="tech-meta-line">requires: ${prereqs}</div>${tech.body.trim() ? `<div class="tech-body">${escapeHtml(tech.body.trim().slice(0, 280))}</div>` : ""}</article>`;
}

/**
 * Mount the technology view into `container`.
 * Returns an unmount function (no-op here, but keeps the router symmetric).
 */
export function mountTechView(container: HTMLElement): () => void {
  container.classList.add("hud-view");
  container.innerHTML = `<div class="tech-view"><div class="tech-head"><span class="coming-badge">Interactive graph — coming in Phase 3</span></div><div class="tech-grid" aria-live="polite"></div></div>`;

  const grid = container.querySelector<HTMLElement>(".tech-grid");
  if (!grid) {
    throw new Error("Tech view container missing .tech-grid element.");
  }
  // Non-null alias: TS drops narrowing of captured variables across awaits.
  const gridEl: HTMLElement = grid;

  let cancelled = false;

  async function load(): Promise<void> {
    try {
      const techs = await getTechnologies();
      if (cancelled) {
        return;
      }
      if (techs.length === 0) {
        gridEl.innerHTML = `<div class="hud-panel"><div class="row">The backend returned zero technologies.</div></div>`;
        return;
      }
      const sorted = [...techs].sort((a, b) => {
        if (a.meta.tier !== b.meta.tier) {
          return a.meta.tier - b.meta.tier;
        }
        return a.meta.name.localeCompare(b.meta.name);
      });
      gridEl.innerHTML = sorted.map(renderTechCard).join("");
    } catch (error) {
      if (cancelled) {
        return;
      }
      const detail =
        error instanceof ApiError ? error.message : "Unexpected error while fetching technologies.";
      gridEl.innerHTML = `<div class="hud-panel"><h3>API offline</h3><div class="row">${escapeHtml(detail)}</div><div class="row">Start the backend on port 8000, then reload this route.</div></div>`;
    }
  }

  void load();

  return () => {
    cancelled = true;
  };
}
