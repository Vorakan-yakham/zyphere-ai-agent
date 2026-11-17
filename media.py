"""Zyphere Media Forge - audio/video production helpers (offline, FFmpeg-based).

Implements the "ingredients" for real MP3/MP4 production:
- metadata tagging (title/artist) via mutagen
- SRT subtitles ( burns into MP4 )
- MIDI-style melody → WAV → MP3 (synthesized music, no copyrighted source)
All work locally with FFmpeg / mutagen; no external service required.
"""
import os, math, struct, wave, json, time, subprocess


def tag_mp3(path, title="", artist="", album="Zyphere"):
    """Write ID3 metadata to an MP3 using mutagen."""
    try:
        from mutagen.id3 import ID3, TIT2, TPE1, TALB
        from mutagen.mp3 import MP3 as M
        a = M(path)
        a.add_tags() if a.tags is None else None
        a.tags.add(TIT2(encoding=3, text=str(title or "")[:200]))
        a.tags.add(TPE1(encoding=3, text=str(artist or "Zyphere")[:200]))
        a.tags.add(TALB(encoding=3, text=str(album or "Zyphere")[:200]))
        a.save()
        return {"ok": True, "tagged": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def srt_from_text(text, seconds_per_chunk=4.0, max_chars=80):
    """Generate SRT subtitle content from plain text, timed evenly."""
    import re
    words = re.split(r"\s+", str(text or "").strip())
    if not words:
        return ""
    lines, cur = [], []
    for w in words:
        if len(" ".join(cur + [w])) > max_chars and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))

    def ts(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
        return "%02d:%02d:%02d,%03d" % (h, m, s, ms)

    out = []
    for i, line in enumerate(lines, 1):
        st = (i - 1) * seconds_per_chunk
        en = i * seconds_per_chunk - 0.1
        out.append("%d\n%s --> %s\n%s\n" % (i, ts(st), ts(en), line))
    return "\n".join(out)


def write_srt(path, text, seconds_per_chunk=4.0):
    try:
        s = srt_from_text(text, seconds_per_chunk)
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        return {"ok": True, "path": path, "blocks": s.count("-->")}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def burn_srt(video_in, srt_path, video_out, ffmpeg=None):
    """Burn SRT subtitles into MP4 using FFmpeg (libx264 + mov_text)."""
    ffmpeg = ffmpeg or subprocess.run(["where", "ffmpeg"], capture_output=True, text=True).stdout.strip().splitlines()
    ffmpeg = ffmpeg[0] if isinstance(ffmpeg, list) and ffmpeg else (ffmpeg if isinstance(ffmpeg, str) else None)
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg not available"}
    try:
        cmd = [ffmpeg, "-y", "-i", video_in, "-i", srt_path,
               "-c:v", "libx264", "-c:a", "copy",
               "-c:s", "mov_text", "-metadata:s:s:0", "language=tha",
               video_out]
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600)
        if p.returncode != 0:
            return {"ok": False, "error": (p.stderr or b"").decode("utf-8", "ignore")[-300:]}
        return {"ok": True, "path": video_out}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def melody_to_wav(path, notes=None, bpm=100, sample_rate=22050):
    """Synthesize a simple melody into WAV (original, royalty-free music).
    notes: list of (semitone_offset_from_A4, beats). If None, uses a calm pentatonic loop.
    """
    if notes is None:
        # calm pentatonic loop (A minor pentatonic)
        seq = [0, 3, 5, 7, 10, 7, 5, 3, 0, -2, 3, 0]
        notes = [(n, 0.5) for n in seq]
    beat = 60.0 / max(1, bpm)
    frames = bytearray()
    for semi, beats in notes:
        freq = 440.0 * (2 ** (semi / 12.0))
        dur = max(0.1, beat * beats)
        n = int(sample_rate * dur)
        for i in range(n):
            env = min(1.0, i / (sample_rate * 0.02), max(0.0, (n - i) / (sample_rate * 0.08)))
            val = int(12000 * env * math.sin(2 * math.pi * freq * i / sample_rate))
            frames += struct.pack("<h", val)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sample_rate)
        w.writeframes(bytes(frames))
    return {"ok": True, "path": path, "samples": len(frames) // 2}


def wav_to_mp3(wav_path, mp3_path, ffmpeg=None, bitrate="192k"):
    """Convert WAV to MP3 with LAME via FFmpeg."""
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg not available"}
    try:
        cmd = [ffmpeg, "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", bitrate, mp3_path]
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300)
        if p.returncode != 0:
            return {"ok": False, "error": (p.stderr or b"").decode("utf-8", "ignore")[-300:]}
        return {"ok": True, "path": mp3_path, "size": os.path.getsize(mp3_path)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def capabilities(ffmpeg=None, has_mutagen=True):
    return {
        "mp3_tts": True,
        "mp4_video": bool(ffmpeg),
        "metadata": bool(has_mutagen),
        "subtitles_srt": True,
        "music_midi_like": True,
        "ffmpeg": bool(ffmpeg),
    }
