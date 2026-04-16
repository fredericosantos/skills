---
name: dotstate
description: Guide for using dotstate, a profile-based dotfile manager with GitHub sync. Use this when managing dotfiles across multiple machines (e.g., Ubuntu and macOS), adding files to sync, switching profiles, or troubleshooting symlinks.
---

# dotstate: Profile-Based Dotfile Manager

dotstate manages dotfiles by replacing them with symlinks to a Git repository, supporting multiple machine profiles and a common shared layer.

## Navigation Rule

**Use dotstate when:**
- The user has a `~/.config/dotstate/` directory
- Files in `~` are symlinks pointing to a dotstate storage directory
- The user mentions syncing dotfiles across machines

## Profile Rule

dotstate organizes files into **profiles** (per-machine, e.g., `ubuntu`, `macos`) and **Common** (shared across all profiles).

**File classification:**
- **Common**: files identical on all machines (e.g., `gitconfig`, `zshenv`, `starship.toml`)
- **Profile-specific**: files with machine differences (e.g., `zprofile` with CUDA paths on Ubuntu, Homebrew paths on macOS; `npmrc` with OS-specific prefix paths)

**Creating profiles**: Profiles are created through the TUI only (no CLI command). Launch `dotstate` → Manage Profiles → create. The name `common` is reserved and cannot be used as a profile name.

**Storage structure:**
```
storage-repo/
├── common/                    # Shared across all profiles
│   ├── .gitconfig
│   └── .zshenv
├── ubuntu/                    # Profile-specific
│   └── .zprofile
├── macos/                     # Profile-specific
│   └── .zprofile
└── .dotstate-profiles.toml    # Manifest (profiles, files, packages)
```

## Core Workflow Rules

### Adding a file

```bash
dotstate add ~/.zshrc               # Add to active profile
dotstate add --common ~/.gitconfig  # Add to Common (shared across all profiles)
```

### Syncing changes

```bash
dotstate sync                          # Commit, pull (rebase), push
dotstate sync -m "update zshrc"        # With custom commit message
```

### Listing tracked files

```bash
dotstate list           # Show all synced files
dotstate list -v        # Verbose: show profile and path details
```

### Removing a file

```bash
dotstate remove .zshrc           # Remove from active profile
dotstate remove --common .gitconfig  # Remove from Common
```

Accepts both absolute (`~/.zshrc`) and relative (`.zshrc`) paths.

### Activate / Deactivate symlinks

```bash
dotstate activate     # Restore all symlinks (use after cloning on a new machine)
dotstate deactivate   # Remove symlinks, restore originals (use before uninstalling)
```

## New Machine Setup Rule

On a new machine, to restore dotfiles:

```bash
cargo install dotstate       # or brew install serkanyersen/dotstate/dotstate
dotstate                     # Launch TUI to configure repo connection and select profile
dotstate activate            # Create symlinks for the active profile
```

The TUI setup must run first — `activate` alone won't work without a configured repo.

## Diagnostics Rule

When symlinks are broken or files are out of sync:

```bash
dotstate doctor          # Run diagnostics
dotstate doctor --fix    # Auto-fix detected issues
dotstate doctor -v       # Verbose output
dotstate doctor --json   # JSON output for scripting
```

## Packages Rule

dotstate can track which CLI tools belong to each profile:

```bash
dotstate packages list                          # List packages for active profile
dotstate packages list -p macos                 # List for a specific profile
dotstate packages add -m brew -b starship       # Track a Homebrew package by binary name
dotstate packages add -m cargo -b dotstate      # Track a Cargo package
dotstate packages check                         # Check installation status
dotstate packages install                       # Install all missing packages

# Supported managers: brew, cargo, apt, npm, pip, yum, dnf, pacman, snap, gem, custom
```

## Migration Rule: Dotbot → dotstate

When migrating from a Dotbot-managed `~/.dotfiles/` repo:

1. Remove existing Dotbot symlinks: `~/.zshrc`, `~/.gitconfig`, etc.
2. Initialize dotstate (TUI) — point it to the existing git repo in Local mode
3. Add common files: `dotstate add --common ~/.gitconfig`, etc.
4. Add profile-specific files: `dotstate add ~/.zprofile`, etc.
5. Verify: `dotstate list -v` and `dotstate doctor`

## TUI Rule

Running `dotstate` with no arguments launches the interactive TUI. Use the TUI for:
- Profile switching
- Browsing tracked files
- One-shot sync operations

For scripting and automation, prefer the CLI subcommands.

## Info & Maintenance Rule

```bash
dotstate config           # Show config file location (~/.config/dotstate/config.toml)
dotstate repository       # Show storage repo path
dotstate logs             # Show log file location
dotstate upgrade          # Check for updates and upgrade
dotstate completions zsh  # Generate shell completions (also: bash, fish, elvish, powershell)
```
