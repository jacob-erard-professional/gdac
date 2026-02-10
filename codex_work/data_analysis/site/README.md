# Visualization Site

This is a static React + ECharts site for exploring pipeline outputs.

## Setup

```bash
cd site
npm install
npm run dev
```

The site expects pipeline artifacts under:
- `outputs/analytics/<year>/`
- `outputs/aux/<year>/`

To make these available to the Vite dev server, create a symlink:

```bash
cd site
mkdir -p public
ln -s ../outputs public/outputs
```

If the dev server blocks the symlink, ensure `vite.config.js` has:

```js
server: {
  fs: {
    allow: [".."],
  },
}
```

Optional: add a `outputs/analytics/index.json` file with:

```json
{ "years": ["2023", "2024"] }
```

If the index is missing, the UI allows manual year entry.
