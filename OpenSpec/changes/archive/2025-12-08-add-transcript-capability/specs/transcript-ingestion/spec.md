# Transcript Ingestion

## ADDED Requirements

### Requirement: Ingest Transcript Files
The system MUST support ingesting transcript files in `.srt`, `.vtt`, and `.txt` formats from a local file path.

#### Scenario: Ingest SRT File
- **Given** a config file listing a local `.srt` path `video_subs.srt` type `transcript`
- **When** the scraper runs
- **Then** it extracts the text content "Hello world" from the SRT file
- **And** it ignores the timestamps "00:00:01 --> 00:00:05".

### Requirement: Normalize Transcript Content
The system MUST normalize ingested transcripts into a structured `Lesson` format containing the title (derived from filename) and cleaned text body.

#### Scenario: Standard Lesson Format
- **Given** an input file "lecture_1.txt"
- **When** the file is parsed
- **Then** a Lesson object is created
- **And** the Lesson title is "lecture_1".

### Requirement: Generate Enriched Skill Output
When processing a `transcript` source, the system MUST generate a skill file that explicitly includes sections for "Summary", "Key Points", and "Practice Exercises".

#### Scenario: Generate Skill from Transcript
- **Given** a normalized transcript lesson "Intro to Python"
- **When** the skill is generated
- **Then** the output Markdown contains `## Summary`
- **And** the output Markdown contains `## Key Points`
- **And** the output Markdown contains `## Practice Exercises`.
