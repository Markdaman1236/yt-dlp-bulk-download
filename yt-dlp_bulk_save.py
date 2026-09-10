#!/usr/bin/env python3
"""
YouTube Search + Selective Download
Keeps running until the user chooses to quit
"""

import os
import yt_dlp
from typing import List, Dict

# ============== CONFIG ==============
DEFAULT_DOWNLOAD_DIR = "downloads"
# Set this if ffmpeg is not in PATH (Windows example):
# FFMPEG_LOCATION = r"C:\ffmpeg\bin"
FFMPEG_LOCATION = None
# ====================================


def format_duration(seconds) -> str:
    if not seconds:
        return "?:??"
    try:
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except (ValueError, TypeError):
        return "?:??"


def search_videos(query: str, max_results: int = 15) -> List[Dict]:
    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "no_warnings": True,
    }
    search_url = f"ytsearch{max_results}:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        return [e for e in info.get("entries", []) if e]


def print_results(videos: List[Dict]):
    print("\n" + "=" * 80)
    print(f"{'#':<4} {'Duration':<10} {'Title':<48} {'Channel'}")
    print("-" * 80)
    for i, v in enumerate(videos, 1):
        title = (v.get("title") or "No title")[:46]
        channel = (v.get("channel") or v.get("uploader") or "Unknown")[:18]
        duration = format_duration(v.get("duration"))
        print(f"{i:<4} {duration:<10} {title:<48} {channel}")
    print("=" * 80)


def get_quality_choice() -> str:
    print("\nQuality options:")
    print("  1. Best available (highest quality)")
    print("  2. 1080p")
    print("  3. 720p  (recommended balance)")
    print("  4. 480p")
    print("  5. 360p  (fastest)")
    print("  6. Audio only (MP3)")
    
    choice = input("Choose quality [3]: ").strip() or "3"
    
    formats = {
        "1": "bestvideo+bestaudio/best",
        "2": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "3": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "4": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "5": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "6": "bestaudio/best",
    }
    return formats.get(choice, formats["3"])


def download_selected(
    videos: List[Dict],
    indices: List[int],
    format_str: str,
    output_dir: str,
    audio_only: bool = False,
):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        "format": format_str,
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 8,
        "retries": 5,
        "fragment_retries": 5,
        "quiet": False,
        "no_warnings": False,
        "ignoreerrors": True,
    }

    if FFMPEG_LOCATION:
        ydl_opts["ffmpeg_location"] = FFMPEG_LOCATION

    if audio_only:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    urls = []
    for i in indices:
        if 1 <= i <= len(videos):
            v = videos[i - 1]
            url = v.get("url") or f"https://www.youtube.com/watch?v={v.get('id')}"
            urls.append(url)
            print(f"→ Queued: {v.get('title', 'Unknown')}")
        else:
            print(f"⚠ Skipping invalid number: {i}")

    if not urls:
        print("No valid videos selected.")
        return

    print(f"\nStarting download of {len(urls)} item(s)...\n")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)
    print("\n✓ Download finished!")


def main():
    print("=" * 50)
    print("  YouTube Search + Download Tool")
    print("  (type 'quit' or 'exit' at any prompt to leave)")
    print("=" * 50)

    while True:
        print("\n" + "-" * 50)
        query = input("Search term / category (or 'quit'): ").strip()

        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not query:
            print("No search term given.")
            continue

        try:
            max_results = int(input("How many results to show? [15]: ").strip() or "15")
        except ValueError:
            max_results = 15

        print(f"\nSearching for “{query}” ...")
        videos = search_videos(query, max_results)

        if not videos:
            print("No results found.")
            continue

        print_results(videos)

        format_str = get_quality_choice()
        audio_only = format_str == "bestaudio/best"

        folder = input(f"\nDownload folder [{DEFAULT_DOWNLOAD_DIR}]: ").strip() or DEFAULT_DOWNLOAD_DIR

        selection = input(
            "\nEnter numbers to download (e.g. 1,3,5-8) or 'all' (or 'back' to search again): "
        ).strip().lower()

        if selection in ("back", "b", "cancel"):
            continue

        if selection == "all":
            indices = list(range(1, len(videos) + 1))
        else:
            indices = []
            try:
                for part in selection.split(","):
                    part = part.strip()
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        indices.extend(range(start, end + 1))
                    else:
                        indices.append(int(part))
            except ValueError:
                print("Invalid selection format.")
                continue

        download_selected(videos, indices, format_str, folder, audio_only)

        # After download finishes → loop back to search
        print("\nReturning to search...")


if __name__ == "__main__":
    main()
