// Sprint 3 (fix C5): bundle the real per-block reference docs so the
// editor's right-click "Help" opens actual content instead of the old
// dead `#/docs/strategy-blocks/...` hash anchors.
//
// Single source of truth: these are the exact files developers read at
// `docs/dsl/blocks/*.md`. Vite inlines them as raw strings at build time
// (eager glob), so there is no duplication and no runtime fetch. The map
// is keyed by slug (filename without extension), which matches the slugs
// already used in HELP_URLS and the /strategies/blocks-help/:slug route.

const modules = import.meta.glob('../../../../../docs/dsl/blocks/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

export const BLOCK_DOCS = Object.entries(modules).reduce((acc, [path, content]) => {
  const slug = path.split('/').pop().replace(/\.md$/, '')
  acc[slug] = content
  return acc
}, {})

export const getBlockDoc = (slug) => BLOCK_DOCS[slug] || null
