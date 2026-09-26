/**
 * Entry point: tiny hash router + shared HUD top bar.
 * Routes: #/map (default) and #/tech.
 */
import "./hud.css";
import { mountMapView } from "./map";
import { mountTechView } from "./tech";

type Route = "map" | "tech";

function currentRoute(): Route {
  const hash = window.location.hash;
  return hash.startsWith("#/tech") ? "tech" : "map";
}

function buildShell(): {
  app: HTMLElement;
  navMap: HTMLAnchorElement;
  navTech: HTMLAnchorElement;
  view: HTMLElement;
} {
  const app = document.getElementById("app");
  if (!app) {
    throw new Error("#app element not found in index.html.");
  }
  app.innerHTML = `<header class="hud-topbar"><a class="hud-brand" href="#/map"><span class="brand-accent">SPACE</span>ORIGINS</a><nav class="hud-nav" aria-label="Views"><a href="#/map" data-route="map">STARMAP</a><a href="#/tech" data-route="tech">TECHNOLOGIES</a></nav><div class="hud-status"><span class="hud-readout">YEAR <span class="value">2280</span></span><span class="hud-readout">CLIENT <span class="value">PROTO</span></span><span class="hud-readout">SIM <span class="value accent">BACKEND</span></span></div></header><div class="hud-view"></div>`;

  const navMap = app.querySelector<HTMLAnchorElement>('a[data-route="map"]');
  const navTech = app.querySelector<HTMLAnchorElement>('a[data-route="tech"]');
  const view = app.querySelector<HTMLElement>(".hud-view");
  if (!navMap || !navTech || !view) {
    throw new Error("HUD shell structure incomplete.");
  }
  return { app, navMap, navTech, view };
}

function setActiveNav(route: Route, navMap: HTMLAnchorElement, navTech: HTMLAnchorElement): void {
  navMap.classList.toggle("active", route === "map");
  navTech.classList.toggle("active", route === "tech");
}

const { navMap, navTech, view } = buildShell();

let unmount: (() => void) | null = null;

function render(): void {
  const route = currentRoute();
  setActiveNav(route, navMap, navTech);
  if (unmount) {
    unmount();
    unmount = null;
  }
  view.innerHTML = "";
  unmount = route === "tech" ? mountTechView(view) : mountMapView(view);
}

window.addEventListener("hashchange", render);
render();
