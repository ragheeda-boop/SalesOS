#!/usr/bin/env node

/**
 * CSS Variable Codemod
 * Migrates Tailwind color utility classes to CSS variables.
 *
 * Usage:
 *   node scripts/migrate-css-vars.js [--dir=./src/pages] [--dry-run]
 *
 * Supported mappings:
 *   text-{color}-{shade}  → var(--text-{role})
 *   bg-{color}-{shade}    → var(--bg-{role})
 *   border-{color}-{shade} → var(--border-{role})
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

// --- Configuration ---

const ROLE_MAP = {
  neutral: { text: 'primary', bg: 'secondary', border: 'default' },
  orange: { text: 'accent', bg: 'accent-muted', border: 'accent' },
  success: { text: 'success', bg: 'success-muted', border: 'success' },
  warning: { text: 'warning', bg: 'warning-muted', border: 'warning' },
  danger: { text: 'danger', bg: 'danger-muted', border: 'danger' },
  info: { text: 'info', bg: 'info-muted', border: 'info' },
  primary: { text: 'primary', bg: 'primary-muted', border: 'primary' },
  secondary: { text: 'secondary', bg: 'secondary', border: 'secondary' },
}

const PROPS = ['text', 'bg', 'border']
const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]

// Build regex pattern for all combos
const patternStr = PROPS.map((prop) => {
  const colors = Object.keys(ROLE_MAP)
  return `\\b${prop}-(${colors.join('|')})-(\\d{2,3})\\b`
}).join('|')

const CLASS_RE = new RegExp(patternStr, 'g')

// --- Reporting ---

let filesChanged = 0
let totalReplacements = 0
const remainingFiles = []

// --- Scanning & Replacement ---

function scanFile(filePath, dryRun) {
  let content = fs.readFileSync(filePath, 'utf-8')
  const original = content
  let replacements = 0

  content = content.replace(CLASS_RE, (match, p1, p2, offset, str) => {
    // Determine which property matched
    const part = match.split('-')
    const prop = part[0]
    const color = part[1]
    const shade = parseInt(part[2], 10)

    const roleEntry = ROLE_MAP[color]
    if (!roleEntry) return match

    const role = roleEntry[prop]
    if (!role) return match

    replacements++
    totalReplacements++

    if (prop === 'text') return `var(--text-${role})`
    if (prop === 'bg') return `var(--bg-${role})`
    if (prop === 'border') return `var(--border-${role})`
    return match
  })

  if (content !== original) {
    filesChanged++
    if (!dryRun) {
      fs.writeFileSync(filePath, content, 'utf-8')
    }
    console.log(`  ✓ ${dryRun ? '[DRY RUN] Would fix' : 'Fixed'} ${filePath} (${replacements} replacement(s))`)
    return true
  }
  return false
}

function walkDir(dir, extensions, dryRun) {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
      walkDir(fullPath, extensions, dryRun)
    } else if (entry.isFile() && extensions.some((ext) => entry.name.endsWith(ext))) {
      scanFile(fullPath, dryRun)
    }
  }
}

// --- Main ---

function main() {
  const args = process.argv.slice(2)
  const dryRun = args.includes('--dry-run')
  const dirIndex = args.findIndex((a) => a.startsWith('--dir='))
  const rootDir = dirIndex >= 0 ? args[dirIndex].split('=')[1] : null

  console.log('=== CSS Variable Migration Codemod ===')
  console.log(`Mode: ${dryRun ? 'DRY RUN (no changes written)' : 'LIVE'}`)
  console.log('')

  // If a specific directory is provided, scan only that
  if (rootDir) {
    console.log(`Scanning: ${rootDir}`)
    if (fs.existsSync(rootDir)) {
      walkDir(rootDir, ['.tsx', '.ts', '.jsx', '.js'], dryRun)
    } else {
      console.error(`Directory not found: ${rootDir}`)
      process.exit(1)
    }
  } else {
    // Scan default project directories
    const searchDirs = []
    const base = path.resolve(__dirname, '..')

    // Try common frontend directories
    const candidates = [
      'frontend/src/pages',
      'frontend/src/components',
      'frontend/src/app',
      'frontend/packages/ui/src',
    ]

    for (const c of candidates) {
      const full = path.join(base, c)
      if (fs.existsSync(full)) {
        searchDirs.push(full)
      }
    }

    if (searchDirs.length === 0) {
      console.log('No frontend directories found. Try specifying --dir=./path/to/src')
      process.exit(0)
    }

    for (const d of searchDirs) {
      console.log(`Scanning: ${d}`)
      walkDir(d, ['.tsx', '.ts', '.jsx', '.js'], dryRun)
    }
  }

  // --- Summary ---
  console.log('')
  console.log('=== Summary ===')
  console.log(`Files scanned: ${filesChanged > 0 ? 'multiple' : 'none'}`)
  console.log(`Files with changes: ${filesChanged}`)
  console.log(`Total replacements: ${totalReplacements}`)
  console.log(`Mode: ${dryRun ? 'DRY RUN' : 'LIVE'}`)

  if (!dryRun && filesChanged > 0) {
    console.log('')
    console.log('Manual review needed for:')
    console.log('  - Inline style color values')
    console.log('  - Arbitrary Tailwind classes like text-[#...]')
    console.log('  - Dark mode overrides (dark:text-neutral-100)')
    console.log(`  - Check ${filesChanged} file(s) updated above`)
  }
}

main()
