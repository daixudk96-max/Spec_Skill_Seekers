# Add Transcript Processing Capability

## Why
A significant amount of high-value knowledge is trapped in course videos and audio. To extract skills from these sources, we need to process their transcripts (SRT, VTT, TXT). This change enables converting raw transcript files into structured Claude AI skills, complete with summaries, key points, and practice exercises.

## What Changes
We will implement a complete pipeline to ingest, normalize, and extract skills from transcripts, merging the technical robustness of dedicated scrapers with rich educational output.

1.  **New Data Source**: Support `transcript` type in unified config, allowing it to be mixed with GitHub/Docs sources.
2.  **Transcript Scraper Implementation**:
    *   **Input**: Supports `.srt` (timestamps), `.vtt`, `.txt`, `.md`, `.docx`.
    *   **Normalization**: Converts all formats into a standard internal `Lesson` object, stripping timestamps for content analysis while preserving structure.
3.  **Rich Skill Output**:
    *   Instead of just raw text, the output skill will specifically include:
        *   **Summary**: A concise overview of the lesson.
        *   **Key Points**: Bulleted concepts.
        *   **Practice Exercises**: Generated tasks to reinforce learning.
4.  **Integration**:
    *   CLI: `skill-seekers transcript --input <file>` for quick one-off processing.
    *   MCP: `scrape_transcript` tool for agents.

## Impact
- **Specs**: New `transcript-ingestion` capability.
- **Codebase**:
    - New `src/skill_seekers/cli/transcript_scraper.py` (implementation).
    - New `src/skill_seekers/cli/transcript_parser.py` (parsing logic).
    - Updates to `unified_scraper.py` to handle the new source type.
