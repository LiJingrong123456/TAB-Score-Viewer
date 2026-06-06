# -*- coding: utf-8 -*-
"""探索 gp3 文件的完整数据结构"""
import guitarpro

song = guitarpro.parse(r'e:\Projects\TAB Score Viewer\gtp格式-吉他谱全集\gtp格式电吉他谱\[影视]灌蓝高手的片尾曲.gp3')

print(f'标题: {song.title}')
print(f'BPM: {song.tempo}')
print(f'音轨数: {len(song.tracks)}')
print()

# 查看每个音轨
for ti, track in enumerate(song.tracks):
    print(f'--- 音轨{ti+1}: {track.name} (乐器{track.channel.instrument}) ---')
    print(f'  弦数: {len(track.strings)}, 调弦(MIDI): {[s.value for s in track.strings]}')
    print(f'  小节数: {len(track.measures)}, 品格: {track.fretCount}')
    # 前3个小节的详细内容
    for mi, measure in enumerate(track.measures[:3]):
        hdr = measure.header
        ts = hdr.timeSignature
        print(f'  小节{mi+1}: {ts.numerator}/{ts.denominator.value}, '
              f'重复开={hdr.isRepeatOpen}, 重复关={hdr.repeatClose}')
        for vi, voice in enumerate(measure.voices):
            for bi, beat in enumerate(voice.beats[:6]):  # 每小节最多看6拍
                dur = beat.duration
                notes_str = ', '.join(
                    f'弦{n.string+1}品{n.value}' + (
                        f'[幻]' if n.effect.ghostNote else ''
                    ) for n in beat.notes
                ) if beat.notes else '(休止)'
                print(f'    v{vi}拍{bi}: dur={dur.value}点={dur.isDotted} | {notes_str}')
    if ti >= 2:
        break  # 只看前3个音轨

# 查看 Duration 枚举值
print('\n=== Duration ===')
print(guitarpro.Duration.whole)
print(guitarpro.Duration.half)
print(guitarpro.Duration.quarter)
print(guitarpro.Duration.eighth)
print(guitarpro.Duration.sixteenth)

# 检查 NoteEffect 的技巧字段
print('\n=== NoteEffect 示例 ===')
track0 = song.tracks[0]
found = False
for mi, m in enumerate(track0.measures):
    if found: break
    for v in m.voices:
        if found: break
        for b in v.beats:
            if found: break
            for n in b.notes:
                e = n.effect
                if any([e.hammer, e.bend, e.slides, e.palmMute,
                        e.vibrato, e.staccato, e.harmonic.type.value != 0]):
                    print(f'  弦{n.string+1}品{n.value}: hammer={e.hammer}, '
                          f'slides={[s.name for s in e.slides]}, '
                          f'PM={e.palmMute}, vib={e.vibrato}, '
                          f'bend={e.bend}, harmonic={e.harmonic.type}')
                    found = True
                    break
