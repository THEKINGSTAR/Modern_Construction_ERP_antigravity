# LES-001: Next.js 14.1.0 Does Not Support TypeScript Configuration Files

## Category
Frontend / Build Configuration

## Root Cause
Next.js version 14.1.0 (`apps/web/package.json`) only supports JavaScript/ECMAScript module configuration files (`next.config.js` or `next.config.mjs`). The initial repository scaffolding introduced `apps/web/next.config.ts`, which causes `next build` to fail immediately with:
`Error: Configuring Next.js via 'next.config.ts' is not supported. Please replace the file with 'next.config.js' or 'next.config.mjs'.`

## Rule / Invariant
- **NEVER** re-introduce `next.config.ts` into Next.js 14.x projects.
- Use `next.config.mjs` or `next.config.js`.
- Always verify frontend build using `npm run build` in `apps/web/` during verification gates.
