#!/usr/bin/env python3
"""
神话星空 MP3 音频预生成脚本
使用 Microsoft Edge TTS (edge-tts) Python API 免费生成 MP3
- 语音: zh-CN-XiaoyiNeural（卡通/小说专用活泼女声）
- 音调: +25Hz（模拟10岁女孩清脆音色）
- 语速: -10%（放慢10%让小朋友听得更清楚）
"""

import asyncio
import json
import os
import re
import sys

import edge_tts

# ============ 配置 ============
VOICE = "zh-CN-XiaoyiNeural"
PITCH = "+25Hz"
RATE = "-10%"
OUTPUT_DIR = "audio"


def extract_stories_from_html(html_path):
    """从 HTML 中提取 STORIES 数组"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到 STORIES = [ ... ];
    start = content.index('const STORIES = [')
    depth = 0
    i = start + len('const STORIES = [')
    while i < len(content):
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            if depth == 0:
                break
            depth -= 1
        i += 1
    end = i + 1

    stories_json = content[start + len('const STORIES = '):end]
    # 替换 JS 风格为 JSON 风格
    stories_json = re.sub(r'(\w+):', r'"\1":', stories_json)
    stories_json = re.sub(r"'", '"', stories_json)

    try:
        stories = json.loads(stories_json)
        return stories
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return []


def build_story_text(story):
    """构建故事的朗读文本：标题 + 内容"""
    title = story.get('title', '')
    content = story.get('content', '')

    # 清理 HTML 标签
    content = re.sub(r'<[^>]+>', '', content)
    content = content.strip()

    # 组合：标题 + 正文
    text = f"{title}。{content}"
    return text


async def generate_mp3(text, output_path):
    """使用 edge-tts Python API 生成单个 MP3"""
    communicate = edge_tts.Communicate(text, VOICE, pitch=PITCH, rate=RATE)
    await communicate.save(output_path)
    return True


async def main():
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    if not os.path.exists(html_path):
        html_path = os.path.abspath('index.html')
    if not os.path.exists(html_path):
        print(f"错误: 找不到 index.html")
        sys.exit(1)

    print("📖 从 HTML 提取故事数据...")
    stories = extract_stories_from_html(html_path)
    print(f"✅ 找到 {len(stories)} 个故事")

    output_dir = os.path.join(os.path.dirname(__file__), OUTPUT_DIR)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n🎤 语音: {VOICE}")
    print(f"🎵 音调: {PITCH}")
    print(f"⏱️  语速: {RATE}")
    print(f"📁 输出: {output_dir}/")
    print(f"\n开���生成 {len(stories)} 个 MP3...\n")

    success = 0
    skip = 0
    fail = 0

    for i, story in enumerate(stories):
        story_id = story.get('id', f'story_{i}')
        title = story.get('title', f'故事{i+1}')
        output_path = os.path.join(output_dir, f'{story_id}.mp3')

        # 跳过已生成的（除非是测试文件）
        if story_id == 'test':
            continue
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            skip += 1
            continue

        text = build_story_text(story)
        print(f"[{i+1}/{len(stories)}] {title} ({story_id})...", end=' ', flush=True)

        try:
            await generate_mp3(text, output_path)
            size_kb = os.path.getsize(output_path) / 1024
            print(f"✅ {size_kb:.0f}KB")
            success += 1
        except Exception as e:
            print(f"❌ {e}")
            fail += 1

        # 短暂暂停避免请求过于频繁
        await asyncio.sleep(0.3)

    print(f"\n{'='*50}")
    print(f"📊 生成完成！")
    print(f"  ✅ 成功: {success}")
    print(f"  ⏭️  跳过: {skip}")
    print(f"  ❌ 失败: {fail}")
    mp3_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
    if mp3_files:
        total_size = sum(os.path.getsize(os.path.join(output_dir, f)) for f in mp3_files)
        print(f"  📁 文件数: {len(mp3_files)}")
        print(f"  💾 总大小: {total_size / 1024 / 1024:.1f} MB")
    print(f"\n音频文件已保存到: {output_dir}/")


if __name__ == '__main__':
    asyncio.run(main())
