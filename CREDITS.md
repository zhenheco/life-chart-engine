# Credits & Attribution

`life-chart-engine` stands on the work of others.

## Swiss Ephemeris (via `pyswisseph`)

- Planetary positions and house cusps.
- © Astrodienst AG, Zürich — <https://www.astro.com/swisseph/>
- **License: GNU AGPL v3** (or a commercial license from Astrodienst).
  Because this engine links Swiss Ephemeris, the whole project is distributed
  under **AGPL-3.0** (see `LICENSE`). If you deploy it as a network service,
  AGPL §13 requires you to offer the complete corresponding source to the users
  of that service. For a closed-source / commercial deployment, obtain a
  Swiss Ephemeris **commercial license** from Astrodienst instead.
- This build uses the **Moshier** analytical ephemeris (`swe.FLG_MOSEPH`): no
  external `.se1` data files are required, but minor bodies (e.g. Chiron) are
  not available.

## iztro

- Zi Wei Dou Shu (紫微斗數) computation.
- TypeScript library: <https://github.com/SylarLong/iztro> — MIT
- Star-brightness output has been cross-checked against 文墨天機.

## Other libraries

FastAPI, Uvicorn, HTTPX, esbuild, and their transitive dependencies. See each
package's distribution for full terms.
