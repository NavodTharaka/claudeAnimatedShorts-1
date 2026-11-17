import asyncio, json, sys, edge_tts
text = open('script.txt', encoding='utf8').read().replace('\n', ' ')
rate = sys.argv[1] if len(sys.argv) > 1 else '+8%'
async def main():
    c = edge_tts.Communicate(text, 'en-US-AndrewNeural', rate=rate, boundary='WordBoundary')
    words = []
    with open('voice.mp3', 'wb') as f:
        async for ch in c.stream():
            if ch['type'] == 'audio': f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                words.append({'word': ch['text'], 'start': ch['offset']/1e7, 'end': (ch['offset']+ch['duration'])/1e7})
    json.dump(words, open('words.json', 'w'), indent=1)
    print(len(words), words[-1]['end'])
asyncio.run(main())
