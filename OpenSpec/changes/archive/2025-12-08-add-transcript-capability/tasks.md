# Tasks: Add Transcript Capability

- [x] Define `Lesson` data structure in `src/skill_seekers/cli/data_types.py` <!-- id: 100 -->
- [x] Implement `TranscriptParser` in `src/skill_seekers/cli/transcript_parser.py` supporting .txt and .srt <!-- id: 101 -->
- [x] Implement `TranscriptScraper` in `src/skill_seekers/cli/transcript_scraper.py` <!-- id: 102 -->
- [x] Add `transcript` source type to configuration schema in `src/skill_seekers/cli/config_validator.py` <!-- id: 103 -->
- [x] Update `unified_scraper.py` to route `transcript` sources to `TranscriptScraper` <!-- id: 104 -->
- [x] Create `verify_transcript_output` test helper to validate structure of generated skills <!-- id: 105 -->
- [x] Add CLI integration tests (E2E) using a sample .srt file <!-- id: 106 -->
