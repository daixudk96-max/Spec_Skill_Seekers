# Spec: skill-install

## Capability: Local Skill Installation

Enable users to install skills directly to Claude's local skills directory with one command.

---

## ADDED Requirements

### Requirement: Install command shall support directory and zip input

The `install` command must accept both a skill directory path and a `.zip` file as input.

#### Scenario: Install from directory
**Given** a valid skill directory with `SKILL.md`
**When** user runs `skill-seekers install <skill_dir>`
**Then** the skill directory is copied to Claude skills folder

#### Scenario: Install from zip
**Given** a valid skill `.zip` file
**When** user runs `skill-seekers install <skill.zip>`
**Then** the zip is extracted to Claude skills folder

---

### Requirement: Cross-platform skills directory detection

The system must automatically detect Claude's skills directory across Windows, macOS, and Linux.

#### Scenario: Windows default detection
**Given** Windows platform with `%USERPROFILE%\.claude\skills` existing
**When** skills directory is resolved
**Then** returns the correct Windows path

#### Scenario: macOS default detection
**Given** macOS platform with `~/.claude/skills` existing
**When** skills directory is resolved
**Then** returns the correct macOS path

#### Scenario: Environment variable override
**Given** `CLAUDE_SKILLS_DIR` environment variable is set
**When** skills directory is resolved
**Then** returns the path from environment variable

---

### Requirement: Conflict handling strategies

The system must provide multiple strategies for handling existing skills with the same name.

#### Scenario: Default fail on conflict
**Given** target skill already exists
**When** user runs `skill-seekers install <skill>` without flags
**Then** command fails with clear error message

#### Scenario: Overwrite mode
**Given** target skill already exists
**When** user runs `skill-seekers install <skill> --overwrite`
**Then** existing skill is deleted and new skill is installed

#### Scenario: Backup mode
**Given** target skill already exists
**When** user runs `skill-seekers install <skill> --backup`
**Then** existing skill is renamed with timestamp suffix and new skill is installed

#### Scenario: Dry run mode
**Given** any install operation
**When** user runs `skill-seekers install <skill> --dry-run`
**Then** shows what would happen without making changes

---

### Requirement: Package command install integration

The `package` command must support an `--install` flag for one-shot packaging and installation.

#### Scenario: Package with install
**Given** a valid skill directory
**When** user runs `skill-seekers package <skill_dir> --install`
**Then** skill is packaged and then installed to Claude skills folder

---

### Requirement: Validation before install

The system must validate skill structure before installation.

#### Scenario: Validate SKILL.md exists
**Given** a directory without `SKILL.md`
**When** user attempts to install
**Then** command fails with validation error

---

### Requirement: Rollback on failure

If installation fails mid-way, the system must clean up partial state.

#### Scenario: Rollback incomplete install
**Given** copy operation fails after creating target directory
**When** error is detected
**Then** partial target directory is removed

#### Scenario: Restore backup on failure
**Given** backup was created before overwrite
**When** new installation fails
**Then** backup is restored to original location

---

## ADDED Requirements (Supplementary)

### Requirement: Linux platform skills directory detection

The system must correctly detect Claude's skills directory on Linux platforms.

#### Scenario: Linux XDG_DATA_HOME detection
**Given** Linux platform with `$XDG_DATA_HOME/Claude/skills` existing
**When** skills directory is resolved
**Then** returns the XDG path

#### Scenario: Linux fallback to .claude/skills
**Given** Linux platform without XDG directory
**When** skills directory is resolved
**Then** returns `~/.claude/skills`

---

### Requirement: Target directory auto-creation

The system must create the target skills directory if it does not exist.

#### Scenario: Create missing skills directory
**Given** target skills directory does not exist
**When** user runs `skill-seekers install <skill>`
**Then** directory is created with `mkdir -p` semantics

#### Scenario: Permission denied creating directory
**Given** insufficient permissions to create directory
**When** user attempts to install
**Then** command fails with clear permission error message

---

### Requirement: Conflict flag mutual exclusivity

The `--overwrite` and `--backup` flags must be mutually exclusive.

#### Scenario: Both flags specified
**Given** user runs `skill-seekers install <skill> --overwrite --backup`
**When** command is parsed
**Then** command fails with error explaining flags are mutually exclusive

---

### Requirement: ZIP security validation

The system must validate ZIP files for security before extraction.

#### Scenario: Reject path traversal
**Given** a ZIP file containing `../malicious.txt` or absolute paths
**When** user attempts to install
**Then** command fails with security error

#### Scenario: Handle missing top-level directory
**Given** a ZIP file with flat structure (no top-level folder)
**When** user runs `skill-seekers install <skill.zip>`
**Then** skill is installed to a folder named after the zip file

#### Scenario: Reject symbolic links in ZIP
**Given** a ZIP file containing symbolic links
**When** user attempts to install
**Then** symbolic links are skipped with warning

---

### Requirement: Atomic installation operation

Installation must be atomic to prevent partial state on failure.

#### Scenario: Atomic directory install
**Given** installing from a directory
**When** copy operation begins
**Then** files are first copied to a temporary directory, then moved to target

#### Scenario: Atomic zip extraction
**Given** installing from a ZIP file
**When** extraction begins
**Then** contents are first extracted to a temporary directory, then moved to target

---

### Requirement: Package install-upload ordering

When both `--install` and `--upload` are specified, they must execute in order.

#### Scenario: Package with install and upload
**Given** user runs `skill-seekers package <skill> --install --upload`
**When** package completes
**Then** install executes first, then upload
**And** if install fails, upload is skipped with error message
