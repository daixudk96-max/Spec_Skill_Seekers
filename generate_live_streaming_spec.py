#!/usr/bin/env python3
"""
Generate SkillSpec for 直播岗位人才培养攻略 transcript.
按照 /skill-seekers-proposal 工作流生成 spec.yaml 和 scraped_data.json
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from skill_seekers.cli.spec_generator import SpecGenerator


def main():
    # Read transcript content
    transcript_path = Path(r"c:\open skills\Skill_Seekers\16.第八章：直播岗位人才培养攻略_原文.txt")
    transcript_text = transcript_path.read_text(encoding="utf-8")
    
    # Build scraped_data structure for transcript
    scraped_data = {
        "title": "直播岗位人才培养攻略",
        "source_type": "transcript",
        "source_file": str(transcript_path),
        "lessons": [
            {
                "title": "直播岗位人才培养攻略",
                "content": transcript_text,
                "duration": "约22分钟",
                "instructor": "唐僧",
                "organization": "抖星会直播电商学院"
            }
        ],
        "metadata": {
            "timestamp": "2025-12-02 12:33",
            "description": "掌握直播团队13个岗位的分工与职责，了解不同阶段的人员架构配置策略，学会面试和选拔优秀主播的方法"
        }
    }
    
    # Create output directory
    output_dir = Path(r"c:\open skills\Skill_Seekers\output\live-streaming-talent")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save scraped_data.json
    scraped_data_path = output_dir / "scraped_data.json"
    with open(scraped_data_path, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
    print(f"✅ scraped_data.json saved: {scraped_data_path}")
    
    # Generate spec using SpecGenerator
    generator = SpecGenerator.from_transcript_scraper(
        scraped_data=scraped_data,
        name="直播岗位人才培养攻略"
    )
    generator._description = "掌握直播团队13个岗位的分工与职责，了解不同阶段的人员架构配置策略，学会面试和选拔优秀主播的方法"
    
    # Generate and save spec
    spec = generator.generate()
    spec_path = output_dir / "spec.yaml"
    spec.save(spec_path)
    print(f"✅ spec.yaml saved: {spec_path}")
    
    # Print summary
    print()
    print(generator.export_for_review())


if __name__ == "__main__":
    main()
